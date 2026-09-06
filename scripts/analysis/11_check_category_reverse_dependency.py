import pandas as pd

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# category_code -> category_id
code_to_category = {}

# 记录冲突
conflicts = {}

print("开始检查 category_code -> category_id ...")
print("这是完整数据扫描。")
print()

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "category_id",
            "category_code"
        ]
    ),
    start=1
):
    print(f"处理第 {chunk_no} 块...")

    valid = df.dropna(
        subset=["category_code"]
    )

    for category_id, category_code in zip(
        valid["category_id"],
        valid["category_code"]
    ):
        category_id = int(category_id)
        category_code = str(category_code).strip()

        old_category_id = code_to_category.get(
            category_code
        )

        if old_category_id is None:
            code_to_category[category_code] = category_id

        elif old_category_id != category_id:
            conflicts.setdefault(
                category_code,
                set()
            ).update(
                [old_category_id, category_id]
            )

print()
print("=" * 70)
print("反向依赖检查结果")
print("=" * 70)

print(
    f"不同非空 category_code 数量: "
    f"{len(code_to_category):,}"
)

print(
    f"一个 category_code 对应多个 category_id 的数量: "
    f"{len(conflicts):,}"
)

if conflicts:
    print()
    print("冲突案例（最多 20 个）：")

    for code, category_ids in list(
        sorted(conflicts.items())
    )[:20]:
        print(
            f"  {code} -> "
            f"{sorted(category_ids)}"
        )

print()
print("检查完成。")
