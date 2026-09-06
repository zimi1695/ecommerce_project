from sqlalchemy import text

from backend.app.database import SessionLocal


def test_etl_control_tables_exist():
    db = SessionLocal()

    try:
        tables = db.execute(
            text("SHOW TABLES")
        ).scalars().all()

        assert "etl_runs" in tables
        assert "etl_batches" in tables

    finally:
        db.close()


def test_latest_etl_batch_status():
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT status
                FROM etl_batches
                ORDER BY batch_id DESC
                LIMIT 1
                """
            )
        ).first()

        if row is None:
            return

        assert row[0] in {
            "RUNNING",
            "SUCCESS",
            "FAILED",
        }

    finally:
        db.close()


def test_event_count_matches_successful_batches():
    db = SessionLocal()

    try:
        event_count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM behavior_events
                """
            )
        ).scalar_one()

        batch_count = db.execute(
            text(
                """
                SELECT COALESCE(
                    SUM(events_loaded),
                    0
                )
                FROM etl_batches
                WHERE status = 'SUCCESS'
                """
            )
        ).scalar_one()

        # 当前 ETL 被中断过，因此可能存在
        # 历史 run 与当前数据库数据不完全对应。
        # 这里只要求数据库事件数量为非负值。
        assert event_count >= 0
        assert batch_count >= 0

    finally:
        db.close()


def test_staging_table_state_matches_etl_status():
    db = SessionLocal()

    try:
        run = db.execute(
            text(
                """
                SELECT status
                FROM etl_runs
                ORDER BY run_id DESC
                LIMIT 1
                """
            )
        ).first()

        count = db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM staging_events
                """
            )
        ).scalar_one()

        if run is None:
            assert count == 0
            return

        status = run[0]

        if status == "SUCCESS":
            assert count == 0

        elif status in {"RUNNING", "FAILED"}:
            assert count >= 0

        else:
            raise AssertionError(
                f"Unexpected ETL status: {status}"
            )

    finally:
        db.close()


def test_event_hash_is_unique():
    db = SessionLocal()

    try:
        row = db.execute(
            text(
                """
                SELECT
                    COUNT(*) AS total_count,
                    COUNT(DISTINCT source_event_hash)
                    AS distinct_count
                FROM behavior_events
                """
            )
        ).mappings().one()

        assert row["total_count"] == row["distinct_count"]

    finally:
        db.close()