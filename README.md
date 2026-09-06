# 电商用户行为分析系统

基于 MySQL 的多品类电商用户行为分析与管理系统（数据库课程实践）。

以 Kaggle 2019 年 11 月电商行为数据（6750 万条事件、9 GB）为底座，完成数据建模、ETL 加载、REST API 与自动化测试，形成可解释的数据应用闭环：**真实数据 → 依赖验证 → 建模 → ETL → 约束 → API → 测试 → 交付**。

## 技术栈

| 层 | 选型 |
|---|---|
| 数据库 | MySQL 8.0（Docker 容器 `ecommerce-mysql`） |
| 后端 | Python 3.11 / FastAPI / SQLAlchemy / PyMySQL |
| 数据处理 | pandas（chunksize=100000 流式加载） |
| 测试 | pytest，37 个用例全部通过 |
| 环境 | WSL2 Ubuntu + Conda（`bigdata` 环境） |

## 核心功能

- 数据总览看板：事件 / 用户 / 商品 / Session 规模一览
- 商品查询、详情与行为统计
- 用户行为流水：分页 + 事件类型筛选
- Session 详情与行为时间线
- 商品 / 品牌 / 类别排行
- 浏览 → 加购 → 购买转化漏斗（Session 口径）
- 4 个数据库业务视图
- ETL 幂等加载与断点恢复

## 快速开始

```bash
# 1. 启动数据库
docker start ecommerce-mysql

# 2. 激活环境并启动后端
conda activate bigdata
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 3. 运行测试（基线：37 passed）
cd .. && python -m pytest -v
```

数据库连接：`127.0.0.1:3307`，库名 `ecommerce`，用户 `ecommerce`。

## 目录结构

```text
ecommerce_project/
├── backend/          # FastAPI 后端
│   └── app/routers/  # dashboard / products / users / sessions / analytics
├── sql/              # 建模、约束、转换、ETL 控制、视图脚本（按序号执行）
├── scripts/
│   ├── etl/          # 正式 ETL 脚本
│   ├── analysis/     # 数据探索与依赖验证脚本
│   └── validation/   # 历史 / 实验脚本
├── tests/            # pytest 测试
├── docs/             # 交接手册、设计依据、演示基线
├── data/
│   ├── raw/          # 原始数据（不入库，见 Release）
│   └── processed/   # 可再生的中间产物
└── docker-compose.yml
```

## API 一览

| 模块 | 端点 |
|---|---|
| Dashboard | `GET /api/dashboard/overview` |
| 商品 | `GET /api/products`、`GET /api/products/{id}`、`GET /api/products/{id}/statistics` |
| 用户 | `GET /api/users/{user_id}/events`（支持 `page` / `page_size` / `event_type`） |
| Session | `GET /api/sessions/{session_id}` |
| 分析 | `GET /api/analytics/top-products` / `top-brands` / `top-categories` / `conversion` |

错误响应统一为 `{code, message, data}` 结构（404 / 422 / 500）。

## 数据文件

原始数据 `2019-Nov.csv`（9 GB）与压缩包不入 Git 仓库，请从 [Release v1.0.0](https://github.com/zimi1695/ecommerce_project/releases/tag/v1.0.0) 下载分卷并合并，解压后放置 `data/raw/`。

数据来源：Kaggle — *eCommerce behavior data from multi category store*（2019 年 11 月）。

## 文档索引

| 文档 | 内容 |
|---|---|
| [docs/PROJECT_HANDOVER.md](docs/PROJECT_HANDOVER.md) | 交接手册：环境、启动、设计红线、故障排查 |
| [docs/README.md](docs/README.md) | 设计依据与开发过程：数据验证、建模决策、ETL 演进 |
| [docs/demo_data.md](docs/demo_data.md) | 演示数据基线与固定演示对象 |

## License

MIT
