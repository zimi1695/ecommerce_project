import pandas as pd

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# product -> category
product_categories = {}

# product -> brand
product_brands = {}

# product -> prices
product_prices = {}

print("开始检查 product_id 的字段依赖关系...")

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "product_id",
            "category_id",
            "brand",
            "price"
        ]
    ),
    start=1
):
    print(f"处理第 {chunk_no} 块...")

    # 检查 product -> category
    for product_id, category_id in zip(
        df["product_id"],
        df["category_id"]
    ):
        old = product_categories.get(product_id)

        if old is None:
            product_categories[product_id] = category_id
        elif old != category_id:
            product_categories[product_id] = "__CONFLICT__"

    # 检查 product -> brand
    for product_id, brand in zip(
        df["product_id"],
        df["brand"]
    ):
        if pd.isna(brand):
            continue

        brand = str(brand)

        old = product_brands.get(product_id)

        if old is None:
            product_brands[product_id] = brand
        elif old != brand:
            product_brands[product_id] = "__CONFLICT__"

    # 检查 product -> price
    for product_id, price in zip(
        df["product_id"],
        df["price"]
    ):
        if pd.isna(price):
            continue

        old = product_prices.get(product_id)

        if old is None:
            product_prices[product_id] = {price}
        else:
            old.add(price)


category_conflicts = sum(
    1 for v in product_categories.values()
    if v == "__CONFLICT__"
)

brand_conflicts = sum(
    1 for v in product_brands.values()
    if v == "__CONFLICT__"
)

products_with_multiple_prices = sum(
    1 for prices in product_prices.values()
    if len(prices) > 1
)

print()
print("=" * 60)
print("检查结果")
print("=" * 60)

print(f"商品数量: {len(product_categories):,}")

print()
print("product_id -> category_id")
print(f"存在冲突的商品: {category_conflicts:,}")

print()
print("product_id -> brand")
print(f"存在冲突的商品: {brand_conflicts:,}")

print()
print("product_id -> price")
print(
    f"存在多个价格的商品: "
    f"{products_with_multiple_prices:,}"
)

print()
print("检查完成。")
