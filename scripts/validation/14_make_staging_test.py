from pathlib import Path

import pandas as pd


SOURCE = Path("data/raw/2019-Nov.csv")
OUTPUT = Path("data/processed/staging_test.csv")

ROWS = 100_000


def main() -> None:
    print(f"读取前 {ROWS:,} 行...")

    df = pd.read_csv(
        SOURCE,
        nrows=ROWS,
        low_memory=False,
    )

    output = df[
        [
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
    ].copy()

    # MySQL staging 表按字符串接收 event_time。
    # 原始数据格式：
    # 2019-11-01 00:00:00 UTC

    output.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    print()
    print("=" * 60)
    print("Staging 测试文件生成完成")
    print("=" * 60)
    print(f"输出: {OUTPUT}")
    print(f"行数: {len(output):,}")
    print(
        f"大小: "
        f"{OUTPUT.stat().st_size / 1024 / 1024:.2f} MB"
    )


if __name__ == "__main__":
    main()