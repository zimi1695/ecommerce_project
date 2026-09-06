import { test, expect } from '@playwright/test'
import { DEMO } from '../../src/utils'

test('总览与商品详情：导航、无损 ID、多品牌和返回分页', async ({ page }) => {
  const errors: string[] = []
  page.on('pageerror', (error) => errors.push(error.message))
  await page.goto('/')
  await expect(page.getByRole('heading', { name: '数据总览' })).toBeVisible()
  await expect(page.getByText('演示数据', { exact: true })).toBeVisible()
  await expect(page.locator('.metric-value').first()).not.toBeEmpty()
  await expect(page.locator('.mini-rank')).toHaveCount(5)
  await page.screenshot({
    path: '../docs/screenshots/frontend-overview.png',
    fullPage: true,
    animations: 'disabled',
  })
  await page.getByRole('navigation').getByText('商品探索').click()
  await expect(page.getByRole('table').last().getByText(DEMO.category).first()).toBeVisible()
  await page.getByLabel('第 2 页', { exact: true }).click()
  await expect(page).toHaveURL(/page=2/)
  const productId = (await page.locator('.el-table__body .table-link').first().innerText())
    .replace('P', '')
    .trim()
  await page.locator('.el-table__body .table-link').first().click()
  await expect(page.getByRole('heading', { name: '商品详情' })).toBeVisible()
  await expect(page.locator('.profile-primary h2')).toHaveText(productId)
  await page.getByRole('link', { name: '返回商品目录' }).click()
  await expect(page).toHaveURL(/page=2/)
  await page.getByRole('textbox', { name: '商品 ID' }).fill(DEMO.product)
  await page.getByRole('button', { name: '查询商品' }).click()
  await expect(page.getByTestId('category-id')).toHaveText(DEMO.category)
  await expect(page.locator('.brand-tag')).toHaveText(['samsung', 'lenovo'])
  await page.reload()
  await expect(page.getByTestId('category-id')).toHaveText(DEMO.category)
  await expect(page.locator('.metric-value')).toHaveCount(4)
  expect(errors).toEqual([])
})

test('用户筛选、URL 恢复、Session 与商品串联', async ({ page }) => {
  await page.goto(`/#/users?user_id=${DEMO.user}&page=2`)
  await expect(page.locator('.el-table__body tr')).toHaveCount(20)
  await page
    .getByRole('radiogroup', { name: '行为类型' })
    .getByText('购买', { exact: true })
    .click()
  await expect(page).toHaveURL(/page=1/)
  await expect(page).toHaveURL(/event_type=purchase/)
  await expect(page.locator('.event-badge').first()).toHaveText('购买')
  await page.reload()
  await expect(page.getByRole('radio', { name: '购买', exact: true })).toBeChecked()
  await expect(page.locator('.event-badge').first()).toHaveText('购买')
  await page.locator('.el-table__body a[href*="/sessions/"]').first().click()
  await expect(page.getByRole('heading', { name: 'Session 轨迹' })).toBeVisible()
  await expect(page.locator('.timeline-card').first()).toBeVisible()
  await page.locator('.timeline-card .table-link').first().click()
  await expect(page.getByRole('heading', { name: '商品详情' })).toBeVisible()
})

test('分析排行切换、口径说明与空值类别', async ({ page }) => {
  await page.goto('/#/analytics')
  await expect(page.getByText('不保证行为先后顺序', { exact: true })).toBeVisible()
  await expect(page.locator('.conversion-rates .metric-value')).toHaveCount(3)
  await expect(page.locator('.el-table__body tr')).toHaveCount(10)
  await page
    .getByRole('radiogroup', { name: '排行维度' })
    .getByText('品牌排行', { exact: true })
    .click()
  await expect(page).toHaveURL(/kind=brands/)
  await expect(page.locator('.el-table__body').getByText('samsung', { exact: true })).toBeVisible()
  await page
    .getByRole('radiogroup', { name: '排行维度' })
    .getByText('类别排行', { exact: true })
    .click()
  await expect(
    page.locator('.el-table__body').getByText(DEMO.category, { exact: true }),
  ).toBeVisible()
  await expect(
    page.locator('.el-table__body').getByText('未提供类别名称', { exact: true }),
  ).toBeVisible()
  await page.locator('.limit-select').getByText('Top 10', { exact: true }).click()
  await page.getByRole('option', { name: 'Top 5', exact: true }).click()
  await expect(page).toHaveURL(/limit=5/)
  await expect(page.locator('.el-table__body tr')).toHaveCount(5)
  await page.screenshot({
    path: '../docs/screenshots/frontend-analytics.png',
    fullPage: true,
    animations: 'disabled',
  })
})

test('未找到对象、空页、零统计、服务错误与重试', async ({ page }) => {
  await page.goto('/#/users?user_id=999999999')
  await expect(page.getByText('用户不存在或没有符合条件的行为', { exact: true })).toBeVisible()
  await page.goto('/#/products?page=999')
  await expect(page.getByRole('button', { name: '返回第一页' })).toBeVisible()
  await page.getByRole('button', { name: '返回第一页' }).click()
  await expect(page.locator('.el-table__body tr')).toHaveCount(20)
  await page.goto('/#/products/1001013')
  await expect(page.locator('.metric-value')).toHaveText(['0', '0', '0', '0.00'])
  await page.goto('/#/products/999999999')
  await expect(page.getByText('未找到该商品', { exact: true })).toBeVisible()
  await page.goto('/#/sessions/nonexistent')
  await expect(page.getByText('未找到该 Session', { exact: true })).toBeVisible()
  await page.evaluate(() => sessionStorage.setItem('mock-scenario', 'error'))
  await page.goto('/#/products')
  await expect(page.getByText('数据暂时无法加载', { exact: true })).toBeVisible()
  await page.evaluate(() => sessionStorage.removeItem('mock-scenario'))
  await page.getByRole('button', { name: '重新加载' }).click()
  await expect(page.locator('.el-table__body tr')).toHaveCount(20)
})

test('窄屏导航、图表与未知路由', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.locator('.mini-rank')).toHaveCount(5)
  await page.screenshot({
    path: '../docs/screenshots/frontend-mobile.png',
    fullPage: true,
    animations: 'disabled',
  })
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true)
  await page.getByRole('button', { name: '展开导航' }).click()
  await page.getByRole('navigation').getByText('用户行为').click()
  await expect(page.getByRole('heading', { name: '用户行为' })).toBeVisible()
  await expect(page.getByRole('button', { name: '展开导航' })).toHaveAttribute(
    'aria-expanded',
    'false',
  )
  await page.goto('/#/unknown')
  await expect(page.getByRole('heading', { name: '这条路径暂时没有数据' })).toBeVisible()
})

test('真实模式用拦截响应验证契约，不启用 Mock 或失败回退', async ({ browser }) => {
  const context = await browser.newContext({ serviceWorkers: 'block' })
  const page = await context.newPage()
  await page.route('**/api/products/1000978', (route) =>
    route.fulfill({
      contentType: 'application/json',
      body: '{"product_id":1000978,"category_id":2053013555631882655,"category_code":null,"brands":[]}',
    }),
  )
  await page.route('**/api/products/1000978/statistics', (route) =>
    route.fulfill({
      contentType: 'application/json',
      body: '{"product_id":1000978,"category_id":2053013555631882655,"category_code":null,"event_count":0,"view_count":0,"cart_count":0,"purchase_count":0,"sales_amount":0}',
    }),
  )
  await page.goto(`http://127.0.0.1:5174/#/products/${DEMO.product}`)
  await expect(page.getByText('真实接口', { exact: true })).toBeVisible()
  await expect(page.getByTestId('category-id')).toHaveText(DEMO.category)
  await expect(page.locator('.metric-value')).toHaveText(['0', '0', '0', '0.00'])
  await page.route('**/api/products?page=1&page_size=20', (route) =>
    route.fulfill({
      status: 500,
      contentType: 'application/json',
      body: '{"code":500,"message":"Internal server error","data":null}',
    }),
  )
  await page.getByRole('link', { name: '返回商品目录' }).click()
  await expect(page.getByText('数据暂时无法加载', { exact: true })).toBeVisible()
  await expect(page.locator('.el-table__body tr')).toHaveCount(0)
  await expect(page.getByText('演示数据', { exact: true })).toHaveCount(0)
  await context.close()
})
