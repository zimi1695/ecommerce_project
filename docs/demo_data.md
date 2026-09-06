# 系统演示数据基线

## 数据库状态

本项目当前使用 2019-Nov 电商用户行为数据进行系统开发和测试。
当前数据库保留约 610 万条已处理行为事件，暂不进行全量 6750 万条数据导入。

## 固定演示对象

### 用户

- user_id: 564068124
- 用途：用户行为查询、购买行为筛选

### 商品

- product_id: 1000978
- 用途：商品详情、商品统计

### Session

- session_id: 4488e77a-9901-4c4b-b162-47a224ceab51
- 用途：Session 详情及行为时间线

### 品牌

- brand_id: 9
- brand_name: samsung

### 类别

- category_id: 2053013555631882655
- category_code: electronics.smartphone

## API 演示地址

- Dashboard:
  `/api/dashboard/overview`

- 商品列表:
  `/api/products?page=1&page_size=5`

- 商品详情:
  `/api/products/1000978`

- 商品统计:
  `/api/products/1000978/statistics`

- 用户行为:
  `/api/users/564068124/events?page=1&page_size=5`

- 用户购买行为:
  `/api/users/564068124/events?page=1&page_size=5&event_type=purchase`

- Session:
  `/api/sessions/4488e77a-9901-4c4b-b162-47a224ceab51`

- 热门商品:
  `/api/analytics/top-products?limit=5`

- 热门品牌:
  `/api/analytics/top-brands?limit=5`

- 热门类别:
  `/api/analytics/top-categories?limit=5`

- 转化分析:
  `/api/analytics/conversion`