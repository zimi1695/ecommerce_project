# 演示数据基线

当前数据库使用 2019-Nov 电商行为数据的前 60 个 ETL batch（约 600 万条事件），暂不导入全量 6750 万条。

## 固定演示对象

统一使用以下对象做演示与测试，不要各自另找 ID：

| 类型 | 值 | 用途 |
|---|---|---|
| 用户 | `564068124` | 用户行为查询、购买行为筛选 |
| 商品 | `1000978` | 商品详情、商品统计 |
| Session | `4488e77a-9901-4c4b-b162-47a224ceab51` | Session 详情与行为时间线 |
| 品牌 | `9` / samsung | 品牌排行 |
| 类别 | `2053013555631882655` / electronics.smartphone | 类别排行 |

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
