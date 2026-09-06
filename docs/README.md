# 基于 MySQL 的多品类电商用户行为分析与管理系统

**项目类型：** 数据库课程实践 / 数据库应用系统  
**项目名称：** 基于 MySQL 的多品类电商用户行为分析与管理系统  
**数据集：** Kaggle — eCommerce behavior data from multi category store  
**数据文件：** `2019-Nov.csv`  
**数据库：** MySQL 8.0 / Docker  
**后端：** FastAPI + SQLAlchemy + PyMySQL  
**数据处理：** Python 3.11 + pandas  
**测试：** pytest  
**开发环境：** WSL2 Ubuntu + Conda

---

## 1. 项目定位

本项目不是商城前台，而是一个面向电商运营分析的数据库应用系统。

系统围绕用户行为事件建立数据库，并提供：

- 数据总览
- 商品查询与商品统计
- 用户行为查询
- Session 分析
- 商品 / 品牌 / 类别排行
- 浏览 → 加购 → 购买漏斗分析
- 数据库视图
- ETL 数据加载与幂等控制
- REST API
- 自动化测试

课程任务要求完成业务调查、系统分析与设计、数据库设计、数据库创建与数据加载、应用软件开发、系统测试、文档和演示。本项目的开发路径按这些交付物反向设计。

---

# 2. 开发路线

```text
选题
 ↓
原始数据探索
 ↓
数据依赖验证
 ↓
数据库建模
 ↓
MySQL + Docker
 ↓
小规模加载测试
 ↓
ETL 正式版本
 ↓
6M 级真实数据验证
 ↓
FastAPI
 ↓
数据库 View
 ↓
API / DB / ETL 自动化测试
 ↓
前端与文档
 ↓
最终联调
```

核心原则：

> 先用真实数据证明依赖关系，再决定表结构；先验证小批量，再扩大规模；每次修改都用自动化测试回归。

---

# 3. 数据集与数据规模

原始 CSV：

```text
data/raw/2019-Nov.csv
```

压缩包：

```text
data/raw/2019-Nov.csv.zip
```

原始 CSV 实际大小约：

```text
9.0 GB
```

完整扫描结果：

| 指标 | 数量 |
|---|---:|
| 原始事件行 | 67,501,979 |
| 用户 | 3,696,117 |
| 商品 | 190,662 |
| category_id | 684 |
| 品牌 | 4,200 |
| Session | 13,776,050 |

事件类型：

| event_type | 数量 |
|---|---:|
| view | 63,556,110 |
| cart | 3,028,930 |
| purchase | 916,939 |

缺失值：

| 字段 | 缺失数 |
|---|---:|
| category_code | 21,898,171 |
| brand | 9,224,078 |
| user_session | 10 |
| 其他字段 | 0 |

时间范围：

```text
2019-11-01 00:00:00 UTC
~
2019-11-30 23:59:59 UTC
```

价格范围：

```text
0.00 ~ 2574.07
```

---

# 4. 数据建模不是凭字段名称决定的

数据库设计前做了完整数据依赖检查。

## 4.1 product_id → category_id

结果：

```text
稳定
冲突数：0
```

因此：

```text
products.category_id
```

可以建外键。

---

## 4.2 product_id → price

结果：

```text
不稳定
```

共有：

```text
70,684
```

个商品出现多个价格。

结论：

```text
price 不属于 products
price 属于 behavior_events
```

这样保存的是“行为发生时的价格”，而不是人为假设的单一商品价格。

---

## 4.3 product_id → brand

结果：

```text
存在冲突
```

共有：

```text
136
```

个商品出现多个非空品牌。

典型值：

```text
lenovo / samsung
hasbro / nerf
bugati / bugatti
dirkje / dirkjebabywear
ikea / imperial
```

没有人工清洗这些关系。

模型改为：

```text
products
    │
    └── product_brands ── brands
```

即产品与品牌使用关联表。

---

## 4.4 category_id → category_code

结果：

```text
稳定
冲突数：0
```

因此：

```text
categories.category_id
categories.category_code
```

可以同时保存。

---

## 4.5 category_code → category_id

结果：

```text
不稳定
```

完整扫描得到：

```text
129 个非空 category_code
其中 58 个 category_code 对应多个 category_id
```

因此不能：

```sql
UNIQUE(category_code)
```

这是项目早期出现过的实际错误。

---

## 4.6 user_session → user_id

结果：

```text
不稳定
```

共有：

```text
591
```

个 Session ID 关联多个 user_id。

结论：

```text
sessions 不存 user_id
```

用户与 Session 的真实关系保留在：

```text
behavior_events.user_id
behavior_events.session_id
```

---

## 4.7 完全重复事件

完整扫描得到：

```text
100,519
```

条完全重复记录。

因此理论唯一事件数：

```text
67,501,979 - 100,519
= 67,401,460
```

数据库使用：

```text
source_event_hash BINARY(32) UNIQUE
```

作为最终幂等约束。

---

# 5. 数据库设计

核心业务表：

```text
users
categories
brands
products
product_brands
sessions
behavior_events
```

ETL 控制表：

```text
staging_events
etl_runs
etl_batches
```

---

## 5.1 users

```text
user_id BIGINT UNSIGNED PRIMARY KEY
```

---

## 5.2 categories

```text
category_id BIGINT UNSIGNED PRIMARY KEY
category_code VARCHAR(255) NULL
```

禁止添加：

```sql
UNIQUE(category_code)
```

---

## 5.3 brands

```text
brand_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY
brand_name VARCHAR(255) NOT NULL UNIQUE
```

---

## 5.4 products

```text
product_id BIGINT UNSIGNED PRIMARY KEY
category_id BIGINT UNSIGNED NOT NULL
```

没有：

```text
price
brand_id
```

---

## 5.5 product_brands

```text
product_id
brand_id

PRIMARY KEY(product_id, brand_id)
```

---

## 5.6 sessions

```text
session_id CHAR(36) PRIMARY KEY
start_time DATETIME(3)
end_time DATETIME(3)
event_count INT UNSIGNED
```

不存：

```text
user_id
```

---

## 5.7 behavior_events

```text
event_id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY
event_time DATETIME(3)
event_type VARCHAR(32)
user_id BIGINT UNSIGNED
session_id CHAR(36)
product_id BIGINT UNSIGNED
brand_id INT UNSIGNED
price DECIMAL(10,2)
source_event_hash BINARY(32) UNIQUE
```

---

# 6. Docker / MySQL

容器：

```text
ecommerce-mysql
```

端口：

```text
127.0.0.1:3307
```

数据库：

```text
ecommerce
```

项目使用 Docker volume 持久化数据库。

启动：

```bash
docker start ecommerce-mysql
```

检查：

```bash
docker ps
```

不要在没有备份/明确需要时执行：

```bash
docker compose down -v
```

因为 `-v` 会删除数据库卷。

---

# 7. SQL 文件

```text
sql/
├── 01_schema.sql
├── 02_constraints.sql
├── 03_transform_staging.sql
├── 04_transform_events.sql
├── 05_etl_control.sql
└── 06_views.sql
```

用途：

| 文件 | 作用 |
|---|---|
| 01_schema.sql | 建库、业务表、staging |
| 02_constraints.sql | 维度表 / 关联表外键 |
| 03_transform_staging.sql | staging → 维度表 |
| 04_transform_events.sql | staging → behavior_events |
| 05_etl_control.sql | ETL run / batch 控制 |
| 06_views.sql | 业务统计 View |

---

# 8. ETL 的最终结构

```text
2019-Nov.csv
     │
     ▼
pandas chunksize=100000
     │
     ▼
staging_events
     │
     ├── users
     ├── categories
     ├── brands
     ├── products
     ├── product_brands
     └── sessions
     │
     ▼
behavior_events
     │
     ▼
source_event_hash
     │
     ▼
重复事件跳过
```

---

# 9. ETL 实际开发过程

## 9.1 第一版测试

100,000 行测试：

```text
source rows: 100,000
loaded:       99,973
duplicates:       27
```

再次运行同一数据：

```text
新增：0
```

证明：

```text
source_event_hash + INSERT IGNORE
```

可以实现幂等。

---

## 9.2 两批测试

200,000 行：

```text
source:        200,000
staging:       200,000
events:        199,920
duplicates:         80
```

---

## 9.3 100 万行测试

完整前 100 万行实际运行：

```text
source:        1,000,000
staging:       1,000,000
events:          999,508
duplicates:          492
```

这里的 `492` 与之前独立扫描前 100 万行得到的重复数完全一致。

这是 ETL 正确性的关键验证。

---

# 10. ETL 断点恢复

开发过程中发现：

> “记录失败”不等于“可以恢复”。

第一版存在两个问题：

1. 重新运行会重复创建 batch。
2. 被中断的 batch 已存在 `RUNNING` 记录，再次插入会触发唯一键冲突。

具体错误：

```text
Duplicate entry '1-4'
for key
'etl_batches.uk_etl_batch_run_no'
```

修复后逻辑：

```text
读取最近一个 SUCCESS batch
        ↓
跳过已成功 batch
        ↓
复用失败/中断 batch 记录
        ↓
重新执行未完成 batch
```

验证结果：

```text
SUCCESS:
batch 1
batch 2
batch 3

中断：
batch 4

--resume

跳过 1
跳过 2
跳过 3
继续 4
```

断点恢复机制通过。

---

# 11. 全量 ETL 为什么暂时停止

实际运行到：

```text
batch 60
```

已成功加载：

```text
5,997,478
```

条事件。

Batch 61 过程中主动中断。

原因不是数据错误，而是当前 ETL 吞吐不足。

100 万行测试耗时约：

```text
188.5 秒
```

继续全量需要较长时间。

项目当前策略：

> 优先完成课程要求的完整应用系统、测试、文档和演示；全量 6750 万数据的吞吐优化作为后续工作。

因此当前数据库保留约 600 万真实事件，足够支撑前后端开发和演示。

---

# 12. 正式 ETL 当前状态

脚本：

```text
scripts/etl/run_etl.py
```

默认：

```text
chunksize = 100000
```

正常运行：

```bash
python scripts/etl/run_etl.py
```

恢复：

```bash
python scripts/etl/run_etl.py --resume
```

注意：

> 当前阶段不要为了“全量”再次长时间运行。没有性能优化前，全量导入不是课程交付的阻塞项。

---

# 13. FastAPI 后端

目录：

```text
backend/
└── app/
    ├── database.py
    ├── main.py
    ├── routers/
    └── services/
```

当前模块：

```text
dashboard
products
users
sessions
analytics
```

---

# 14. API

## Dashboard

```http
GET /api/dashboard/overview
```

## Product

```http
GET /api/products
GET /api/products/{product_id}
GET /api/products/{product_id}/statistics
```

## User

```http
GET /api/users/{user_id}/events
```

支持：

```text
page
page_size
event_type
```

## Session

```http
GET /api/sessions/{session_id}
```

## Analytics

```http
GET /api/analytics/top-products
GET /api/analytics/top-brands
GET /api/analytics/top-categories
GET /api/analytics/conversion
```

---

# 15. Conversion 业务口径修正

第一版：

```text
purchase events / cart events
```

出现超过 100% 的结果。

原因：

> 事件数量不是漏斗人数。

例如一个用户可以多次 purchase。

最终采用 Session 漏斗：

```text
view session
      ↓
cart session
      ↓
purchase session
```

指标：

```text
view_to_cart_rate
cart_to_purchase_rate
view_to_purchase_rate
```

计算对象是 Session，而不是事件次数。

---

# 16. 数据库 View

```text
v_product_statistics
v_brand_statistics
v_category_statistics
v_user_behavior_summary
```

用途：

```text
商品统计
品牌统计
类别统计
用户行为摘要
```

---

# 17. API 错误规范

统一结构：

```json
{
  "code": 404,
  "message": "Product not found",
  "data": null
}
```

参数校验：

```json
{
  "code": 422,
  "message": "Request validation failed",
  "data": []
}
```

服务异常：

```json
{
  "code": 500,
  "message": "Internal server error",
  "data": null
}
```

---

# 18. 自动化测试

测试目录：

```text
tests/
├── test_api.py
├── test_database.py
└── test_etl.py
```

pytest：

```text
8.4.2
```

最终基线：

```text
37 passed
```

组成：

```text
API       16
Database  16
ETL        5
----------------
Total     37
```

---

# 19. API 测试覆盖

包括：

```text
Root
Dashboard
Product list
Pagination validation
Product detail
Product 404
Product statistics
Product statistics 404
User events
Purchase filter
Top products
Top brands
Top categories
Conversion
Session detail
Session 404
```

---

# 20. 数据库测试覆盖

包括：

```text
source_event_hash 唯一性
产品类别完整性
产品-品牌关联完整性
品牌关联完整性
event_type 合法性
price 非负
View 存在
View 可查询
事件必填字段
price 范围
user_id
product_id
event_time 范围
```

---

# 21. ETL 测试覆盖

包括：

```text
ETL 控制表
batch 状态
成功批次统计
staging 状态
event hash 唯一性
```

---

# 22. 历史踩坑索引

| 问题 | 根因 | 修复 |
|---|---|---|
| `category_code` 唯一约束冲突 | 真实数据中一对多 | 删除 UNIQUE |
| 重复 ETL 产生重复事件 | 依赖自增 event_id | 增加 source hash |
| Session 跨批次统计错误 | 直接 INSERT | Session UPSERT |
| `etl_batches` 重试冲突 | 重试再次 INSERT | 复用已有 batch |
| Ctrl+C 后出现二次 traceback | DB 连接同时断开 | 中断处理增加保护 |
| pytest 误执行 ETL 原型 | 原型文件符合 pytest 发现规则 | 改名 `09_etl_prototype.py` |
| conversion >100% | 使用事件数计算漏斗 | 改为 Session 漏斗 |
| conversion SQL `Unknown column` | 外层错误引用子查询字段 | 修正 SQL |
| pytest 旧字段断言失败 | API 字段已经改口径 | 同步测试字段 |
| 包导入失败 | `app` 与 `backend.app` 路径不一致 | 统一使用 `backend.app` |

---

# 23. 当前演示基线

当前真实数据库：

```text
events       5,997,478
users          748,770
products       119,243
sessions     1,331,322
brands           3,241
categories         618
```

固定演示对象：

```text
user_id:
564068124
```

```text
product_id:
1000978
```

```text
session_id:
4488e77a-9901-4c4b-b162-47a224ceab51
```

```text
brand:
9 / samsung
```

```text
category:
2053013555631882655 / electronics.smartphone
```

详细记录：

```text
docs/demo_data.md
```

---

# 24. 启动项目

## MySQL

```bash
docker start ecommerce-mysql
```

## Conda

```bash
conda activate bigdata
```

## Backend

```bash
cd ~/ecommerce_project/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Test

另开终端：

```bash
cd ~/ecommerce_project
conda activate bigdata
python -m pytest -v
```

---

# 25. 当前项目目录

```text
ecommerce_project/
├── backend/
├── data/
│   ├── raw/
│   └── processed/
├── docs/
├── frontend/
├── scripts/
│   ├── analysis/
│   ├── etl/
│   └── validation/
├── sql/
├── tests/
└── docker-compose.yml
```

---

# 26. 尚未完成

当前代码基线不代表最终课程提交已经完成。

剩余重点：

```text
1. 前端 UI
2. DFD
3. 用例图
4. 数据字典
5. 正式 ER 图
6. 模块结构图
7. 正式测试用例表
8. 前后端联调
9. 最终演示流程
10. 课程报告
```

当前 `frontend/` 仍需要正式实现。

---

# 27. 最终验收标准

最终交付前至少应满足：

```text
MySQL 可启动
API 可启动
前端可启动
37 个现有自动化测试全部通过
正式测试用例完整
ER / DFD / 用例 / 数据字典齐全
报告完成
演示流程完整
```

最终回归：

```bash
python -m pytest -v
```

要求：

```text
全部 PASSED
```

---

# 28. 项目核心经验

本项目最重要的成果不是把 CSV 导入 MySQL，而是建立了一个可解释的工程闭环：

```text
真实数据
→ 发现依赖
→ 修正假设
→ 建模
→ ETL
→ 数据库约束
→ 业务 API
→ 自动化测试
→ 前端
→ 系统交付
```

数据库结构中的关键取舍都有数据依据，而不是根据“看起来应该这样”决定。

