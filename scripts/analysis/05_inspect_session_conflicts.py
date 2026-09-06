import pandas as pd
from collections import defaultdict

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# 第一遍：找出存在多个用户的 session
session_users = defaultdict(set)

print("第一阶段：寻找异常 Session...")

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "event_time",
            "user_id",
            "user_session",
        ]
    ),
    start=1
):
    print(f"处理第 {chunk_no} 块...")

    valid = df.dropna(subset=["user_session"])

    for session_id, user_id in zip(
        valid["user_session"],
        valid["user_id"]
    ):
        session_users[str(session_id)].add(user_id)

conflict_sessions = {
    session_id
    for session_id, users in session_users.items()
    if len(users) > 1
}

print()
print(f"发现异常 Session: {len(conflict_sessions):,}")

# 第二阶段：重新扫描，只提取这些 session
print()
print("第二阶段：提取异常 Session 的具体事件...")

examples = defaultdict(list)

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "event_time",
            "event_type",
            "product_id",
            "user_id",
            "user_session",
            "price"
        ]
    ),
    start=1
):
    valid = df[
        df["user_session"].astype(str).isin(conflict_sessions)
    ]

    for _, row in valid.iterrows():
        session_id = str(row["user_session"])

        if len(examples[session_id]) < 10:
            examples[session_id].append({
                "event_time": row["event_time"],
                "event_type": row["event_type"],
                "product_id": row["product_id"],
                "user_id": row["user_id"],
                "price": row["price"],
            })

    # 找够 5 个案例后就可以提前结束
    if len(examples) >= 5:
        break

print()
print("=" * 80)
print("异常 Session 示例")
print("=" * 80)

for session_id, events in list(examples.items())[:5]:

    print()
    print(f"Session: {session_id}")
    print("-" * 80)

    for event in sorted(
        events,
        key=lambda x: x["event_time"]
    ):
        print(
            f"{event['event_time']} | "
            f"user={event['user_id']} | "
            f"{event['event_type']} | "
            f"product={event['product_id']} | "
            f"price={event['price']}"
        )

print()
print("检查完成。")
