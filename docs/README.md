# 设计依据与开发过程

记录建模决策的数据依据、ETL 迭代过程和踩过的坑。项目用法见根目录 [README.md](../README.md)，交接须知见 [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md)。

## 1. 开发顺序

```text
选题 → 数据探索 → 依赖验证 → 建模 → 建库 → 小批量加载测试
     → ETL 正式版 → 600 万级验证 → FastAPI → 视图 → 测试
     → 前端（已实现，Mock 独立演示；真实接口联调待完成）
```

三条规矩：

- 表结构跟着依赖验证结果走，不凭字段名直觉
- 小批量跑通再放大：10 万 → 20 万 → 100 万 → 600 万
- 后端改动要过完 37 个测试才算完；仅前端变更按前端检查与测试验收，详见 [前端交接](FRONTEND_HANDOVER.md)

## 2. 数据集

Kaggle — eCommerce behavior data from multi category store，2019 年 11 月整月，原始 CSV 约 9.0 GB。

全量扫描结果：

| 指标 | 数量 |
|---|---:|
| 原始事件行 | 67,501,979 |
| 用户 | 3,696,117 |
| 商品 | 190,662 |
| category_id | 684 |
| 品牌 | 4,200 |
| Session | 13,776,050 |
| 完全重复事件 | 100,519 |

事件分布：view 63,556,110 / cart 3,028,930 / purchase 916,939。

缺失值：category_code 21,898,171（32.4%）、brand 9,224,078（13.7%）、user_session 10 条，其余字段无缺失。这两个字段的缺失比例决定了建表时必须允许 NULL。

时间范围 2019-11-01 ~ 2019-11-30 UTC，价格 0.00 ~ 2574.07。

## 3. 依赖验证

建表前对全量数据跑了 7 项函数依赖检查。

### 3.1 product_id → category_id

冲突 0。`products.category_id` 建外键。

### 3.2 product_id → price

70,684 个商品在数据里出现过多个价格。price 放进 `behavior_events`，记行为发生时的价格。按商品建价格字段会丢掉这 7 万个商品的变动事实。

### 3.3 product_id → brand

136 个商品有多个非空品牌：

```text
lenovo / samsung      hasbro / nerf
bugati / bugatti      dirkje / dirkjebabywear
ikea / imperial
```

没做清洗。哪些是拼写错误、哪些是真实多品牌，从数据里判断不了，强行清洗等于替数据做主。按多对多建 `product_brands` 桥表。

### 3.4 category_id → category_code

冲突 0。两字段同存 `categories`。

### 3.5 category_code → category_id

129 个非空 category_code 里 58 个对应多个 category_id。category_code 不能加 UNIQUE。早期版本加过，导入真实数据时直接报唯一键冲突，删掉了。

### 3.6 user_session → user_id

591 个 Session ID 关联多个 user_id。`sessions` 不存 user_id，用户和 Session 的关系留在 `behavior_events.user_id` 和 `session_id` 两个字段里。

### 3.7 重复事件

完全重复 100,519 条，去重后理论唯一事件 67,401,460。`behavior_events` 加 `source_event_hash BINARY(32) UNIQUE`，对源事件主要原始字段做 SHA-256。

### 汇总

| 验证项 | 结果 | 建模影响 |
|---|---|---|
| product_id → category_id | 冲突 0 | products.category_id 外键 |
| product_id → price | 70,684 商品多价格 | price 入事实表 |
| product_id → brand | 136 商品多品牌 | product_brands 桥表 |
| category_id → category_code | 冲突 0 | categories 同存两字段 |
| category_code → category_id | 58 code 多 id | 禁止 UNIQUE(category_code) |
| user_session → user_id | 591 session 多用户 | sessions 不存 user_id |
| 完全重复事件 | 100,519 条 | source_event_hash 唯一约束 |

## 4. 建模决策

业务表 7 张：users / categories / brands / products / product_brands / sessions / behavior_events。ETL 控制表 3 张：staging_events / etl_runs / etl_batches。建表细节见 `sql/01_schema.sql`、`sql/02_constraints.sql`，取舍点如下：

| 决策 | 依据 |
|---|---|
| products 无 price | §3.2，价格属于行为时点 |
| products 无 brand_id | §3.3，多对多走桥表 |
| categories 无 UNIQUE(code) | §3.5 |
| sessions 无 user_id | §3.6 |
| behavior_events 加 hash 唯一约束 | §3.7 |
| 事实表暂不全建外键 | 当前 600 万行、目标 6750 万，批量写入吞吐优先；展示前再评估 |

## 5. ETL

### 5.1 流程

```text
2019-Nov.csv
     │  pandas chunksize=100000，流式读
     ▼
staging_events
     ├── users / categories / brands / products / product_brands
     └── sessions（ON DUPLICATE KEY UPDATE）
     ▼
behavior_events
     ▼  source_event_hash + INSERT IGNORE
重复事件跳过，计数上报
```

staging 的作用是把转换逻辑集中到 `sql/03_transform_staging.sql` 和 `sql/04_transform_events.sql`，和原始数据隔离，出问题整层重放。

Session 必须 UPSERT：一个 Session 跨 batch 出现很正常（用户长时间浏览），直接 INSERT 会把跨批次的统计做错。

### 5.2 幂等验证

| 批量 | source | staging | events | duplicates |
|---|---:|---:|---:|---:|
| 10 万行 | 100,000 | — | 99,973 | 27 |
| 同批重跑 | — | — | 新增 0 | — |
| 20 万行 | 200,000 | 200,000 | 199,920 | 80 |
| 100 万行 | 1,000,000 | 1,000,000 | 999,508 | 492 |

100 万行跑出的 492 条重复，和独立扫描前 100 万行的重复数一致，两条独立路径对上了。同批重跑新增 0，幂等成立。

### 5.3 resume

第一版 resume 跑不通，两个问题：

1. 重跑会重复建 batch 记录
2. 中断的 batch 已经有 RUNNING 记录，再插入撞 `uk_etl_batch_run_no`：

```text
Duplicate entry '1-4' for key 'etl_batches.uk_etl_batch_run_no'
```

修复后：读最近一个 SUCCESS batch → 跳过已成功 → 复用失败/中断的 batch 记录 → 续跑未完成的。

验证：batch 1-3 SUCCESS、4 中断，`--resume` 后跳 1/2/3、续 4。

### 5.4 停在 600 万

跑到 batch 60（5,997,478 条），batch 61 手动停的。100 万行 188.5 秒，全量 6750 万要几个小时。600 万够前后端联调和演示用，先做交付，吞吐优化以后再说。

脚本 `scripts/etl/run_etl.py`：

```bash
python scripts/etl/run_etl.py            # 正常跑
python scripts/etl/run_etl.py --resume   # 断点续跑
```

现阶段不要为了全量去长时间跑。

## 6. conversion 口径

第一版用 `purchase events / cart events`，结果超过 100%。事件数没有包含关系：一个用户可以多次购买，购买的商品也未必是这次加购的。

改成 Session 口径：同一 Session 内出现过对应事件就计数。

```text
view session → cart session → purchase session
```

指标：view_to_cart_rate、cart_to_purchase_rate、view_to_purchase_rate。别改回事件口径。

## 7. 视图

`v_product_statistics` / `v_brand_statistics` / `v_category_statistics` / `v_user_behavior_summary`，定义在 `sql/06_views.sql`。统计口径固化在数据库层，API 查视图，避免各接口自己算一套。

## 8. 测试

37 = API 16 + 数据库 16 + ETL 5，pytest 8.4.2。

踩过的坑都补成了用例：hash 唯一性、外键完整性（产品-类别、产品-品牌）、event_type 合法性、price 非负与范围、四个视图存在且可查、必填字段、时间范围；ETL 控制表、batch 状态、成功批次统计、staging 状态。

依赖验证的结论靠这批用例守着，防止后续改动悄悄破坏约束。

## 9. 踩坑记录

| 问题 | 发现 | 根因 | 修复 |
|---|---|---|---|
| category_code 唯一约束冲突 | 导入报错 | 真实数据一对多（§3.5） | 删 UNIQUE |
| 重复 ETL 产生重复事件 | 行数对不上 | 幂等靠自增 event_id，重跑必重 | 加 source_event_hash |
| Session 跨批次统计错误 | event_count 和明细对不上 | 跨 batch 直接 INSERT | Session UPSERT |
| etl_batches 重试冲突 | resume 报 Duplicate entry | 重试再 INSERT 已有记录 | 复用 batch 记录 |
| Ctrl+C 后二次 traceback | 中断时观察 | 中断处理里 DB 连接同时断 | 中断处理加保护 |
| pytest 误执行 ETL 原型 | 测试环境意外写库 | 文件名命中 pytest 发现规则 | 改名 09_etl_prototype.py；实验脚本禁用 test_* 命名 |
| conversion >100% | 指标明显不对 | 事件数当漏斗人数（§6） | 改 Session 口径 |
| conversion SQL Unknown column | 接口报错 | 外层引用子查询字段 | 修 SQL |
| pytest 旧字段断言失败 | 回归挂了 | API 改口径，测试没跟 | 同步测试；口径变更必须带测试 |
| 包导入失败 | 启动 ImportError | app 与 backend.app 混用 | 统一 backend.app |

## 10. 当前数据

| 表 | 行数 |
|---|---:|
| behavior_events | 5,997,478 |
| users | 748,770 |
| sessions | 1,331,322 |
| products | 119,243 |
| brands | 3,241 |
| categories | 618 |

固定演示对象：user `564068124`、product `1000978`、session `4488e77a-9901-4c4b-b162-47a224ceab51`、brand `9/samsung`、category `2053013555631882655/electronics.smartphone`，详见 [demo_data.md](demo_data.md)。

## 11. 前端与剩余交付

前端 UI 与 Mock 演示流程已实现，包含总览、商品、用户行为、Session、分析页面，见 [前端交接](FRONTEND_HANDOVER.md)。

剩余：DFD、用例图、数据字典、正式 ER 图、模块结构图、系统正式测试用例表、真实前后端联调、真实数据演示流程与课程报告。本文中的数据库规模及 37 个后端测试结果为历史开发记录，不代表前端交付时重新验证。
