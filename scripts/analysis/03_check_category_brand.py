import pandas as pd
from collections import defaultdict

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# category_id -> set(category_code)
category_codes = defaultdict(set)

# product_id -> set(brand)
product_brands = defaultdict(set)

print("开始检查 category_id -> category_code ...")
print("以及 product_id -> brand ...")
print()

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "product_id",
            "category_id",
            "category_code",
            "brand"
        ]
    ),
    start=1
):
    print(f"处理第 {chunk_no} 块...")

    # category_id -> category_code
    for category_id, category_code in zip(
        df["category_id"],
        df["category_code"]
    ):
        if pd.notna(category_code):
            category_codes[category_id].add(
                str(category_code)
            )

    # product_id -> brand
    for product_id, brand in zip(
        df["product_id"],
        df["brand"]
    ):
        if pd.notna(brand):
            product_brands[product_id].add(
                str(brand)
            )

print()
print("=" * 60)
print("检查结果")
print("=" * 60)

# category 冲突
category_conflicts = {
    category_id: codes
    for category_id, codes in category_codes.items()
    if len(codes) > 1
}

print()
print("category_id -> category_code")
print(
    f"不同 category_code 的 category_id 数量: "
    f"{len(category_conflicts):,}"
)

# 输出部分案例
if category_conflicts:
    print()
    print("category 冲突案例（最多10个）：")

    for category_id, codes in list(
        category_conflicts.items()
    )[:10]:
        print(
            f"  category_id={category_id}"
            f" -> {sorted(codes)}"
        )

# brand 冲突
brand_conflicts = {
    product_id: brands
    for product_id, brands in product_brands.items()
    if len(brands) > 1
}

print()
print("product_id -> brand")
print(
    f"存在多个非空品牌的商品数量: "
    f"{len(brand_conflicts):,}"
)

if brand_conflicts:
    print()
    print("brand 冲突案例（最多20个）：")

    for product_id, brands in list(
        brand_conflicts.items()
    )[:20]:
        print(
            f"  product_id={product_id}"
            f" -> {sorted(brands)}"
        )

print()
print("检查完成。")
