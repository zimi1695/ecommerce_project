# 设计依据与开发过程

本文档记录关键设计决策的数据依据、ETL 演进过程与历史问题，作为课程报告素材与设计回溯参考。交接须知见 [PROJECT_HANDOVER.md](PROJECT_HANDOVER.md)。

## 1. 开发路线

选题 → 原始数据探索 → 数据依赖验证 → 数据库建模 → MySQL 建库 → 小规模加载测试 → ETL 正式版 → 600 万级真实数据验证 → FastAPI → 业务视图 → 自动化测试 →（待做）前端与文档 → 最终联调。

核心原则：**先用真实数据证明依赖关系，再决定表结构；先验证小批量，再扩大规模；每次修改都用自动化测试回归。**

## 2. 数据集概况

Kaggle — eCommerce behavior data from multi category store（2019 年 11 月）。

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

缺失值：category_code 21,898,171、brand 9,224,078、user_session 10，其余为 0。时间范围 2019-11-01 至 2019-11-30（UTC），价格 0.00 ~ 2574.07。

## 3. 数据依赖验证结论

建模前对全量数据做了依赖检查，每条结论都有扫描数据支撑：

| 验证项 | 结论 | 建模影响 |
|---|---|---|
| product_id → category_id | 稳定（冲突 0） | `products.category_id` 可建外键 |
| product_id → price | 不稳定（70,684 个商品多价格） | price 放入 `behavior_events`，记录行为发生时价格 |
| product_id → brand | 冲突（136 个商品多个非空品牌，如 lenovo/samsung、hasbro/nerf） | 引入桥表 `product_brands`，多对多 |
| category_id → category_code | 稳定（冲突 0） | 两字段可同存于 `categories` |
| category_code → category_id | 不稳定（58 个 code 对应多个 id） | **禁止** `UNIQUE(category_code)` |
| user_session → user_id | 不稳定（591 个 Session 关联多个用户） | `sessions` 不存 user_id，关系保留在事实表 |

未对品牌冲突做人工清洗，按多对多如实建模。

## 4. 数据库设计

业务表：`users`、`categories`、`brands`、`products`、`product_brands`、`sessions`、`behavior_events`；ETL 控制表：`staging_events`、`etl_runs`、`etl_batches`。

| 表 | 结构要点 |
|---|---|
| users | user_id PK |
| categories | category_id PK，category_code 可空，无 UNIQUE |
| brands | brand_id 自增 PK，brand_name UNIQUE |
| products | product_id PK，category_id 外键；**无 price、无 brand_id** |
| product_brands | 复合主键 (product_id, brand_id) |
| sessions | session_id PK，start_time / end_time / event_count；**无 user_id** |
| behavior_events | event_id 自增 PK，event_time / event_type / user_id / session_id / product_id / brand_id / price，`source_event_hash BINARY(32) UNIQUE` |

SQL 脚本按序号执行：01 建库建表 → 02 外键 → 03 staging 转维度 → 04 staging 转事实 → 05 ETL 控制 → 06 业务视图。

## 5. ETL 设计与演进

### 5.1 结构

```text
2019-Nov.csv → pandas 分块(10万行) → staging_events
    → users / categories / brands / products / product_brands / sessions(UPSERT)
    → behavior_events（source_event_hash 去重，重复跳过）
```

Session 用 `ON DUPLICATE KEY UPDATE` UPSERT，因为一个 Session 可能跨 batch。

### 5.2 幂等性验证

- 10 万行：加载 99,973，重复 27；重跑同批新增 0
- 20 万行：事件 199,920，重复 80
- 100 万行：事件 999,508，重复 492——与独立扫描的重复数完全一致，ETL 正确性关键验证

### 5.3 断点恢复

第一版"记录失败"不等于"可恢复"：重跑重复创建 batch，被中断的 batch 已有 RUNNING 记录，触发唯一键冲突（`Duplicate entry '1-4' for uk_etl_batch_run_no`）。修复后逻辑：读取最近 SUCCESS batch → 跳过已成功 → 复用失败/中断记录 → 续跑未完成。验证：batch 1-3 SUCCESS、4 中断，`--resume` 后跳过 1-3、续跑 4。

### 5.4 全量暂停原因

跑到 batch 61（已加载 5,997,478 条）时主动中断。不是数据错误，是吞吐不足（100 万行约 188.5 秒）。当前策略：优先完成课程交付，全量优化作为后续工作。600 万真实数据足够开发与演示。

## 6. 转化率口径修正

第一版用 `purchase events / cart events`，结果超过 100%——事件数不是漏斗人数，一个用户可多次购买。改为 **Session 漏斗**：以同一 Session 内是否出现对应事件计算 view_to_cart_rate、cart_to_purchase_rate、view_to_purchase_rate。

## 7. 业务视图

`v_product_statistics`、`v_brand_statistics`、`v_category_statistics`、`v_user_behavior_summary`，定义见 `sql/06_views.sql`。

## 8. 测试覆盖

pytest 8.4.2，共 37 个用例：API 16 + 数据库 16 + ETL 5。

- API：全部端点 + 分页校验 + 404 + 筛选
- 数据库：哈希唯一性、外键完整性、event_type 合法性、price 约束、视图存在与可查、必填字段、时间范围
- ETL：控制表、batch 状态、成功批次统计、staging 状态、哈希唯一

## 9. 历史问题索引

| 问题 | 根因 | 修复 |
|---|---|---|
| category_code 唯一约束冲突 | 真实数据一对多 | 删除 UNIQUE |
| 重复 ETL 产生重复事件 | 依赖自增 event_id | 增加 source hash |
| Session 跨批次统计错误 | 直接 INSERT | Session UPSERT |
| etl_batches 重试冲突 | 重试再次 INSERT | 复用已有 batch |
| Ctrl+C 后二次 traceback | DB 连接同时断开 | 中断处理加保护 |
| pytest 误执行 ETL 原型 | 原型命名符合发现规则 | 改名 `09_etl_prototype.py` |
| conversion >100% | 事件数计算漏斗 | 改 Session 漏斗 |
| conversion SQL Unknown column | 外层引用子查询字段 | 修正 SQL |
| pytest 旧字段断言失败 | API 字段改口径 | 同步测试字段 |
| 包导入失败 | `app` 与 `backend.app` 路径不一致 | 统一 `backend.app` |

## 10. 待完成事项

前端 UI、DFD、用例图、数据字典、正式 ER 图、模块结构图、正式测试用例表、前后端联调、演示流程、课程报告。
