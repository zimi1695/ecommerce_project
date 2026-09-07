from pathlib import Path

import pymysql


CSV_FILE = (
    Path("data/processed/staging_test.csv")
    .resolve()
)

DB_CONFIG = {
    "host": "127.0.0.1",
    "port": 3307,
    "user": "ecommerce",
    "password": "ecommerce_2026",
    "database": "ecommerce",
    "charset": "utf8mb4",
    "local_infile": True,
    "autocommit": False,
}


def main() -> None:

    if not CSV_FILE.exists():
        raise FileNotFoundError(CSV_FILE)

    print("=" * 70)
    print("STAGING LOAD TEST")
    print("=" * 70)

    print(f"CSV: {CSV_FILE}")

    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) FROM staging_events"
            )

            before = cursor.fetchone()[0]

            print(
                f"导入前 staging 行数: "
                f"{before:,}"
            )

            load_sql = f"""
                LOAD DATA LOCAL INFILE
                '{CSV_FILE.as_posix()}'
                INTO TABLE staging_events
                FIELDS TERMINATED BY ','
                OPTIONALLY ENCLOSED BY '"'
                LINES TERMINATED BY '\\n'
                IGNORE 1 LINES
                (
                    event_time_raw,
                    event_type,
                    product_id,
                    category_id,
                    @category_code,
                    @brand,
                    price,
                    user_id,
                    @user_session
                )
                SET
                    category_code =
                        NULLIF(@category_code, ''),
                    brand =
                        NULLIF(@brand, ''),
                    user_session =
                        NULLIF(@user_session, '')
            """

            cursor.execute(load_sql)

            print(
                f"本次 LOAD DATA 写入: "
                f"{cursor.rowcount:,}"
            )

        connection.commit()

        with connection.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) FROM staging_events"
            )

            after = cursor.fetchone()[0]

        print(
            f"导入后 staging 行数: "
            f"{after:,}"
        )

        print()
        print("=" * 70)
        print("STAGING LOAD TEST SUCCESS")
        print("=" * 70)

    except Exception:
        connection.rollback()
        print("加载失败，事务已回滚。")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()