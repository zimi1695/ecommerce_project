# 项目交接文档

> 项目：基于 MySQL 的多品类电商用户行为分析与管理系统  
> 工作目录：`~/ecommerce_project`  
> Python 环境：`bigdata`  
> 数据库：Docker MySQL 8.0  
> 文档用途：新成员接手、开发协作、故障恢复、最终提交

---

# 1. 当前项目一句话状态

项目已经完成：

- 数据探索
- 数据建模
- MySQL 数据库
- ETL
- ETL 控制与断点恢复
- FastAPI 后端
- 业务 View
- API 自动化测试
- 数据库自动化测试
- ETL 自动化测试
- 固定演示数据

当前真实数据库中约有：

```text
behavior_events = 5,997,478
```

当前完整自动化测试：

```text
37 passed
```

前端尚未正式完成。

---

# 2. 接手第一件事

不要一上来修改数据库。

先执行：

```bash
cd ~/ecommerce_project
conda activate bigdata
docker start ecommerce-mysql
```

确认：

```bash
docker ps
```

然后：

```bash
python -m pytest -v
```

基准应该是：

```text
37 passed
```

如果不是 37 passed，先查问题，不要继续加功能。

---

# 3. 当前数据库基线

当前数据库：

```text
ecommerce
```

容器：

```text
ecommerce-mysql
```

映射：

```text
127.0.0.1:3307 -> MySQL 3306
```

连接：

```text
host=127.0.0.1
port=3307
database=ecommerce
user=ecommerce
```

---

# 4. 当前数据规模

当前正式数据库：

```text
behavior_events    5,997,478
users                748,770
products             119,243
sessions           1,331,322
brands                 3,241
categories               618
```

这些数据来自原始 2019-Nov 数据的前 60 个完整 ETL batch。

每 batch：

```text
100,000 source rows
```

当前：

```text
batch 1 ~ 60 = SUCCESS
batch 61 = 中断
```

因此数据库中可用于前后端演示和开发的事实数据约 600 万条。

---

# 5. 原始数据在哪里

原始文件：

```text
data/raw/2019-Nov.csv
```

压缩文件：

```text
data/raw/2019-Nov.csv.zip
```

原始 CSV：

```text
约 9 GB
约 6750 万行
```

不要删除。

---

# 6. 当前开发策略：暂时不要全量 ETL

项目曾经实际运行全量 ETL，但发现当前实现速度较慢。

已实际处理：

```text
约 600 万事件
```

目前决定：

> 暂时停止全量导入，把开发重点转到业务逻辑、前端、测试、文档和课程交付。

以后需要性能优化时再处理。

禁止新成员接手后未经讨论直接执行：

```bash
python scripts/etl/run_etl.py
```

因为这会继续处理大量数据。

---

# 7. ETL 文件

正式脚本：

```text
scripts/etl/run_etl.py
```

测试/历史脚本：

```text
scripts/validation/
```

重要：

```text
09_etl_prototype.py
```

是历史原型，不是正式 ETL。

不要把它当正式数据管线。

---

# 8. ETL 如何工作

核心：

```text
2019-Nov.csv
      ↓
pandas chunksize=100000
      ↓
staging_events
      ↓
users/categories/brands/products
      ↓
product_brands
      ↓
sessions UPSERT
      ↓
behavior_events
      ↓
source_event_hash 去重
```

Session 的关键：

```sql
ON DUPLICATE KEY UPDATE
```

必须保留，因为一个 Session 可能跨 batch。

---

# 9. 为什么 source_event_hash 很重要

事实表：

```text
behavior_events
```

包含：

```text
source_event_hash BINARY(32) UNIQUE
```

生成方式：

```text
SHA-256
```

输入包括源事件的主要原始字段。

作用：

```text
同一源事件
    ↓
相同 hash
    ↓
UNIQUE 冲突
    ↓
INSERT IGNORE
    ↓
不重复插入
```

任何人修改 ETL 时都不能轻易删除这个机制。

---

# 10. 数据建模的关键决定

不要随意修改以下规则。

## 10.1 category_code 不唯一

正确：

```text
categories(
    category_id PK,
    category_code
)
```

错误：

```sql
UNIQUE(category_code)
```

理由：

完整数据扫描已经确认：

```text
58 个 category_code
```

对应多个 category_id。

---

## 10.2 products 没有 price

正确：

```text
products(
    product_id,
    category_id
)
```

price 在：

```text
behavior_events
```

因为同一个产品存在多种价格。

---

## 10.3 products 没有 brand_id

因为 136 个产品有多个非空品牌。

使用：

```text
product_brands
```

保存产品-品牌关联。

---

## 10.4 sessions 没有 user_id

591 个 Session ID 对应多个 user_id。

用户和 Session 的关系由：

```text
behavior_events.user_id
behavior_events.session_id
```

体现。

---

# 11. SQL 文件顺序

初始化/结构：

```text
sql/01_schema.sql
```

维度/桥表外键：

```text
sql/02_constraints.sql
```

Staging -> dimension：

```text
sql/03_transform_staging.sql
```

Staging -> behavior：

```text
sql/04_transform_events.sql
```

ETL 控制表：

```text
sql/05_etl_control.sql
```

业务 View：

```text
sql/06_views.sql
```

---

# 12. 外键策略

当前：

```text
products -> categories
product_brands -> products
product_brands -> brands
```

事实表 `behavior_events` 暂时没有全部建立外键。

原因：

```text
behavior_events ≈ 600万+ 当前数据
```

且未来可达：

```text
6750 万
```

大量批量写入时，过多 FK 会影响吞吐。

课程展示前可重新评估是否添加事实表外键。

---

# 13. 后端启动

第一终端：

```bash
cd ~/ecommerce_project/backend
conda activate bigdata
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

不要关闭。

第二终端做测试。

---

# 14. 后端当前目录

```text
backend/app/
├── database.py
├── main.py
├── routers/
└── services/
```

当前 Router：

```text
dashboard.py
products.py
users.py
analytics.py
sessions.py
```

---

# 15. API 当前清单

## Dashboard

```http
GET /api/dashboard/overview
```

## 商品

```http
GET /api/products
GET /api/products/{product_id}
GET /api/products/{product_id}/statistics
```

## 用户

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

# 16. Conversion 特别注意

不要改回：

```text
purchase events / cart events
```

这种口径。

它会出现超过 100% 的结果。

当前业务定义是 Session 漏斗：

```text
view session
↓
cart session
↓
purchase session
```

并以同一 Session 内是否出现对应事件来计算。

---

# 17. API 错误格式

当前已统一：

404：

```json
{
  "code": 404,
  "message": "Product not found",
  "data": null
}
```

422：

```json
{
  "code": 422,
  "message": "Request validation failed",
  "data": [...]
}
```

500：

```json
{
  "code": 500,
  "message": "Internal server error",
  "data": null
}
```

不要新写一个接口却返回完全不同的错误结构。

---

# 18. View

当前 View：

```text
v_product_statistics
v_brand_statistics
v_category_statistics
v_user_behavior_summary
```

SQL：

```text
sql/06_views.sql
```

这些 View 是数据库课程报告中“视图”部分的重要实物。

---

# 19. 测试目录

```text
tests/
├── test_api.py
├── test_database.py
└── test_etl.py
```

执行全部：

```bash
python -m pytest -v
```

基准：

```text
37 passed
```

---

# 20. 为什么 pytest 曾经出现 1 error

旧文件：

```text
scripts/validation/09_etl_test.py
```

里面包含顶层执行代码。

pytest 会自动发现它并直接运行。

结果造成：

```text
Field 'source_event_hash' doesn't have a default value
```

解决：

```text
09_etl_test.py
↓
09_etl_prototype.py
```

以后不要把“可执行 ETL 实验脚本”命名成：

```text
test_*.py
*_test.py
```

除非它真的是 pytest 测试文件。

---

# 21. 固定演示数据

统一使用：

```text
user:
564068124
```

```text
product:
1000978
```

```text
session:
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

前端和测试不要每个人自己随便找一组 ID。

---

# 22. 前端当前状态

当前：

```text
frontend/
```

为空/尚未正式实现。

这是当前最大的代码缺口。

建议至少做：

```text
Dashboard
Products
Product Detail
User Events
Session Detail
Analytics
```

---

# 23. 设计文档当前状态

目前尚未完整建立：

```text
DFD
Use Case
Data Dictionary
ER Diagram
Module Structure Diagram
```

这些是课程实践明确要求的设计材料。

建议存到：

```text
docs/
```

例如：

```text
docs/
├── problem_definition.md
├── requirements.md
├── use_case.md
├── dfd.md
├── data_dictionary.md
├── er_design.md
├── module_design.md
├── test_cases.md
└── demo_data.md
```

---

# 24. 测试用例文档

已有 pytest，不等于课程要求的正式“测试用例文档”已经完成。

必须补：

```text
TC-001
TC-002
...
```

字段建议：

```text
编号
测试目标
前置条件
测试输入
操作步骤
预期结果
实际结果
是否通过
```

覆盖：

```text
正常功能
异常输入
边界值
数据库完整性
ETL 幂等
SQL 注入/安全输入
```

---

# 25. 当前目录里哪些文件可以动

可以正常开发：

```text
backend/
frontend/
tests/
docs/
sql/
scripts/etl/
```

谨慎修改：

```text
sql/01_schema.sql
```

因为它定义数据库模型。

---

# 26. 哪些东西不要随便删

不要删除：

```text
data/raw/2019-Nov.csv
data/raw/2019-Nov.csv.zip
```

不要删除数据库 Docker volume。

不要执行：

```bash
docker compose down -v
```

除非明确决定重建整个数据库。

---

# 27. 如果数据库容器没启动

执行：

```bash
docker start ecommerce-mysql
```

然后：

```bash
docker ps
```

---

# 28. 如果 FastAPI 没启动

执行：

```bash
cd ~/ecommerce_project/backend
conda activate bigdata
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

# 29. 如果 pytest 失败

第一步不要修改测试。

先执行：

```bash
python -m pytest -v
```

确认：

```text
哪个测试失败
```

然后：

```bash
git diff
```

如果项目没有 Git，再人工检查最近修改的文件。

优先判断：

```text
数据库结构问题
API 字段变化
SQL 口径变化
导入路径变化
测试预期没同步
```

---

# 30. 如果需要继续 ETL

先检查：

```bash
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
SELECT
    run_id,
    status,
    total_source_rows,
    total_events_loaded,
    total_duplicates
FROM etl_runs
ORDER BY run_id DESC
LIMIT 3;
"
```

再检查：

```bash
docker exec ecommerce-mysql mysql -uecommerce -pecommerce_2026 ecommerce -e "
SELECT
    batch_no,
    status,
    source_rows,
    events_loaded,
    duplicates_skipped
FROM etl_batches
ORDER BY batch_id DESC
LIMIT 10;
"
```

只有确定要继续时才：

```bash
python scripts/etl/run_etl.py --resume
```

---

# 31. 当前项目协作建议

## 成员 A：前端

负责：

```text
frontend/
```

不要等待全量 ETL。

当前 600 万真实数据已经足够完成 UI 联调。

---

## 成员 B：系统分析

负责：

```text
DFD
用例图
数据字典
ER 图
模块结构图
```

内容应该以当前实际数据库设计为准。

特别注意：

```text
products - brands
```

是多对多。

```text
sessions - users
```

不要在 ER 图中画成简单的一对一。

---

## 成员 C：测试

负责：

```text
docs/test_cases.md
```

以及：

```text
pytest
```

测试结果截图。

---

## 成员 D：文档

负责：

```text
项目报告
README
开发过程
问题与讨论
总结
```

---

# 32. 最终提交前检查清单

数据库：

```text
[ ] MySQL 可启动
[ ] 表结构正确
[ ] 外键正确
[ ] View 正常
[ ] 当前数据可查询
```

后端：

```text
[ ] FastAPI 可启动
[ ] Dashboard
[ ] Products
[ ] Users
[ ] Sessions
[ ] Analytics
```

前端：

```text
[ ] Dashboard
[ ] 商品
[ ] 用户
[ ] Session
[ ] 分析
```

测试：

```text
[ ] API tests
[ ] Database tests
[ ] ETL tests
[ ] 正式测试用例表
[ ] 全部通过
```

文档：

```text
[ ] 问题定义
[ ] 需求分析
[ ] DFD
[ ] 用例图
[ ] 数据字典
[ ] ER 图
[ ] 关系模型
[ ] View
[ ] 模块结构
[ ] 实现
[ ] 测试
[ ] 问题与讨论
[ ] 总结
```

演示：

```text
[ ] Dashboard
[ ] 商品查询
[ ] 用户行为
[ ] Session
[ ] Analytics
[ ] 测试结果
```

---

# 33. 交接后的推荐开发顺序

不要继续扩充 ETL。

推荐顺序：

```text
1. 前端 UI
2. 系统分析文档
3. 正式测试用例
4. 前后端联调
5. 最终数据库检查
6. 最终测试
7. 报告
8. 演示
```

---

# 34. 关键项目原则

接手后请始终遵守：

1. **不要为了“看起来规范”而违背已经通过完整数据扫描验证的事实。**
2. **不要把 category_code 改成 UNIQUE。**
3. **不要把 price 再放回 products。**
4. **不要把 product 直接绑定一个 brand_id。**
5. **不要给 session 强行绑定一个 user_id。**
6. **不要删除 source_event_hash。**
7. **不要让 pytest 运行实验脚本。**
8. **不要因为课程项目而贸然重跑 6750 万全量 ETL。**
9. **后端 SQL 的业务口径发生变化时，必须同步修改测试。**
10. **数据库结构变化时，必须同步检查 ER 图、关系模型、View、API 和测试。**

---

# 35. 当前最重要的下一步

**前端直接开始开发。**

后端已经拥有稳定的业务 API，数据库也有约 600 万条真实数据，足够完成界面联调。

同时其他成员并行完成：

```text
DFD
Use Case
Data Dictionary
ER
Test Cases
Report
```

当所有模块完成后，最终再执行一次：

```bash
python -m pytest -v
```

并形成最终交付基线。
