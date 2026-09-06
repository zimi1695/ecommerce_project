import pandas as pd
from collections import defaultdict

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# product_id -> set(brand)
product_brands = defaultdict(set)

print("开始扫描商品品牌...")
print()

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "product_id",
            "brand"
        ]
    ),
    start=1
):
    print(f"处理第 {chunk_no} 块...")

    # 只处理有品牌的数据
    valid = df.dropna(subset=["brand"])

    for product_id, brand in zip(
        valid["product_id"],
        valid["brand"]
    ):
        product_brands[product_id].add(str(brand).strip())

# 找出一个商品对应多个品牌的情况
conflicts = {
    product_id: sorted(brands)
    for product_id, brands in product_brands.items()
    if len(brands) > 1
}

print()
print("=" * 80)
print("品牌冲突统计")
print("=" * 80)

print(f"冲突商品数量: {len(conflicts):,}")

print()
print("全部冲突商品：")
print("-" * 80)

for product_id, brands in sorted(conflicts.items()):
    print(
        f"product_id={product_id} "
        f"-> {', '.join(brands)}"
    )

# 同时输出 CSV，方便后续人工检查
output_file = "data/processed/brand_conflicts.csv"

rows = []

for product_id, brands in sorted(conflicts.items()):
    rows.append({
        "product_id": product_id,
        "brands": " | ".join(brands),
        "brand_count": len(brands)
    })

result = pd.DataFrame(rows)

result.to_csv(
    output_file,
    index=False,
    encoding="utf-8"
)

print()
print("=" * 80)
print(f"冲突数据已保存到：{output_file}")
print("=" * 80)
print()
print("检查完成。")
