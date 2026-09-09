# 观数 · 电商行为分析前端

Vue 3 + TypeScript + Vite，使用 Element Plus 与 ECharts 构建中文深色分析界面。默认开发模式使用 MSW 模拟全部业务接口，不需要启动 Python、MySQL 或 ETL。

## 环境与启动

使用 Node.js 22.12+（22 系列）或 24.x，npm。交付环境为 Node.js 22.23.2 / npm 10.9.8。依赖版本以 `package-lock.json` 为准。

在仓库根目录执行：

```bash
cd frontend
npm ci
npm run dev
```

打开终端显示的本地地址，默认为 `http://127.0.0.1:5173`。首次启动等待 Mock Service Worker 就绪，页面右上角显示“演示数据”。请通过 HTTP 本地服务访问，不要直接双击 HTML 文件。

## 模式与命令

| 命令                 | 默认行为                                           |
| -------------------- | -------------------------------------------------- |
| `npm run dev`        | 开发服务，启用 Mock                                |
| `npm run dev:api`    | 开发服务，访问真实接口                             |
| `npm run check`      | 类型检查、ESLint、Prettier、Vitest                 |
| `npm run test:e2e`   | Chromium 浏览器关键流程测试，自动启动两个前端服务  |
| `npm run build`      | 类型检查并生成真实接口版本到 `dist/`               |
| `npm run build:demo` | 类型检查并生成可独立运行的 Mock 演示版本到 `dist/` |
| `npm run preview`    | 本地预览最近一次构建，默认端口 4173                |

两个构建命令都输出到同一个 `dist/`，后一次覆盖前一次。生产版本不启动 Mock；演示版本持续显示“演示数据”。

### 接入真实后端

默认无需配置文件：`npm run dev:api` 将 `/api` 请求代理至 `http://127.0.0.1:8000`，保留 `/api` 路径。

需要修改地址时，将 `.env.example` 复制为 `.env.local`：

```dotenv
VITE_API_BASE_URL=/api
API_PROXY_TARGET=http://后端主机:8000
```

修改环境变量后重新启动／构建。`VITE_USE_MOCK` 可以显式覆盖模式默认值，例如 `VITE_USE_MOCK=false`；不需要覆盖时保持该项未设置，避免 `.env.local` 中的 `true` 将正式构建变成演示版本。`VITE_*` 内容会公开进入浏览器，不存放密码或令牌。

Vite 代理仅用于开发。真实版本部署时由集成人员将同源 `/api` 转发至后端，或将 `VITE_API_BASE_URL` 配为完整后端 API 地址并由后端配置 CORS。`preview` 用于查看构建产物，不是生产部署方案。

路由采用 `#/...`，刷新子页面无需服务器配置 SPA 回退。应用使用相对资源基址，演示版本的 Service Worker 也相对于应用目录加载。

## 页面与接口契约

接口以 `backend/app/routers/` 当前代码为准，不依赖缺少响应模型的 OpenAPI 自动生成类型。成功响应为原始对象；列表为 `{page, page_size, total, items}`，排行为 `{limit, items}`；错误为 `{code, message, data}`。

| 页面         | 接口（均为 GET）                                                            | 查询能力                                       |
| ------------ | --------------------------------------------------------------------------- | ---------------------------------------------- |
| 数据总览     | `/api/dashboard/overview`、`/api/analytics/top-products`                    | 指标、行为分布、Top 5 商品                     |
| 商品探索     | `/api/products`                                                             | `page`、`page_size`；按 ID 直达详情            |
| 商品详情     | `/api/products/{id}`、`/api/products/{id}/statistics`                       | 类别、多品牌、事件统计与销售金额               |
| 用户行为     | `/api/users/{user_id}/events`                                               | `page`、`page_size`、`event_type`              |
| Session 轨迹 | `/api/sessions/{session_id}`                                                | 时间线及关联用户；前端每页展示 50 条已返回事件 |
| 转化与排行   | `/api/analytics/top-products`、`top-brands`、`top-categories`、`conversion` | `limit` 为 5／10／20／50；Session 关联指标     |

- 分页参数与筛选条件保存在 URL；用户筛选切换后回到第一页。商品目录跳转详情后可返回原分页。
- 商品／用户数字 ID 使用字符串输入。类别 ID 如 `2053013555631882655` 超出 JavaScript 安全整数范围：请求模块从响应原文无损解析，再将所有 `*_id` 规范成字符串。不要在此之前调用 `response.json()` 或 `JSON.parse()`。
- 商品没有名称、图片和固定售价；品牌为数组。类别名称、品牌名称和 Session 可为空，使用明确的缺失提示。
- 用户接口的 404 同时可能表示用户不存在或筛选无结果，页面保留此区别，不断言用户一定不存在。
- Session 不强绑单个用户，每条事件保留自己的用户 ID。
- 时间按现有项目的 UTC 约定显示，币种未经确认，金额不添加货币符号。
- 排行按事件量降序，不能将接口返回的局部 Top N 当作全量按销售额排序。
- 三项转化率使用后端返回值，展示为百分比。它们描述同一 Session 内两种行为的共同出现，未验证发生顺序或完整三步路径。
- 请求超时为 30 秒；查询切换会取消旧请求并拒绝旧结果覆盖新页面。真实接口失败不会自动退回 Mock。

## Mock 与开发验证

Mock 是一组确定性合成事件及其聚合结果，覆盖全部 10 个业务端点。2026-09-09 起合成数据按真实库分布构造：事件类型 view 96.5% / cart 1.2% / purchase 2.4%，Session 漏斗 view→cart 3.67% / cart→purchase 54.3% / view→purchase 5.81%（真实口径 3.68% / 54.2% / 5.82%），时间全月分布、价格 0~2574 长尾。固定演示对象的数字与真实接口精确一致（商品 1000978 = 22 条 view，用户 564068124 = 781 条事件含 265 购买，Session 4488e77a = 504 条 view），Mock / 真实两种模式切换页面数字不变。背景数据为约 4.7 万条事件的合成抽样，**总量不代表数据库 600 万级规模**。总览、商品统计、排行、Session 和用户行为来自同一组事件。

固定入口：

- 商品：`/#/products/1000978`（多品牌、19 位类别 ID）
- 用户：`/#/users?user_id=564068124`
- Session：`/#/sessions/4488e77a-9901-4c4b-b162-47a224ceab51`（多个关联用户）
- 零统计商品：`/#/products/1001013`
- 空页：`/#/products?page=999`
- 未找到：商品／用户 `999999999`，Session `nonexistent`

仅在 Mock 模式，浏览器控制台可设置场景后点击页面刷新／重试按钮：

```javascript
sessionStorage.setItem('mock-scenario', 'error') // 全部业务接口返回 500
sessionStorage.setItem('mock-scenario', 'slow') // 响应延迟 1.6 秒
sessionStorage.removeItem('mock-scenario') // 恢复默认 180 ms 延迟
```

Mock 的 422 会校验分页与排行数量；无匹配用户事件返回 404；超出已有记录的页返回空列表。首次运行浏览器测试前：

```bash
npx playwright install chromium --no-shell
npm run test:e2e
```

浏览器测试占用 5173 和 5174，请先停止占用这些端口的本地服务。若测试提示 Linux 系统库缺失，由环境负责人安装对应运行库。测试使用本地 Chromium、Mock 或拦截响应，不访问真实后端；生成的 HTML 报告位于 `playwright-report/`，失败诊断位于 `test-results/`，均不入 Git。

类型与适配器位于 `src/types.ts`、`src/api/`；可取消请求状态在 `src/composables/`；模拟契约在 `src/mocks/`；页面位于 `src/pages/`。修改接口时同步更新类型、Mock、页面与对应测试。

## 交接

详见 [前端交接与验收记录](../docs/FRONTEND_HANDOVER.md)。前端检查不替代真实接口联调、后端测试或生产性能验证。
