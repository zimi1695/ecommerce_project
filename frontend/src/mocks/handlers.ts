import { http, HttpResponse, delay } from 'msw'
import JSONbig from 'json-bigint'
import { apiBase } from '../api/client'
import { products, events, productStatistics, overview, ranking, conversion } from './data'
import type { RankingKind } from '../types'

const root = apiBase.startsWith('http') ? apiBase : `*${apiBase}`
function numericIds(value: unknown, key = ''): unknown {
  if (key.endsWith('_id') && typeof value === 'string' && /^\d+$/.test(value)) return BigInt(value)
  if (Array.isArray(value)) return value.map((v) => numericIds(v))
  if (value && typeof value === 'object')
    return Object.fromEntries(Object.entries(value).map(([k, v]) => [k, numericIds(v, k)]))
  return value
}
export function wire(data: unknown) {
  return JSONbig.stringify(numericIds(data))
}
const response = (data: unknown, status = 200) =>
  new HttpResponse(wire(data), { status, headers: { 'Content-Type': 'application/json' } })
const error = (status: number, message: string) =>
  response({ code: status, message, data: status === 422 ? [] : null }, status)
function intParam(url: URL, key: string, fallback: number, max = Number.MAX_SAFE_INTEGER) {
  const raw = url.searchParams.get(key)
  const n = raw === null ? fallback : Number(raw)
  return Number.isSafeInteger(n) && n >= 1 && n <= max ? n : null
}
async function before() {
  const scenario =
    typeof sessionStorage === 'undefined' ? '' : sessionStorage.getItem('mock-scenario')
  await delay(scenario === 'slow' ? 1600 : 180)
  return scenario === 'error' ? error(500, 'Internal server error') : undefined
}
export const handlers = [
  http.get(`${root}/dashboard/overview`, async () => (await before()) ?? response(overview)),
  http.get(`${root}/products`, async ({ request }) => {
    const failed = await before()
    if (failed) return failed
    const url = new URL(request.url),
      page = intParam(url, 'page', 1),
      size = intParam(url, 'page_size', 20, 100)
    if (!page || !size) return error(422, 'Request validation failed')
    return response({
      page,
      page_size: size,
      total: products.length,
      items: products.slice((page - 1) * size, page * size).map(({ brands: _brands, ...p }) => p),
    })
  }),
  http.get(`${root}/products/:id/statistics`, async ({ params }) => {
    const failed = await before()
    if (failed) return failed
    if (!/^\d+$/.test(String(params.id))) return error(422, 'Request validation failed')
    const product = productStatistics.find((p) => p.product_id === params.id)
    return product ? response(product) : error(404, 'Product not found')
  }),
  http.get(`${root}/products/:id`, async ({ params }) => {
    const failed = await before()
    if (failed) return failed
    if (!/^\d+$/.test(String(params.id))) return error(422, 'Request validation failed')
    const product = products.find((p) => p.product_id === params.id)
    return product ? response(product) : error(404, 'Product not found')
  }),
  http.get(`${root}/users/:id/events`, async ({ params, request }) => {
    const failed = await before()
    if (failed) return failed
    const url = new URL(request.url),
      page = intParam(url, 'page', 1),
      size = intParam(url, 'page_size', 20, 100)
    if (!page || !size || !/^\d+$/.test(String(params.id)))
      return error(422, 'Request validation failed')
    const type = url.searchParams.get('event_type')
    const rows = events
      .filter((e) => e.user_id === params.id && (type === null || e.event_type === type))
      .reverse()
    if (!rows.length) return error(404, 'User not found or no matching events')
    return response({
      user_id: params.id,
      page,
      page_size: size,
      total: rows.length,
      items: rows
        .slice((page - 1) * size, page * size)
        .map(({ user_id: _user, brand_id: _brand, ...e }) => e),
    })
  }),
  http.get(`${root}/sessions/:id`, async ({ params }) => {
    const failed = await before()
    if (failed) return failed
    const rows = events.filter((e) => e.session_id === params.id)
    if (!rows.length) return error(404, 'Session not found')
    return response({
      session_id: params.id,
      start_time: rows[0]!.event_time,
      end_time: rows.at(-1)!.event_time,
      event_count: rows.length,
      events: rows.map(({ session_id: _session, brand_id: _brand, ...e }) => e),
    })
  }),
  ...(['products', 'brands', 'categories'] as RankingKind[]).map((kind) =>
    http.get(`${root}/analytics/top-${kind}`, async ({ request }) => {
      const failed = await before()
      if (failed) return failed
      const limit = intParam(new URL(request.url), 'limit', 10, 50)
      return limit
        ? response({ limit, items: ranking(kind).slice(0, limit) })
        : error(422, 'Request validation failed')
    }),
  ),
  http.get(`${root}/analytics/conversion`, async () => (await before()) ?? response(conversion)),
]
