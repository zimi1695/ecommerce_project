# 设计依据与开发过程

本文档记录项目的完整设计依据与开发过程，包括数据依赖验证、建模决策、ETL 演进与历史问题，可作为课程报告素材与设计回溯参考。交接须知见 [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md)。

## 1. 项目定位

本项目不是商城前台，而是面向电商运营分析的数据库应用系统。围绕用户行为事件建立数据库，提供数据总览、商品查询与统计、用户行为查询、Session 分析、商品 / 品牌 / 类别排行、浏览 → 加购 → 购买漏斗分析、数据库视图、ETL 加载与幂等控制、REST API 与自动化测试。

课程任务要求完成业务调查、系统分析与设计、数据库设计、建库与加载、应用开发、系统测试、文档和演示，本项目开发路径按这些交付物反向设计。

## 2. 开发路线

```text
选题 → 原始数据探索 → 数据依赖验证 → 数据库建模 → MySQL 建库
     → 小规模加载测试 → ETL 正式版 → 600 万级真实数据验证
     → FastAPI → 业务视图 → 自动化测试 → 前端与文档 → 最终联调
```

核心原则：**先用真实数据证明依赖关系，再决定表结构；先验证小批量，再扩大规模；每次修改都用自动化测试回归。**

## 3. 数据集概况

数据来源：Kaggle — eCommerce behavior data from multi category store（2019 年 11 月）。原始文件 `data/raw/2019-Nov.csv` 约 9.0 GB。

完整扫描结果：

| 指标 | 数量 |
|---|---:|
| 原始事件行 | 67,501,979 |
| 用户 | 3,696,117 |
| 商品 | 190,662 |
| category_id | 684 |
| 品牌 | 4,200 |
| Session | 13,776,050 |

事件类型分布：

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

时间范围 `2019-11-01 00:00:00 ~ 2019-11-30 23:59:59 UTC`，价格范围 `0.00 ~ 2574.07`。

## 4. 数据依赖验证

数据库设计前对全量数据做了完整依赖检查。每条建模决策都有扫描数据支撑，而不是根据"看起来应该这样"决定。

| # | 验证项 | 结论 | 数据依据 | 建模影响 |
|---|---|---|---|---|
| 4.1 | product_id → category_id | 稳定 | 冲突 0 | `products.category_id` 可建外键 |
| 4.2 | product_id → price | 不稳定 | 70,684 个商品存在多个价格 | price 放入 `behavior_events`，记录行为发生时价格，而非人为假设的单一商品价 |
| 4.3 | product_id → brand | 冲突 | 136 个商品有多个非空品牌（典型：lenovo/samsung、hasbro/nerf、bugati/bugatti、dirkje/dirkjebabywear、ikea/imperial） | 产品-品牌改用关联表 `product_brands`，按多对多如实建模，未做人工清洗 |
| 4.4 | category_id → category_code | 稳定 | 冲突 0 | `categories` 可同时保存两字段 |
| 4.5 | category_code → category_id | 不稳定 | 129 个非空 category_code 中 58 个对应多个 category_id | **禁止** `UNIQUE(category_code)`——这是项目早期出现过的实际错误 |
| 4.6 | user_session → user_id | 不稳定 | 591 个 Session ID 关联多个 user_id | `sessions` 不存 user_id，用户与 Session 的真实关系保留在事实表两个字段中 |
| 4.7 | 完全重复事件 | 存在 | 100,519 条完全重复记录 | 理论唯一事件 67,401,460 条，以 `source_event_hash BINARY(32) UNIQUE` 作为最终幂等约束 |

## 5. 数据库设计

核心业务表 7 张，ETL 控制表 3 张：

```text
users / categories / brands / products / product_brands / sessions / behavior_events
staging_events / etl_runs / etl_batches
```

| 表 | 结构要点 |
|---|---|
| users | `user_id BIGINT UNSIGNED PRIMARY KEY` |
| categories | `category_id` PK + `category_code VARCHAR(255) NULL`，**无 UNIQUE** |
| brands | `brand_id INT UNSIGNED AUTO_INCREMENT` PK，`brand_name VARCHAR(255) NOT NULL UNIQUE` |
| products | `product_id` PK + `category_id` 外键；**没有 price、没有 brand_id** |
| product_brands | 复合主键 `(product_id, brand_id)`，多对多桥表 |
| sessions | `session_id CHAR(36)` PK，`start_time / end_time DATETIME(3)`，`event_count INT UNSIGNED`；**不存 user_id** |
| behavior_events | `event_id` 自增 PK，`event_time / event_type / user_id / session_id / product_id / brand_id / price DECIMAL(10,2)`，`source_event_hash BINARY(32) UNIQUE` |

外键策略：维度表与桥表已建外键（products→categories、product_brands→products/brands）；事实表 `behavior_events` 暂未建全外键——当前 600 万行、未来可达 6750 万行，批量写入场景下过多外键影响吞吐，课程展示前可重新评估。

## 6. 运行环境：Docker / MySQL

| 项 | 值 |
|---|---|
| 容器名 | `ecommerce-mysql` |
| 端口映射 | `127.0.0.1:3307 → 3306` |
| 数据库 | `ecommerce` |
| 持久化 | Docker volume |

```bash
docker start ecommerce-mysql   # 启动
docker ps                      # 确认运行
```

**禁止在没有备份 / 明确需要时执行 `docker compose down -v`**，`-v` 会删除数据库卷。

## 7. SQL 脚本

按序号执行：

| 文件 | 作用 |
|---|---|
| `sql/01_schema.sql` | 建库、业务表、staging |
| `sql/02_constraints.sql` | 维度表 / 桥表外键 |
| `sql/03_transform_staging.sql` | staging → 维度表 |
| `sql/04_transform_events.sql` | staging → behavior_events |
| `sql/05_etl_control.sql` | ETL run / batch 控制表 |
| `sql/06_views.sql` | 业务统计视图 |

## 8. ETL 设计

### 8.1 整体结构

```text
2019-Nov.csv
     │ pandas chunksize=100000
     ▼
staging_events
     ├── users / categories / brands / products / product_brands
     └── sessions（UPSERT，Session 可能跨 batch）
     ▼
behavior_events
     ▼ source_event_hash 唯一约束 + INSERT IGNORE
重复事件跳过
```

`source_event_hash` 由源事件主要原始字段经 SHA-256 生成：同一源事件 → 相同哈希 → 唯一约束冲突 → INSERT IGNORE 跳过。Session 用 `ON DUPLICATE KEY UPDATE` UPSERT，必须保留——一个 Session 可能跨 batch。

### 8.2 幂等性验证

| 批量 | source | staging | events | duplicates |
|---|---:|---:|---:|---:|
| 10 万行 | 100,000 | — | 99,973 | 27 |
| 10 万行重跑 | 同批 | — | **新增 0** | — |
| 20 万行 | 200,000 | 200,000 | 199,920 | 80 |
| 100 万行 | 1,000,000 | 1,000,000 | 999,508 | 492 |

100 万行的 `492` 与独立扫描前 100 万行得到的重复数完全一致，是 ETL 正确性的关键验证。

### 8.3 断点恢复

开发中发现"记录失败"不等于"可以恢复"。第一版两个问题：重新运行会重复创建 batch；被中断的 batch 已有 `RUNNING` 记录，再次插入触发唯一键冲突（`Duplicate entry '1-4' for key 'etl_batches.uk_etl_batch_run_no'`）。

修复后逻辑：读取最近一个 SUCCESS batch → 跳过已成功 batch → 复用失败 / 中断的 batch 记录 → 重新执行未完成 batch。

验证结果：batch 1-3 SUCCESS、batch 4 中断，`--resume` 后跳过 1、2、3，继续 4，断点恢复机制通过。

### 8.4 全量 ETL 暂停原因

实际运行到 batch 60，已成功加载 5,997,478 条事件，batch 61 过程中主动中断。原因不是数据错误，而是吞吐不足：100 万行测试耗时约 188.5 秒，继续全量需要很长时间。当前策略是优先完成课程要求的完整应用系统、测试、文档和演示，全量 6750 万数据的吞吐优化作为后续工作。

### 8.5 当前状态

脚本 `scripts/etl/run_etl.py`，默认 chunksize=100000：

```bash
python scripts/etl/run_etl.py            # 正常运行
python scripts/etl/run_etl.py --resume   # 断点恢复
```

当前阶段不要为了"全量"再次长时间运行；没有性能优化前，全量导入不是课程交付的阻塞项。

## 9. FastAPI 后端

```text
backend/app/
├── database.py
├── main.py
├── routers/    # dashboard / products / users / sessions / analytics
└── services/
```

API 清单：

| 模块 | 端点 |
|---|---|
| Dashboard | `GET /api/dashboard/overview` |
| 商品 | `GET /api/products`、`GET /api/products/{product_id}`、`GET /api/products/{product_id}/statistics` |
| 用户 | `GET /api/users/{user_id}/events`（支持 `page` / `page_size` / `event_type`） |
| Session | `GET /api/sessions/{session_id}` |
| 分析 | `GET /api/analytics/top-products` / `top-brands` / `top-categories` / `conversion` |

## 10. 转化率口径修正

第一版用 `purchase events / cart events`，结果超过 100%——事件数量不是漏斗人数，一个用户可以多次 purchase。最终采用 **Session 漏斗**：以同一 Session 内是否出现对应事件计算 `view_to_cart_rate`、`cart_to_purchase_rate`、`view_to_purchase_rate`。计算对象是 Session，不是事件次数，不要改回旧口径。

## 11. 业务视图

| 视图 | 用途 |
|---|---|
| `v_product_statistics` | 商品统计 |
| `v_brand_statistics` | 品牌统计 |
| `v_category_statistics` | 类别统计 |
| `v_user_behavior_summary` | 用户行为摘要 |

定义见 `sql/06_views.sql`，是课程报告中"视图"部分的重要实物。

## 12. API 错误规范

统一结构，新接口不要另起炉灶：

```json
{ "code": 404, "message": "Product not found", "data": null }
```

```json
{ "code": 422, "message": "Request validation failed", "data": [] }
```

```json
{ "code": 500, "message": "Internal server error", "data": null }
```

## 13. 自动化测试

pytest 8.4.2，最终基线 **37 passed** = API 16 + Database 16 + ETL 5。

API 覆盖：Root、Dashboard、商品列表、分页校验、商品详情、商品 404、商品统计、商品统计 404、用户行为、购买筛选、热门商品 / 品牌 / 类别、转化分析、Session 详情、Session 404。

数据库覆盖：`source_event_hash` 唯一性、产品类别完整性、产品-品牌关联完整性、品牌关联完整性、`event_type` 合法性、price 非负、视图存在、视图可查询、事件必填字段、price 范围、user_id / product_id / event_time 范围。

ETL 覆盖：控制表、batch 状态、成功批次统计、staging 状态、event hash 唯一性。

## 14. 历史问题索引

| 问题 | 根因 | 修复 |
|---|---|---|
| `category_code` 唯一约束冲突 | 真实数据中一对多 | 删除 UNIQUE |
| 重复 ETL 产生重复事件 | 依赖自增 event_id | 增加 source hash |
| Session 跨批次统计错误 | 直接 INSERT | Session UPSERT |
| `etl_batches` 重试冲突 | 重试再次 INSERT | 复用已有 batch |
| Ctrl+C 后二次 traceback | DB 连接同时断开 | 中断处理增加保护 |
| pytest 误执行 ETL 原型 | 原型文件符合 pytest 发现规则 | 改名 `09_etl_prototype.py` |
| conversion >100% | 用事件数计算漏斗 | 改为 Session 漏斗 |
| conversion SQL `Unknown column` | 外层引用子查询字段 | 修正 SQL |
| pytest 旧字段断言失败 | API 字段已改口径 | 同步测试字段 |
| 包导入失败 | `app` 与 `backend.app` 路径不一致 | 统一使用 `backend.app` |

## 15. 当前演示基线

| 表 | 行数 |
|---|---:|
| behavior_events | 5,997,478 |
| users | 748,770 |
| products | 119,243 |
| sessions | 1,331,322 |
| brands | 3,241 |
| categories | 618 |

固定演示对象（详见 [demo_data.md](demo_data.md)）：user `564068124`、product `1000978`、session `4488e77a-9901-4c4b-b162-47a224ceab51`、brand `9 / samsung`、category `2053013555631882655 / electronics.smartphone`。

## 16. 启动项目

```bash
# MySQL
docker start ecommerce-mysql

# 后端（第一终端）
conda activate bigdata
cd ~/ecommerce_project/backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 测试（第二终端）
cd ~/ecommerce_project
conda activate bigdata
python -m pytest -v
```

## 17. 目录结构

```text
ecommerce_project/
├── backend/           # FastAPI 后端
├── data/
│   ├── raw/           # 原始数据（不入库，见 Release）
│   └── processed/     # 可再生的中间产物
├── docs/              # 交接手册、设计依据、演示基线
├── frontend/          # 待开发
├── scripts/
│   ├── analysis/      # 数据探索与依赖验证
│   ├── etl/           # 正式 ETL
│   └── validation/    # 历史 / 实验脚本
├── sql/               # 建模到视图全流程脚本
├── tests/             # pytest 测试
└── docker-compose.yml
```

## 18. 待完成事项

前端 UI、DFD、用例图、数据字典、正式 ER 图、模块结构图、正式测试用例表、前后端联调、最终演示流程、课程报告。当前 `frontend/` 尚未正式实现，是最大代码缺口。

## 19. 验收标准

最终交付前至少满足：MySQL / API / 前端均可启动，37 个测试全部 PASSED，正式测试用例完整，ER / DFD / 用例 / 数据字典齐全，报告与演示流程完成。最终回归执行 `python -m pytest -v`，要求全部通过。

## 20. 核心经验

本项目最重要的成果不是把 CSV 导入 MySQL，而是建立了一个可解释的工程闭环：

```text
真实数据 → 发现依赖 → 修正假设 → 建模 → ETL → 数据库约束
         → 业务 API → 自动化测试 → 前端 → 系统交付
```

数据库结构中的关键取舍都有数据依据，而不是根据"看起来应该这样"决定。
