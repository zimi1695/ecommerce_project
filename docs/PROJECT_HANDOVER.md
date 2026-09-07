# 项目交接手册

> 项目：基于 MySQL 的多品类电商用户行为分析与管理系统
> 适用场景：新成员接手、协作开发、故障恢复、最终提交

## 1. 项目现状

后端历史基线为已完成并通过测试、约 600 万条真实事件（前 60 个 ETL batch）。前端六类页面已合入 main 并于 2026-09-07 完成真实接口联调（9 类接口实测、CORS 与索引性能修复，详见 [前端交接](FRONTEND_HANDOVER.md) 的集成确认节）。在线演示：https://zimi1695.github.io/ecommerce_project/ 。

| 模块 | 状态 |
|---|---|
| 数据探索与依赖验证 | 已完成 |
| 数据建模 + MySQL 建库 | 已完成 |
| ETL（幂等加载 / 断点恢复） | 已完成 |
| FastAPI 后端（5 组路由） | 已完成 |
| 业务视图（4 个） | 已完成 |
| 自动化测试 | 后端 pytest 37 passed；前端 8 单元 + 6 浏览器流程通过 |
| 前端 | 已合入 main 并完成真实接口联调（2026-09-07）；GitHub Pages 在线演示 |
| 课程设计文档（ER / DFD / 用例 / 数据字典） | 未开始，当前最大缺口 |

## 2. 接手第一步

**仅负责前端时：**按 [前端 README](../frontend/README.md) 安装与验证前端，不必启动数据库、执行 ETL 或运行后端测试。下列基线要求适用于后端维护和系统集成。

不要直接改数据库。按顺序确认基线：

```bash
cd ~/ecommerce_project
conda activate bigdata
docker start ecommerce-mysql
docker ps                    # 确认容器运行
python -m pytest -v          # 基线必须是 37 passed
```

不是 37 passed 就先排查问题，不要继续加功能。

## 3. 环境信息

| 项 | 值 |
|---|---|
| 容器 | `ecommerce-mysql`（Docker volume 持久化） |
| 端口映射 | `127.0.0.1:3307 → 3306` |
| 数据库 / 用户 | `ecommerce` / `ecommerce` |
| Python 环境 | Conda `bigdata` |
| 后端启动 | `uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000`（从项目根启动；`backend/` 目录下以 `app.main:app` 启动会因 `backend.app` 导入路径报错） |
| 前端环境 | Node 22.12+/24.x（WSL 用 nvm 管理，当前 v22.23.2） |
| 前端启动 | `cd frontend && npm run dev:api`（真实接口）/ `npm run dev`（Mock） |
| 常驻服务 | `scripts/deploy/` 的 systemd 单元：`ecommerce-backend`、`ecommerce-frontend`，`systemctl status/restart` 管理 |
| 在线演示 | https://zimi1695.github.io/ecommerce_project/ （push main 自动部署，Mock 构建） |

## 4. 当前数据规模

| 表 | 行数 |
|---|---:|
| behavior_events | 5,997,478 |
| users | 748,770 |
| sessions | 1,331,322 |
| products | 119,243 |
| brands | 3,241 |
| categories | 618 |

来源：2019-Nov 数据前 60 个 batch（每 batch 10 万行）。batch 61 中断，`--resume` 可续。

## 5. ETL 说明

正式脚本：`scripts/etl/run_etl.py`。`scripts/analysis/` 下 01-15 按开发时序编号：01-07 数据探索与依赖验证，08 连库冒烟测试，**09 ETL 原型不是正式管线**，10-11 类别依赖复查，12-15 小批量加载测试。部署相关见 `scripts/deploy/`（一键启动 + systemd 服务单元）。

流程：CSV → pandas 分块 → `staging_events` → 维度表 / 桥表 → Session UPSERT → `behavior_events`（`source_event_hash` 唯一约束去重）。

```bash
python scripts/etl/run_etl.py            # 正常运行
python scripts/etl/run_etl.py --resume   # 断点恢复
```

**当前策略：暂停全量导入。** 未做性能优化前全量耗时过长（100 万行约 188 秒），优先完成前端、测试与文档。禁止接手后未经讨论直接跑全量。

## 6. 关键设计决策（不要推翻）

以下结论来自全量数据扫描，不要推翻：

| 决策 | 数据依据 |
|---|---|
| `categories` 不加 `UNIQUE(category_code)` | 58 个 category_code 对应多个 category_id |
| `products` 不存 price | 70,684 个商品存在多个价格，price 属于行为发生时点 |
| 产品-品牌用桥表 `product_brands` | 136 个商品有多个非空品牌 |
| `sessions` 不存 user_id | 591 个 Session ID 关联多个 user_id |
| `behavior_events.source_event_hash` 唯一约束 | 原始数据含 100,519 条完全重复记录，靠 SHA-256 哈希 + INSERT IGNORE 实现幂等 |

事实表暂未建全外键（600 万行且未来可达 6750 万，批量写入优先吞吐），展示前可再评估。

## 7. 转化率口径（不要改回）

转化漏斗按 **Session 数**计算（view session → cart session → purchase session），不是事件次数。事件口径会出现超过 100% 的结果（一个用户可多次购买）。

## 8. 红线清单

1. 不把 `category_code` 改成 UNIQUE
2. 不把 price 放回 products
3. 不给 product 绑定单一 brand_id
4. 不给 session 强绑 user_id
5. 不删 `source_event_hash`
6. 不让 pytest 执行实验脚本（实验脚本不要命名 `test_*.py` / `*_test.py`）
7. 不贸然重跑全量 ETL
8. 不执行 `docker compose down -v`（会删数据库卷）
9. SQL 口径变化必须同步测试
10. 结构变化必须同步 ER 图、关系模型、View、API 和测试

## 9. API 与错误格式

端点清单见根目录 [README.md](../README.md)。错误响应统一结构，新接口不要另起炉灶：

```json
{ "code": 404, "message": "Product not found", "data": null }
```

## 10. 故障排查

| 症状 | 处理 |
|---|---|
| 容器没起 | `docker start ecommerce-mysql` |
| 后端没起 | 见第 3 节启动命令 |
| pytest 失败 | 先跑 `python -m pytest -v` 定位用例，再 `git diff` 看改动，优先怀疑：结构变化 / API 字段变化 / SQL 口径变化 / 导入路径变化 |
| 需要继续 ETL | 先查 `etl_runs` / `etl_batches` 最近状态，确认后再 `--resume` |

## 11. 固定演示对象

统一使用，不要各自随便找 ID：user `564068124`、product `1000978`、session `4488e77a-9901-4c4b-b162-47a224ceab51`、brand `9 / samsung`、category `2053013555631882655 / electronics.smartphone`。详见 [demo_data.md](demo_data.md)。

## 12. 原始数据

`data/raw/2019-Nov.csv`（9 GB，6750 万行）与 zip 均不删。Git 仓库不含数据文件，从 GitHub Release 下载。

## 13. 协作分工建议

前端实现与集成结论见 [FRONTEND_HANDOVER.md](FRONTEND_HANDOVER.md)（六类页面已交付合入，接口联调已完成）。剩余工作聚焦分析与文档：

| 角色 | 负责 |
|---|---|
| 系统分析 | DFD、用例图、数据字典、ER 图、模块结构图（注意 products-brands 是多对多，sessions-users 不要画成一对一） |
| 测试 | `docs/test_cases.md` 正式测试用例表 + pytest 结果截图 |
| 文档 | 项目报告、README、开发过程、问题与讨论、总结 |

## 14. 提交前检查清单

- [ ] MySQL 可启动，表结构 / 外键 / View 正常
- [ ] FastAPI 可启动，六组 API 全部可用
- [ ] 前端可启动（Dashboard / 商品 / 用户 / Session / 分析）
- [ ] 后端 37 个测试全部 PASSED
- [ ] 前端 `npm run check` 与浏览器流程通过
- [ ] 正式测试用例表完整
- [ ] ER / DFD / 用例 / 数据字典齐全
- [ ] 报告与演示流程完成
