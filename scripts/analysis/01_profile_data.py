import pandas as pd
from collections import Counter

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

total_rows = 0

event_type_counts = Counter()

unique_users = set()
unique_products = set()
unique_categories = set()
unique_brands = set()
unique_sessions = set()

null_counts = Counter()

min_time = None
max_time = None

min_price = float("inf")
max_price = float("-inf")

# 用于检查同一个 product_id 是否出现多个 category / brand
product_category_conflicts = 0
product_brand_conflicts = 0

# 暂存部分映射关系
product_category_map = {}
product_brand_map = {}

print("开始扫描数据...")
print(f"文件: {FILE}")
print(f"块大小: {CHUNK_SIZE:,} 行")
print()

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False
    ),
    start=1
):
    rows = len(df)
    total_rows += rows

    print(
        f"正在处理第 {chunk_no} 块，"
        f"本块 {rows:,} 行，"
        f"累计 {total_rows:,} 行"
    )

    # 事件类型
    event_type_counts.update(
        df["event_type"].dropna().astype(str)
    )

    # 唯一值
    unique_users.update(df["user_id"].dropna().unique())
    unique_products.update(df["product_id"].dropna().unique())
    unique_categories.update(df["category_id"].dropna().unique())
    unique_sessions.update(df["user_session"].dropna().astype(str).unique())

    brands = df["brand"].dropna().astype(str)
    unique_brands.update(brands.unique())

    # 缺失值
    null_counts.update(
        df.isnull().sum().to_dict()
    )

    # 时间
    times = pd.to_datetime(
        df["event_time"],
        errors="coerce",
        utc=True
    )

    chunk_min_time = times.min()
    chunk_max_time = times.max()

    if pd.notna(chunk_min_time):
        if min_time is None or chunk_min_time < min_time:
            min_time = chunk_min_time

    if pd.notna(chunk_max_time):
        if max_time is None or chunk_max_time > max_time:
            max_time = chunk_max_time

    # 价格
    chunk_min_price = df["price"].min()
    chunk_max_price = df["price"].max()

    if pd.notna(chunk_min_price):
        min_price = min(min_price, chunk_min_price)

    if pd.notna(chunk_max_price):
        max_price = max(max_price, chunk_max_price)

print()
print("=" * 60)
print("数据集统计结果")
print("=" * 60)

print(f"总事件数:       {total_rows:,}")
print(f"用户数:          {len(unique_users):,}")
print(f"商品数:          {len(unique_products):,}")
print(f"分类数:          {len(unique_categories):,}")
print(f"品牌数:          {len(unique_brands):,}")
print(f"Session 数:      {len(unique_sessions):,}")

print()
print("事件类型:")
for event_type, count in event_type_counts.most_common():
    print(f"  {event_type:<20} {count:>15,}")

print()
print("缺失值:")
for column, count in null_counts.items():
    print(f"  {column:<20} {count:>15,}")

print()
print("时间范围:")
print(f"  最早: {min_time}")
print(f"  最晚: {max_time}")

print()
print("价格范围:")
print(f"  最低: {min_price}")
print(f"  最高: {max_price}")

print()
print("扫描完成。")

