import pandas as pd
from collections import defaultdict

FILE = "data/raw/2019-Nov.csv"
CHUNK_SIZE = 1_000_000

# session_id -> user_id 集合
session_users = defaultdict(set)

print("开始检查 user_session -> user_id ...")
print()

for chunk_no, df in enumerate(
    pd.read_csv(
        FILE,
        chunksize=CHUNK_SIZE,
        low_memory=False,
        usecols=[
            "user_session",
            "user_id"
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

conflicts = {
    session_id: users
    for session_id, users in session_users.items()
    if len(users) > 1
}

print()
print("=" * 60)
print("检查结果")
print("=" * 60)

print(f"Session 数量: {len(session_users):,}")

print(
    f"一个 Session 对应多个用户的数量: "
    f"{len(conflicts):,}"
)

if conflicts:
    print()
    print("冲突案例（最多20个）：")

    for session_id, users in list(conflicts.items())[:20]:
        print(
            f"  session={session_id}"
            f" -> users={sorted(users)}"
        )

print()
print("检查完成。")
