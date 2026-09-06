import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'
import { setupServer } from 'msw/node'
import { http, HttpResponse } from 'msw'
import { effectScope } from 'vue'
import { handlers, wire } from '../../src/mocks/handlers'
import { overview, events, products, conversion, summarize } from '../../src/mocks/data'
import { parseResponse, request, ApiError } from '../../src/api/client'
import { api } from '../../src/api'
import { useResource } from '../../src/composables/useResource'
import { DEMO } from '../../src/utils'
const server = setupServer(...handlers)
beforeAll(() => server.listen({ onUnhandledRequest: 'error' }))
afterEach(() => {
  server.resetHandlers()
  vi.restoreAllMocks()
  vi.useRealTimers()
})
afterAll(() => server.close())

describe('接口契约与无损解析', () => {
  it('从原始 JSON 保留 19 位 ID，同时保持指标为数值与缺失字段为 null', () => {
    const parsed = parseResponse<{
      category_id: string
      product_id: string
      total: number
      price: number
      session_id: null
    }>(
      '{"category_id":2053013555631882655,"product_id":1000978,"total":35,"price":199.99,"session_id":null}',
    )
    expect(parsed).toEqual({
      category_id: DEMO.category,
      product_id: DEMO.product,
      total: 35,
      price: 199.99,
      session_id: null,
    })
    expect(wire({ category_id: DEMO.category })).toBe('{"category_id":2053013555631882655}')
  })
  it('商品接口保留多品牌与完整类别 ID，分页不重叠', async () => {
    const [detail, page1, page2] = await Promise.all([
      api.product(DEMO.product),
      api.products(1, 10),
      api.products(2, 10),
    ])
    expect(detail.category_id).toBe(DEMO.category)
    expect(detail.brands).toHaveLength(2)
    expect(page1.items).toHaveLength(10)
    expect(page2.items.some((p) => page1.items.some((q) => p.product_id === q.product_id))).toBe(
      false,
    )
    expect(page1.total).toBe(products.length)
  })
  it('用户行为筛选和分页符合服务端语义，无匹配结果返回 404', async () => {
    const data = await api.userEvents(DEMO.user, 1, 5, 'purchase')
    expect(data.items.length).toBeGreaterThan(0)
    expect(data.items.every((e) => e.event_type === 'purchase')).toBe(true)
    expect(data.items.length).toBeLessThanOrEqual(5)
    await expect(api.userEvents('999999999', 1, 20, '')).rejects.toMatchObject({
      status: 404,
      message: 'User not found or no matching events',
    })
    const emptyPage = await api.userEvents(DEMO.user, 9999, 20, '')
    expect(emptyPage.items).toEqual([])
    expect(emptyPage.total).toBeGreaterThan(0)
  })
  it('排行限制和降序正确，非法分页/limit 保持 422 格式', async () => {
    for (const kind of ['products', 'brands', 'categories'] as const) {
      const result = await api.ranking(kind, 5)
      expect(result.items.length).toBeLessThanOrEqual(5)
      expect(result.items.map((r) => r.event_count)).toEqual(
        result.items.map((r) => r.event_count).sort((a, b) => b - a),
      )
    }
    await expect(api.products(0, 20)).rejects.toMatchObject({ status: 422 })
    await expect(api.products(1, 101)).rejects.toMatchObject({ status: 422 })
    await expect(api.ranking('products', 51)).rejects.toMatchObject({ status: 422 })
  })
  it('Session 按时间排序、允许关联多个用户，所有统计来自同一组事件', async () => {
    const session = await api.session(DEMO.session)
    expect(session.events).toHaveLength(session.event_count)
    expect(new Set(session.events.map((e) => e.user_id)).size).toBeGreaterThan(1)
    expect(session.events.map((e) => e.event_time)).toEqual(
      session.events.map((e) => e.event_time).sort(),
    )
    expect(overview.total_events).toBe(events.length)
    expect(overview.total_views + overview.total_carts + overview.total_purchases).toBe(
      overview.total_events,
    )
    expect(summarize(events).event_count).toBe(overview.total_events)
    const zero = await api.statistics(products.at(-1)!.product_id)
    expect(zero.event_count).toBe(0)
    expect(zero.sales_amount).toBe(0)
    expect(conversion.view_to_cart_rate).toBe(
      conversion.view_cart_sessions / conversion.view_sessions,
    )
    expect(conversion.cart_to_purchase_rate).toBe(
      conversion.cart_purchase_sessions / conversion.cart_sessions,
    )
    expect(conversion.view_to_purchase_rate).toBe(
      conversion.view_purchase_sessions / conversion.view_sessions,
    )
  })
  it('错误保持 HTTP 状态，非法 JSON 不作为正常数据返回', async () => {
    server.use(
      http.get('http://localhost/api/dashboard/overview', () =>
        HttpResponse.json(
          { code: 500, message: 'Internal server error', data: null },
          { status: 500 },
        ),
      ),
    )
    await expect(api.overview()).rejects.toMatchObject({ status: 500 })
    server.use(
      http.get('http://localhost/api/dashboard/overview', () =>
        HttpResponse.text('<html>Proxy error</html>'),
      ),
    )
    await expect(api.overview()).rejects.toMatchObject({ status: 502 })
  })
  it('超时会终止请求并给出可重试错误', async () => {
    vi.useFakeTimers()
    vi.spyOn(globalThis, 'fetch').mockImplementation(
      (_url, options) =>
        new Promise((_resolve, reject) => {
          options?.signal?.addEventListener('abort', () =>
            reject(new DOMException('Aborted', 'AbortError')),
          )
        }),
    )
    const promise = expect(request('/slow')).rejects.toMatchObject({ status: 408 })
    await vi.advanceTimersByTimeAsync(30_001)
    await promise
  })
})

describe('查询竞态', () => {
  it('较早返回的旧请求不会覆盖新结果或错误状态', async () => {
    const scope = effectScope()
    const resource = scope.run(() => useResource<string>())!
    let firstResolve: (value: string) => void = () => {}
    const old = resource.load(
      () =>
        new Promise<string>((resolve) => {
          firstResolve = resolve
        }),
    )
    await resource.load(() => Promise.resolve('new'))
    firstResolve('old')
    await old
    expect(resource.data.value).toBe('new')
    expect(resource.loading.value).toBe(false)
    await resource.load(() => Promise.reject(new ApiError(500, 'failed')))
    expect(resource.data.value).toBeNull()
    expect(resource.error.value?.status).toBe(500)
    scope.stop()
  })
})
