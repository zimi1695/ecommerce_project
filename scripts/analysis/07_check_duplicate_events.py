import pandas as pd
import hashlib

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# 只检查事件字段，不包括我们后面生成的 event_id
USE_COLS = [
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

# 用 hash 记录已经见过的事件
seen = set()

duplicate_count = 0

print("开始检查完全重复的事件记录...")
print()

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=USE_COLS
    ),
    start=1
):
    print(f"处理第 {chunk_no} 块...")

    # 将每一行转换为稳定字符串后计算 hash
    for row in df.itertuples(index=False, name=None):

        row_string = "\x1f".join(
            "" if pd.isna(value) else str(value)
            for value in row
        )

        row_hash = hashlib.blake2b(
            row_string.encode("utf-8"),
            digest_size=16
        ).digest()

        if row_hash in seen:
            duplicate_count += 1
        else:
            seen.add(row_hash)

print()
print("=" * 60)
print("重复事件检查结果")
print("=" * 60)
print(f"完全重复记录数量: {duplicate_count:,}")
print()
print("检查完成。")
