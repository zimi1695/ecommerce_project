from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import pandas as pd
import pymysql


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CSV = PROJECT_ROOT / "data" / "raw" / "2019-Nov.csv"

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "ecommerce",
    "password": "ecommerce_2026",
    "database": "ecommerce",
    "charset": "utf8mb4",
    "autocommit": False,
    "local_infile": True,
}

INSERT_STAGING_SQL = """
INSERT INTO staging_events (
    event_time_raw,
    event_type,
    product_id,
    category_id,
    category_code,
    brand,
    price,
    user_id,
    user_session
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

UPSERT_USERS_SQL = """
INSERT IGNORE INTO users (user_id)
SELECT DISTINCT user_id
FROM staging_events
"""

UPSERT_CATEGORIES_SQL = """
INSERT INTO categories (
    category_id,
    category_code
)
SELECT
    category_id,
    MAX(category_code)
FROM staging_events
GROUP BY category_id
ON DUPLICATE KEY UPDATE
    category_code = COALESCE(
        VALUES(category_code),
        categories.category_code
    )
"""

UPSERT_BRANDS_SQL = """
INSERT IGNORE INTO brands (brand_name)
SELECT DISTINCT TRIM(brand)
FROM staging_events
WHERE brand IS NOT NULL
  AND TRIM(brand) <> ''
"""

UPSERT_PRODUCTS_SQL = """
INSERT INTO products (
    product_id,
    category_id
)
SELECT
    product_id,
    MIN(category_id)
FROM staging_events
GROUP BY product_id
ON DUPLICATE KEY UPDATE
    category_id = VALUES(category_id)
"""

UPSERT_PRODUCT_BRANDS_SQL = """
INSERT IGNORE INTO product_brands (
    product_id,
    brand_id
)
SELECT DISTINCT
    s.product_id,
    b.brand_id
FROM staging_events s
JOIN brands b
    ON b.brand_name = TRIM(s.brand)
WHERE s.brand IS NOT NULL
  AND TRIM(s.brand) <> ''
"""

UPSERT_SESSIONS_SQL = """
INSERT INTO sessions (
    session_id,
    start_time,
    end_time,
    event_count
)
SELECT
    user_session,

    MIN(
        STR_TO_DATE(
            REPLACE(event_time_raw, ' UTC', ''),
            '%Y-%m-%d %H:%i:%s'
        )
    ),

    MAX(
        STR_TO_DATE(
            REPLACE(event_time_raw, ' UTC', ''),
            '%Y-%m-%d %H:%i:%s'
        )
    ),

    COUNT(*)

FROM staging_events

WHERE user_session IS NOT NULL
  AND user_session <> ''

GROUP BY user_session

ON DUPLICATE KEY UPDATE
    start_time = LEAST(
        sessions.start_time,
        VALUES(start_time)
    ),
    end_time = GREATEST(
        sessions.end_time,
        VALUES(end_time)
    ),
    event_count = sessions.event_count
                  + VALUES(event_count)
"""

INSERT_EVENTS_SQL = """
INSERT IGNORE INTO behavior_events (
    event_time,
    event_type,
    user_id,
    session_id,
    product_id,
    brand_id,
    price,
    source_event_hash
)
SELECT
    STR_TO_DATE(
        REPLACE(s.event_time_raw, ' UTC', ''),
        '%Y-%m-%d %H:%i:%s'
    ),

    s.event_type,

    s.user_id,

    NULLIF(s.user_session, ''),

    s.product_id,

    b.brand_id,

    s.price,

    UNHEX(
        SHA2(
            CONCAT_WS(
                CHAR(31),
                s.event_time_raw,
                s.event_type,
                s.product_id,
                s.category_id,
                COALESCE(s.category_code, ''),
                COALESCE(s.brand, ''),
                s.price,
                s.user_id,
                COALESCE(s.user_session, '')
            ),
            256
        )
    )

FROM staging_events s

LEFT JOIN brands b
    ON b.brand_name = TRIM(s.brand)
"""


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def get_count(cur, table_name: str) -> int:
    cur.execute(f"SELECT COUNT(*) FROM {table_name}")
    return int(cur.fetchone()[0])


def clear_staging(conn):
    with conn.cursor() as cur:
        cur.execute("TRUNCATE TABLE staging_events")
    conn.commit()


def create_run(conn, source_file: str) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO etl_runs (
                job_name,
                source_file,
                status
            )
            VALUES (
                %s,
                %s,
                'RUNNING'
            )
            """,
            (
                "ecommerce_2019_11",
                source_file,
            ),
        )

        run_id = cur.lastrowid

    conn.commit()

    return int(run_id)


def find_resume_run(conn, source_file: str):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                run_id,
                status,
                total_source_rows,
                total_staging_rows,
                total_events_loaded,
                total_duplicates
            FROM etl_runs
            WHERE job_name = %s
              AND source_file = %s
              AND status IN ('RUNNING', 'FAILED')
            ORDER BY run_id DESC
            LIMIT 1
            """,
            (
                "ecommerce_2019_11",
                source_file,
            ),
        )

        return cur.fetchone()


def get_last_success_batch(conn, run_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT
                batch_no,
                source_end_row
            FROM etl_batches
            WHERE run_id = %s
              AND status = 'SUCCESS'
            ORDER BY batch_no DESC
            LIMIT 1
            """,
            (run_id,),
        )

        return cur.fetchone()


def mark_run_running(conn, run_id: int):
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_runs
            SET
                status = 'RUNNING',
                finished_at = NULL,
                error_message = NULL
            WHERE run_id = %s
            """,
            (run_id,),
        )

    conn.commit()


def create_batch(
    conn,
    run_id: int,
    batch_no: int,
    source_start_row: int,
    source_end_row: int,
    source_rows: int,
) -> int:

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT batch_id, status
            FROM etl_batches
            WHERE run_id = %s
              AND batch_no = %s
            """,
            (run_id, batch_no),
        )

        existing = cur.fetchone()

        if existing:
            batch_id = int(existing[0])

            cur.execute(
                """
                UPDATE etl_batches
                SET
                    source_start_row = %s,
                    source_end_row = %s,
                    source_rows = %s,
                    staging_rows = 0,
                    events_loaded = 0,
                    duplicates_skipped = 0,
                    status = 'RUNNING',
                    started_at = CURRENT_TIMESTAMP(3),
                    finished_at = NULL,
                    error_message = NULL
                WHERE batch_id = %s
                """,
                (
                    source_start_row,
                    source_end_row,
                    source_rows,
                    batch_id,
                ),
            )

            conn.commit()
            return batch_id

        cur.execute(
            """
            INSERT INTO etl_batches (
                run_id,
                batch_no,
                source_start_row,
                source_end_row,
                source_rows,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                'RUNNING'
            )
            """,
            (
                run_id,
                batch_no,
                source_start_row,
                source_end_row,
                source_rows,
            ),
        )

        batch_id = int(cur.lastrowid)

    conn.commit()

    return batch_id


def finish_batch(
    conn,
    batch_id: int,
    status: str,
    staging_rows: int,
    events_loaded: int,
    duplicates_skipped: int,
    error_message: str | None = None,
):

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_batches
            SET
                status = %s,
                finished_at = CURRENT_TIMESTAMP(3),
                staging_rows = %s,
                events_loaded = %s,
                duplicates_skipped = %s,
                error_message = %s
            WHERE batch_id = %s
            """,
            (
                status,
                staging_rows,
                events_loaded,
                duplicates_skipped,
                error_message,
                batch_id,
            ),
        )

    conn.commit()


def finish_run(
    conn,
    run_id: int,
    status: str,
    total_source_rows: int,
    total_staging_rows: int,
    total_events_loaded: int,
    total_duplicates: int,
    error_message: str | None = None,
):

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE etl_runs
            SET
                status = %s,
                finished_at = CURRENT_TIMESTAMP(3),
                total_source_rows = %s,
                total_staging_rows = %s,
                total_events_loaded = %s,
                total_duplicates = %s,
                error_message = %s
            WHERE run_id = %s
            """,
            (
                status,
                total_source_rows,
                total_staging_rows,
                total_events_loaded,
                total_duplicates,
                error_message,
                run_id,
            ),
        )

    conn.commit()


def normalize_value(value):
    if pd.isna(value):
        return None
    return value


def build_rows(df: pd.DataFrame):

    rows = []

    for row in df.itertuples(index=False, name=None):

        rows.append(
            (
                normalize_value(row[0]),
                normalize_value(row[1]),
                int(row[2]),
                int(row[3]),
                normalize_value(row[4]),
                normalize_value(row[5]),
                float(row[6]),
                int(row[7]),
                normalize_value(row[8]),
            )
        )

    return rows


def execute_transformations(conn):

    with conn.cursor() as cur:

        cur.execute(UPSERT_USERS_SQL)

        cur.execute(UPSERT_CATEGORIES_SQL)

        cur.execute(UPSERT_BRANDS_SQL)

        cur.execute(UPSERT_PRODUCTS_SQL)

        cur.execute(UPSERT_PRODUCT_BRANDS_SQL)

        cur.execute(UPSERT_SESSIONS_SQL)

        before = get_count(
            cur,
            "behavior_events"
        )

        cur.execute(
            INSERT_EVENTS_SQL
        )

        after = get_count(
            cur,
            "behavior_events"
        )

    conn.commit()

    return after - before


def process_batch(
    conn,
    df: pd.DataFrame,
    run_id: int,
    batch_no: int,
    source_start_row: int,
    source_end_row: int,
):

    source_rows = len(df)

    batch_id = create_batch(
        conn,
        run_id,
        batch_no,
        source_start_row,
        source_end_row,
        source_rows,
    )

    try:

        clear_staging(conn)

        rows = build_rows(df)

        with conn.cursor() as cur:

            cur.executemany(
                INSERT_STAGING_SQL,
                rows,
            )

            staging_rows = get_count(
                cur,
                "staging_events"
            )

        conn.commit()

        events_loaded = execute_transformations(
            conn
        )

        duplicates_skipped = (
            source_rows - events_loaded
        )

        finish_batch(
            conn,
            batch_id,
            "SUCCESS",
            staging_rows,
            events_loaded,
            duplicates_skipped,
            None,
        )

        clear_staging(conn)

        return (
            staging_rows,
            events_loaded,
            duplicates_skipped,
        )

    except Exception as exc:

        conn.rollback()

        try:
            clear_staging(conn)
        except Exception:
            pass

        finish_batch(
            conn,
            batch_id,
            "FAILED",
            0,
            0,
            0,
            str(exc),
        )

        raise


def process_file(
    conn,
    run_id: int,
    input_path: Path,
    chunksize: int,
    resume_batch_no: int,
):

    total_source_rows = 0
    total_staging_rows = 0
    total_events_loaded = 0
    total_duplicates = 0

    last_success = get_last_success_batch(
        conn,
        run_id,
    )

    if last_success:

        last_batch_no = int(
            last_success[0]
        )

        last_source_end = int(
            last_success[1]
        )

        print(
            f"Resume detected: "
            f"batch={last_batch_no}, "
            f"source_end_row={last_source_end:,}"
        )

    else:

        last_batch_no = 0
        last_source_end = 1

    skip_batches = max(
        last_batch_no,
        resume_batch_no,
    )

    reader = pd.read_csv(
        input_path,
        chunksize=chunksize,
        dtype={
            "event_type": "string",
            "product_id": "int64",
            "category_id": "int64",
            "category_code": "string",
            "brand": "string",
            "price": "float64",
            "user_id": "int64",
            "user_session": "string",
        },
    )

    for batch_no, df in enumerate(
        reader,
        start=1,
    ):

        source_start_row = (
            2
            + (batch_no - 1) * chunksize
        )

        source_end_row = (
            source_start_row
            + len(df)
            - 1
        )

        if batch_no <= skip_batches:

            print(
                f"[Resume] skip batch "
                f"{batch_no}: "
                f"{source_start_row:,}-"
                f"{source_end_row:,}"
            )

            continue

        print(
            f"[Batch {batch_no}] "
            f"rows={len(df):,} "
            f"source="
            f"{source_start_row:,}-"
            f"{source_end_row:,}"
        )

        (
            staging_rows,
            events_loaded,
            duplicates,
        ) = process_batch(
            conn,
            df,
            run_id,
            batch_no,
            source_start_row,
            source_end_row,
        )

        total_source_rows += len(df)

        total_staging_rows += staging_rows

        total_events_loaded += events_loaded

        total_duplicates += duplicates

        print(
            f"  staging={staging_rows:,} "
            f"loaded={events_loaded:,} "
            f"duplicates={duplicates:,}"
        )

    return (
        total_source_rows,
        total_staging_rows,
        total_events_loaded,
        total_duplicates,
    )


def parse_args():

    parser = argparse.ArgumentParser(
        description=(
            "Production ETL for "
            "2019-Nov e-commerce dataset."
        )
    )

    parser.add_argument(
        "--input",
        type=str,
        default=str(DEFAULT_CSV),
    )

    parser.add_argument(
        "--chunksize",
        type=int,
        default=100_000,
    )

    parser.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume the latest RUNNING/FAILED "
            "ETL run."
        ),
    )

    parser.add_argument(
        "--max-batches",
        type=int,
        default=None,
    )

    return parser.parse_args()


def main():

    args = parse_args()

    input_path = Path(
        args.input
    )

    if not input_path.exists():

        print(
            f"ERROR: input file not found: "
            f"{input_path}"
        )

        sys.exit(1)

    conn = get_connection()

    run_id = None

    started = time.time()

    try:

        existing_run = None

        if args.resume:

            existing_run = (
                find_resume_run(
                    conn,
                    str(input_path),
                )
            )

        if existing_run:

            run_id = int(
                existing_run[0]
            )

            print(
                f"Resuming existing run_id={run_id}"
            )

            mark_run_running(
                conn,
                run_id,
            )

        else:

            run_id = create_run(
                conn,
                str(input_path),
            )

            print(
                f"Created new run_id={run_id}"
            )

        print("=" * 70)

        print(
            "E-commerce ETL started"
        )

        print(
            f"run_id    : {run_id}"
        )

        print(
            f"input     : {input_path}"
        )

        print(
            f"chunksize : {args.chunksize}"
        )

        print("=" * 70)

        (
            total_source_rows,
            total_staging_rows,
            total_events_loaded,
            total_duplicates,
        ) = process_file(
            conn,
            run_id,
            input_path,
            args.chunksize,
            0,
        )

        finish_run(
            conn,
            run_id,
            "SUCCESS",
            total_source_rows,
            total_staging_rows,
            total_events_loaded,
            total_duplicates,
            None,
        )

        print("=" * 70)

        print(
            "ETL finished successfully"
        )

        print(
            f"run_id             : {run_id}"
        )

        print(
            f"new source rows    : "
            f"{total_source_rows:,}"
        )

        print(
            f"new staging rows   : "
            f"{total_staging_rows:,}"
        )

        print(
            f"new events loaded  : "
            f"{total_events_loaded:,}"
        )

        print(
            f"new duplicates     : "
            f"{total_duplicates:,}"
        )

        print(
            f"elapsed            : "
            f"{time.time() - started:.1f}s"
        )

        print("=" * 70)

    except KeyboardInterrupt:

        print()
        print(
            "ETL interrupted by user."
        )
        print(
            "Run again with --resume "
            "to continue."
        )

        if run_id is not None:
            try:
                finish_run(
                    conn,
                    run_id,
                    "FAILED",
                    0,
                    0,
                    0,
                    0,
                    "Interrupted by user",
                )
            except Exception:
                pass

        sys.exit(130)

    except Exception as exc:

        print("=" * 70)

        print("ETL FAILED")

        print(
            f"run_id : {run_id}"
        )

        print(
            f"error  : {exc}"
        )

        print("=" * 70)

        if run_id is not None:

            finish_run(
                conn,
                run_id,
                "FAILED",
                0,
                0,
                0,
                0,
                str(exc),
            )

        sys.exit(1)

    finally:

        conn.close()


if __name__ == "__main__":
    main()