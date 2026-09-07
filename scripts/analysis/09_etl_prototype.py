import pandas as pd
import pymysql
from collections import OrderedDict

# ============================================================
# Configuration
# ============================================================

CSV_FILE = "data/raw/2019-Nov.csv"

MAX_ROWS = 1_000_000
CHUNK_SIZE = 100_000

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "ecommerce",
    "password": "ecommerce_2026",
    "database": "ecommerce",
    "charset": "utf8mb4",
    "autocommit": False,
}

# ============================================================
# Database connection
# ============================================================

conn = pymysql.connect(**DB_CONFIG)

try:
    cursor = conn.cursor()

    print("=" * 70)
    print("ETL TEST")
    print("=" * 70)
    print(f"Source: {CSV_FILE}")
    print(f"Maximum rows: {MAX_ROWS:,}")
    print(f"Chunk size: {CHUNK_SIZE:,}")
    print()

    # --------------------------------------------------------
    # Read first 1,000,000 rows
    # --------------------------------------------------------

    all_chunks = []

    rows_read = 0

    for df in pd.read_csv(
        CSV_FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False
    ):
        remaining = MAX_ROWS - rows_read

        if len(df) > remaining:
            df = df.iloc[:remaining]

        all_chunks.append(df)
        rows_read += len(df)

        print(f"读取进度: {rows_read:,} / {MAX_ROWS:,}")

        if rows_read >= MAX_ROWS:
            break

    df = pd.concat(all_chunks, ignore_index=True)

    print()
    print(f"实际读取: {len(df):,}")

    # --------------------------------------------------------
    # Remove exact duplicates
    # --------------------------------------------------------

    original_count = len(df)

    df = df.drop_duplicates(
        subset=[
            "event_time",
            "event_type",
            "product_id",
            "category_id",
            "category_code",
            "brand",
            "price",
            "user_id",
            "user_session",
        ]
    )

    duplicate_count = original_count - len(df)

    print(f"完全重复记录: {duplicate_count:,}")
    print(f"去重后事件数: {len(df):,}")

    # --------------------------------------------------------
    # Normalize data types
    # --------------------------------------------------------

    df["event_time"] = pd.to_datetime(
        df["event_time"],
        utc=True
    )

    df["event_time"] = df["event_time"].dt.strftime(
        "%Y-%m-%d %H:%M:%S.%f"
    )

    df["brand"] = df["brand"].where(
        df["brand"].notna(),
        None
    )

    df["category_code"] = df["category_code"].where(
        df["category_code"].notna(),
        None
    )

    df["user_session"] = df["user_session"].where(
        df["user_session"].notna(),
        None
    )

    # --------------------------------------------------------
    # Build users
    # --------------------------------------------------------

    users = sorted(
        set(df["user_id"].astype(int))
    )

    print(f"Users: {len(users):,}")

    # --------------------------------------------------------
    # Build categories
    # --------------------------------------------------------

    categories_dict = OrderedDict()

    for category_id, category_code in zip(
        df["category_id"],
        df["category_code"]
    ):
        category_id = int(category_id)

        if category_id not in categories_dict:
            categories_dict[category_id] = category_code

        elif (
            categories_dict[category_id] is None
            and category_code is not None
        ):
            categories_dict[category_id] = category_code

    print(f"Categories: {len(categories_dict):,}")

    # --------------------------------------------------------
    # Build brands
    # --------------------------------------------------------

    brand_names = sorted(
        set(
            df.loc[
                df["brand"].notna(),
                "brand"
            ].astype(str).str.strip()
        )
    )

    print(f"Brands: {len(brand_names):,}")

    # --------------------------------------------------------
    # Build products
    # --------------------------------------------------------

    product_category = {}

    for product_id, category_id in zip(
        df["product_id"],
        df["category_id"]
    ):
        product_id = int(product_id)
        category_id = int(category_id)

        if product_id not in product_category:
            product_category[product_id] = category_id

    print(f"Products: {len(product_category):,}")

    # --------------------------------------------------------
    # Build sessions
    # --------------------------------------------------------

    session_info = {}

    for session_id, event_time in zip(
        df["user_session"],
        df["event_time"]
    ):
        if session_id is None:
            continue

        if session_id not in session_info:
            session_info[session_id] = [
                event_time,
                event_time,
                1,
            ]
        else:
            info = session_info[session_id]

            if event_time < info[0]:
                info[0] = event_time

            if event_time > info[1]:
                info[1] = event_time

            info[2] += 1

    print(f"Sessions: {len(session_info):,}")

    # --------------------------------------------------------
    # Start transaction
    # --------------------------------------------------------

    print()
    print("开始写入 MySQL...")

    # --------------------------------------------------------
    # users
    # --------------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO users (user_id)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE user_id = VALUES(user_id)
        """,
        [(user_id,) for user_id in users]
    )

    print("users ✓")

    # --------------------------------------------------------
    # categories
    # --------------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO categories (
            category_id,
            category_code
        )
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            category_code =
                COALESCE(
                    categories.category_code,
                    VALUES(category_code)
                )
        """,
        [
            (category_id, category_code)
            for category_id, category_code
            in categories_dict.items()
        ]
    )

    print("categories ✓")

    # --------------------------------------------------------
    # brands
    # --------------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO brands (brand_name)
        VALUES (%s)
        ON DUPLICATE KEY UPDATE
            brand_name = VALUES(brand_name)
        """,
        [(brand,) for brand in brand_names]
    )

    print("brands ✓")

    # --------------------------------------------------------
    # Get brand IDs
    # --------------------------------------------------------

    brand_id_map = {}

    if brand_names:
        placeholders = ",".join(
            ["%s"] * len(brand_names)
        )

        cursor.execute(
            f"""
            SELECT brand_id, brand_name
            FROM brands
            WHERE brand_name IN ({placeholders})
            """,
            brand_names
        )

        for brand_id, brand_name in cursor.fetchall():
            brand_id_map[brand_name] = brand_id

    # --------------------------------------------------------
    # products
    # --------------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO products (
            product_id,
            category_id
        )
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE
            category_id = VALUES(category_id)
        """,
        [
            (product_id, category_id)
            for product_id, category_id
            in product_category.items()
        ]
    )

    print("products ✓")

    # --------------------------------------------------------
    # product_brands
    # --------------------------------------------------------

    product_brand_rows = set()

    for product_id, brand in zip(
        df["product_id"],
        df["brand"]
    ):
        if brand is None:
            continue

        brand = str(brand).strip()

        brand_id = brand_id_map.get(brand)

        if brand_id is not None:
            product_brand_rows.add(
                (int(product_id), brand_id)
            )

    cursor.executemany(
        """
        INSERT IGNORE INTO product_brands (
            product_id,
            brand_id
        )
        VALUES (%s, %s)
        """,
        list(product_brand_rows)
    )

    print("product_brands ✓")

    # --------------------------------------------------------
    # sessions
    # --------------------------------------------------------

    cursor.executemany(
        """
        INSERT INTO sessions (
            session_id,
            start_time,
            end_time,
            event_count
        )
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            start_time = LEAST(
                sessions.start_time,
                VALUES(start_time)
            ),
            end_time = GREATEST(
                sessions.end_time,
                VALUES(end_time)
            ),
            event_count = VALUES(event_count)
        """,
        [
            (
                session_id,
                start_time,
                end_time,
                event_count
            )
            for session_id,
            (
                start_time,
                end_time,
                event_count
            )
            in session_info.items()
        ]
    )

    print("sessions ✓")

    # --------------------------------------------------------
    # behavior_events
    # --------------------------------------------------------

    event_rows = []

    for row in df.itertuples(index=False):

        brand = row.brand

        if brand is not None:
            brand = str(brand).strip()

        brand_id = brand_id_map.get(brand)

        event_rows.append(
            (
                row.event_time,
                row.event_type,
                int(row.user_id),
                row.user_session,
                int(row.product_id),
                brand_id,
                float(row.price),
            )
        )

    cursor.executemany(
        """
        INSERT INTO behavior_events (
            event_time,
            event_type,
            user_id,
            session_id,
            product_id,
            brand_id,
            price
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s
        )
        """,
        event_rows
    )

    print("behavior_events ✓")

    # --------------------------------------------------------
    # Commit
    # --------------------------------------------------------

    conn.commit()

    print()
    print("=" * 70)
    print("ETL TEST SUCCESS")
    print("=" * 70)

except Exception:
    conn.rollback()
    print()
    print("ETL 失败，事务已回滚。")
    raise

finally:
    conn.close()
