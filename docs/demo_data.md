# 演示数据基线

当前数据库使用 2019-Nov 电商行为数据的前 60 个 ETL batch（约 600 万条事件），暂不导入全量 6750 万条。

## 固定演示对象

统一使用以下对象做演示与测试，不要各自另找 ID：

| 类型 | 值 | 用途 |
|---|---|---|
| 用户 | `564068124` | 用户行为查询、购买行为筛选（全库购买冠军：781 事件 / 265 购买 / 消费 77,703.89） |
| 商品 | `1000978` | 商品详情、商品统计（双品牌 samsung+lenovo，桥表演示） |
| 商品 | `7003278` | 备选多品牌案例（coballe+joie，112 事件） |
| Session | `4488e77a-9901-4c4b-b162-47a224ceab51` | 深度浏览：504 条 view，03:38~07:15 |
| Session | `828b56d9-6c23-40b7-8825-173d58d33fe4` | 跨用户 Session（2 用户 24 事件，sessions 不绑 user_id 的证据） |
| 商品 | `1004856` | 流量王：62,457 事件 / 销售额 457,966 |
| 商品 | `1005115` | 演示用户反复购买的 Apple 手机（921 元） |
| 商品 | `21408160` | 全库最高单价 2574.07 |
| 品牌 | `9` / samsung | 品牌排行（与 apple 双巨头） |
| 类别 | `2053013555631882655` / electronics.smartphone | 类别榜首、19 位大整数 ID 演示 |

完整演示路线与讲稿见 [DEMO_SCRIPT.md](DEMO_SCRIPT.md)。

## 演示 API 清单

```text
/api/dashboard/overview
/api/products?page=1&page_size=5
/api/products/1000978
/api/products/1000978/statistics
/api/users/564068124/events?page=1&page_size=5
/api/users/564068124/events?page=1&page_size=5&event_type=purchase
/api/sessions/4488e77a-9901-4c4b-b162-47a224ceab51
/api/analytics/top-products?limit=5
/api/analytics/top-brands?limit=5
/api/analytics/top-categories?limit=5
/api/analytics/conversion
```
