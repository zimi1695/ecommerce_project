import type {
  BehaviorEvent,
  ProductDetail,
  ProductStatistics,
  RankingKind,
  RankItem,
  Conversion,
} from '../types'
import { DEMO } from '../utils'

const categories = [
  [DEMO.category, 'electronics.smartphone'],
  ['2053013554415534427', 'electronics.audio.headphone'],
  ['2053013558920217191', 'computers.notebook'],
  ['2053013555631882656', null],
  ['2053013554658804075', 'appliances.kitchen.refrigerators'],
  ['2053013556160365401', 'electronics.video.tv'],
] as const
const brands = [
  { brand_id: '9', brand_name: 'samsung' },
  { brand_id: '12', brand_name: 'apple' },
  { brand_id: '25', brand_name: 'xiaomi' },
  { brand_id: '31', brand_name: 'lenovo' },
]
export const products: ProductDetail[] = Array.from({ length: 36 }, (_, i) => ({
  product_id: String(Number(DEMO.product) + i),
  category_id: categories[i % 6]![0],
  category_code: categories[i % 6]![1],
  brands: i === 0 ? [brands[0]!, brands[3]!] : i % 7 === 0 ? [] : [brands[i % 4]!],
}))
export interface FixtureEvent extends BehaviorEvent {
  user_id: string
  session_id: string | null
  brand_id: string | null
}
export const sessionIds = Array.from({ length: 72 }, (_, i) =>
  i === 0 ? DEMO.session : `00000000-0000-4000-8000-${String(i).padStart(12, '0')}`,
)
export const events: FixtureEvent[] = products
  .flatMap((product, i) =>
    Array.from({ length: i === 35 ? 0 : 72 + (36 - i) * 17 }, (_, j): FixtureEvent => {
      const brand = product.brands[j % Math.max(product.brands.length, 1)]
      return {
        event_id: String(i * 1000 + j + 1),
        event_time: new Date(Date.UTC(2019, 10, 1, 0, i * 7 + j)).toISOString().replace('Z', ''),
        event_type: j % 17 === 0 ? 'purchase' : j % 5 === 0 ? 'cart' : 'view',
        product_id: product.product_id,
        price: Number((149.99 + i * 21.3 + (j % 3) * 5).toFixed(2)),
        user_id: String(Number(DEMO.user) + (j % 24) + (i % 5 === 0 && j % 72 === 0 ? 1 : 0)),
        session_id: j % 101 === 100 ? null : sessionIds[j % 72]!,
        brand_name: brand?.brand_name ?? null,
        brand_id: brand?.brand_id ?? null,
        category_code: product.category_code,
      }
    }),
  )
  .sort(
    (a, b) => a.event_time.localeCompare(b.event_time) || Number(a.event_id) - Number(b.event_id),
  )

export function summarize(rows: FixtureEvent[]) {
  return {
    event_count: rows.length,
    view_count: rows.filter((e) => e.event_type === 'view').length,
    cart_count: rows.filter((e) => e.event_type === 'cart').length,
    purchase_count: rows.filter((e) => e.event_type === 'purchase').length,
    sales_amount: Number(
      rows
        .filter((e) => e.event_type === 'purchase')
        .reduce((sum, e) => sum + e.price, 0)
        .toFixed(2),
    ),
  }
}
export const productStatistics: ProductStatistics[] = products.map(
  ({ brands: _brands, ...product }) => ({
    ...product,
    ...summarize(events.filter((e) => e.product_id === product.product_id)),
  }),
)
const totals = summarize(events)
export const overview = {
  total_users: new Set(events.map((e) => e.user_id)).size,
  total_products: products.length,
  total_categories: categories.length,
  total_brands: brands.length,
  total_events: totals.event_count,
  total_views: totals.view_count,
  total_carts: totals.cart_count,
  total_purchases: totals.purchase_count,
}
export function ranking(kind: RankingKind): RankItem[] {
  const rows =
    kind === 'products'
      ? products.map((p) => ({
          product_id: p.product_id,
          ...summarize(events.filter((e) => e.product_id === p.product_id)),
        }))
      : kind === 'brands'
        ? brands.map((b) => ({
            ...b,
            ...summarize(events.filter((e) => e.brand_id === b.brand_id)),
          }))
        : categories.map(([category_id, category_code]) => ({
            category_id,
            category_code,
            ...summarize(
              events.filter(
                (e) =>
                  products.find((p) => p.product_id === e.product_id)?.category_id === category_id,
              ),
            ),
          }))
  return rows
    .filter((row) => row.event_count > 0)
    .sort((a, b) => b.event_count - a.event_count)
    .map((row) => {
      const { view_count: _view, cart_count: _cart, ...item } = row
      return item
    })
}
const flags = sessionIds.map(
  (id) => new Set(events.filter((e) => e.session_id === id).map((e) => e.event_type)),
)
const count = (...types: string[]) =>
  flags.filter((f) => types.every((type) => f.has(type as FixtureEvent['event_type']))).length
export const conversion: Conversion = {
  total_sessions: flags.filter((f) => f.size).length,
  view_sessions: count('view'),
  cart_sessions: count('cart'),
  purchase_sessions: count('purchase'),
  view_cart_sessions: count('view', 'cart'),
  cart_purchase_sessions: count('cart', 'purchase'),
  view_purchase_sessions: count('view', 'purchase'),
  view_to_cart_rate: count('view', 'cart') / count('view'),
  cart_to_purchase_rate: count('cart', 'purchase') / count('cart'),
  view_to_purchase_rate: count('view', 'purchase') / count('view'),
}
