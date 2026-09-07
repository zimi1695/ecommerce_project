from pathlib import Path

import pandas as pd


SOURCE = Path("data/raw/2019-Nov.csv")
OUTPUT = Path("data/processed/load_test_events.csv")

ROWS = 100_000


def main() -> None:
    print(f"读取前 {ROWS:,} 行...")

    df = pd.read_csv(
        SOURCE,
        nrows=ROWS,
        low_memory=False,
    )

    # 完全按照原始事件的 9 个字段生成稳定 hash
    hash_columns = [
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

    # 对 NULL 做统一处理，避免 hash 因 NaN/None 表示方式不同而变化
    normalized = df[hash_columns].copy()

    for column in normalized.columns:
        normalized[column] = normalized[column].where(
            normalized[column].notna(),
            ""
        ).astype(str)

    df["source_event_hash"] = pd.util.hash_pandas_object(
        normalized,
        index=False,
    )

    # hash_pandas_object 是 uint64，不是我们最终要的 SHA-256。
    # 所以这里改为 SHA-256。
    import hashlib

    hashes = []

    for row in normalized.itertuples(index=False, name=None):
        raw = "\x1f".join(row).encode("utf-8")
        hashes.append(hashlib.sha256(raw).hexdigest())

    df["source_event_hash"] = hashes

    # MySQL LOAD DATA 测试表只需要最终需要导入的字段。
    output_df = df[
        [
            "event_time",
            "event_type",
            "user_id",
            "user_session",
            "product_id",
            "price",
            "source_event_hash",
        ]
    ].copy()

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    output_df.to_csv(
        OUTPUT,
        index=False,
        encoding="utf-8",
        lineterminator="\n",
    )

    print()
    print("=" * 60)
    print("LOAD DATA 测试文件生成完成")
    print("=" * 60)
    print(f"输出: {OUTPUT}")
    print(f"行数: {len(output_df):,}")
    print(f"大小: {OUTPUT.stat().st_size / 1024 / 1024:.2f} MB")


if __name__ == "__main__":
    main()