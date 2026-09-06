import pandas as pd

FILE = "data/raw/2019-Nov.csv"

print("读取前 1,000,000 行...")

df = pd.read_csv(
    FILE,
    nrows=1_000_000,
    low_memory=False,
    usecols=[
        "product_id",
        "category_id",
        "category_code",
    ],
)

# ------------------------------------------------------------
# 所有 category_id
# ------------------------------------------------------------

category_ids = set(
    df["category_id"]
    .dropna()
    .astype("int64")
    .tolist()
)

# ------------------------------------------------------------
# products 中出现的 category_id
# ------------------------------------------------------------

product_categories = (
    df[["product_id", "category_id"]]
    .drop_duplicates("product_id")
)

product_category_ids = set(
    product_categories["category_id"]
    .dropna()
    .astype("int64")
    .tolist()
)

# ------------------------------------------------------------
# 检查集合关系
# ------------------------------------------------------------

missing_in_categories = (
    product_category_ids - category_ids
)

missing_in_products = (
    category_ids - product_category_ids
)

print()
print("=" * 70)
print("Category 一致性检查")
print("=" * 70)

print(
    f"原始数据中 category_id 数量: "
    f"{len(category_ids):,}"
)

print(
    f"商品实际引用的 category_id 数量: "
    f"{len(product_category_ids):,}"
)

print(
    f"商品引用但 category 集合中不存在: "
    f"{len(missing_in_categories):,}"
)

print(
    f"category 存在但没有商品引用: "
    f"{len(missing_in_products):,}"
)

if missing_in_categories:
    print()
    print("异常 category_id：")
    for x in sorted(missing_in_categories):
        print(x)

print()
print("=" * 70)
print("Category ID 示例")
print("=" * 70)

print(
    product_categories
    .sort_values("category_id")
    .head(20)
    .to_string(index=False)
)

print()
print("检查完成。")
