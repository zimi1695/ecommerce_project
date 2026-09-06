from pathlib import Path

import pymysql


CSV_FILE = Path(
    "data/processed/load_test_events.csv"
).resolve()

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
    print("=" * 70)
    print("MySQL LOAD DATA 测试")
    print("=" * 70)

    print(f"CSV: {CSV_FILE}")
    print(f"存在: {CSV_FILE.exists()}")

    if not CSV_FILE.exists():
        raise FileNotFoundError(CSV_FILE)

    connection = pymysql.connect(**DB_CONFIG)

    try:
        with connection.cursor() as cursor:

            # 确认当前表为空
            cursor.execute(
                "SELECT COUNT(*) FROM behavior_events"
            )

            before = cursor.fetchone()[0]

            print(f"导入前事件数: {before:,}")

            # user_session 允许 NULL
            # brand_id 暂时写 NULL
            load_sql = f"""
                LOAD DATA LOCAL INFILE '{CSV_FILE.as_posix()}'
                IGNORE
                INTO TABLE behavior_events
                FIELDS TERMINATED BY ','
                OPTIONALLY ENCLOSED BY '"'
                LINES TERMINATED BY '\\n'
                IGNORE 1 LINES
                (
                    event_time,
                    event_type,
                    user_id,
                    @session_id,
                    product_id,
                    price,
                    @source_event_hash
                )
                SET
                    session_id = NULLIF(@session_id, ''),
                    brand_id = NULL,
                    source_event_hash =
                        UNHEX(@source_event_hash)
            """

            cursor.execute(load_sql)

            print(
                f"LOAD DATA affected rows: "
                f"{cursor.rowcount:,}"
            )

        connection.commit()

        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) FROM behavior_events"
            )

            after = cursor.fetchone()[0]

        print()
        print(f"导入后事件数: {after:,}")

        print()
        print("=" * 70)
        print("LOAD DATA 测试成功")
        print("=" * 70)

    except Exception:
        connection.rollback()
        print("LOAD DATA 失败，事务已回滚。")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()