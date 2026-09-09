import type {
  BehaviorEvent,
  Brand,
  Conversion,
  ProductDetail,
  ProductStatistics,
  RankingKind,
  RankItem,
} from '../types'
import { DEMO } from '../utils'

// ------------------------------------------------------------
// 合成数据按真实口径构造（对齐 2019-Nov 前 60 ETL batch 的分布）：
//   事件类型   view ≈ 96% / cart ≈ 1.4% / purchase ≈ 2.4%（真实 97.2 / 1.25 / 1.5）
//   Session 漏斗  view→cart 3.68% / cart→purchase 54% / view→purchase 5.82%
//   时间全月分布、价格 0~2574 长尾、session 平均 4~5 条事件
// 固定演示对象对齐真实库记录，两种模式切换页面数字一致：
//   商品 1000978：22 条 view、0 加购 0 购买（真实 event_count=22）
//   用户 564068124：781 条事件、其中 265 条 purchase（真实 total=781 / purchase=265）
//   Session 4488e77a…：504 条 view、2019-11-01 03:38~07:15（真实画像）
// 生成全程确定性（无 Math.random），测试与快照稳定。
// ------------------------------------------------------------

function rng(seed: number) {
  let a = seed >>> 0
  return () => {
    a = (a + 0x6d2b79f5) | 0
    let t = Math.imul(a ^ (a >>> 15), 1 | a)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
const rand = rng(2019_1101)

const pad2 = (n: number) => String(n).padStart(2, '0')
const MONTH_START = Date.UTC(2019, 10, 1)
// 与真实 API 一致的时间格式：'YYYY-MM-DDTHH:MM:SS'（UTC，无毫秒）
const stamp = (monthSeconds: number) => {
  const d = new Date(MONTH_START + Math.floor(monthSeconds) * 1000)
  return `${d.getUTCFullYear()}-${pad2(d.getUTCMonth() + 1)}-${pad2(d.getUTCDate())}T${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())}:${pad2(d.getUTCSeconds())}`
}
const at = (day: number, hour: number, minute: number, second = 0) =>
  (day - 1) * 86_400 + hour * 3_600 + minute * 60 + second
function uuid(seed: number) {
  const r = rng(seed)
  const hex = (n: number) =>
    Array.from({ length: n }, () => '0123456789abcdef'[Math.floor(r() * 16)]!).join('')
  return `${hex(8)}-${hex(4)}-4${hex(3)}-8${hex(3)}-${hex(12)}`
}

// ---------- 商品 ----------
// 类别：1/6 无类别名称（真实 category_code 缺失 32%，演示抽样取低配）
const categoryDefs: ReadonlyArray<readonly [string, string | null]> = [
  [DEMO.category, 'electronics.smartphone'],
  ['2053013555631882656', null],
  ['2053013554415534427', 'electronics.audio.headphone'],
  ['2053013558920217191', 'computers.notebook'],
  ['2053013554995305161', 'electronics.camera'],
  ['2053013556160365401', 'electronics.video.tv'],
]
const brandList: Brand[] = [
  { brand_id: '9', brand_name: 'samsung' },
  { brand_id: '12', brand_name: 'apple' },
  { brand_id: '25', brand_name: 'xiaomi' },
  { brand_id: '31', brand_name: 'lenovo' },
  { brand_id: '46', brand_name: 'lg' },
  { brand_id: '58', brand_name: 'huawei' },
  { brand_id: '71', brand_name: 'asus' },
  { brand_id: '83', brand_name: 'acer' },
  { brand_id: '97', brand_name: 'oppo' },
  { brand_id: '112', brand_name: 'bosch' },
  { brand_id: '128', brand_name: 'siemens' },
  { brand_id: '145', brand_name: 'indesit' },
]
const conflictBrands: Brand[] = [
  { brand_id: '201', brand_name: 'bugati' },
  { brand_id: '202', brand_name: 'bugatti' },
]

interface Spec {
  id: string
  category: readonly [string, string | null]
  brands: Brand[]
  base: number
  hasEvents: boolean
}
const specs: Spec[] = []
for (let i = 0; i < 119; i++) {
  const brands =
    i === 0
      ? [brandList[0]!, brandList[3]!] // 演示多品牌桥表（product_brands）
      : i === 42
        ? conflictBrands // 真实数据中的品牌冲突样例
        : i % 7 === 3
          ? [] // ~14% 无品牌（真实 brand 缺失 13.7%）
          : [brandList[(i * 5 + 7) % 12]!]
  const base = rand() < 0.02 ? 0 : Number((3 + Math.pow(rand(), 1.8) * 2400).toFixed(2))
  specs.push({
    id: String(1000978 + i),
    category: categoryDefs[i % 6]!,
    brands,
    base,
    hasEvents: i !== 35, // 1001013：零事件（真实空统计）
  })
}
// 演示用户的 bulk 购买商品（真实：1005115 / apple / smartphone / 921.0）
specs.push({
  id: '1005115',
  category: categoryDefs[0]!,
  brands: [brandList[1]!],
  base: 921.0,
  hasEvents: true,
})
// 末位零事件商品
specs.push({
  id: '1001097',
  category: categoryDefs[5]!,
  brands: [brandList[10]!],
  base: 189.0,
  hasEvents: false,
})

export const products: ProductDetail[] = specs.map(({ id, category, brands }) => ({
  product_id: id,
  category_id: category[0],
  category_code: category[1],
  brands,
}))

// ---------- 事件 ----------
export interface FixtureEvent extends BehaviorEvent {
  user_id: string
  session_id: string | null
  brand_id: string | null
}

const userPool = Array.from({ length: 4600 }, (_, i) => String(500_000_000 + i * 977))
const DEMO_SESSION_USER = '537972582'
const DEMO_SESSION_USER_2 = '538115720' // 真实数据存在跨用户 Session（591 个），演示对象保留双用户
const PURCHASE_SESSION = '93fe16a5-1e25-468c-b569-446913a84b12'
const demoSpec = specs[0]!
const bulkSpec = specs[119]!

// 幂律商品池（排除零事件商品；演示商品事件单独精确注入）
const pool = specs.filter((s, i) => s.hasEvents && i !== 0)
const weights = pool.map((_, i) => 1 / (1 + i * 0.08))
const totalWeight = weights.reduce((a, b) => a + b, 0)
const pickAny = (r: () => number) => {
  let x = r() * totalWeight
  for (let i = 0; i < pool.length; i++) {
    x -= weights[i]!
    if (x <= 0) return pool[i]!
  }
  return pool.at(-1)!
}
const brandless = pool.filter((s) => s.brands.length === 0)
const pickBrandless = (r: () => number) => brandless[Math.floor(r() * brandless.length)]!

interface Counts {
  view: number
  cart: number
  purchase: number
}
type Price = (spec: Spec, r: () => number) => number
const jitter = (spec: Spec, r: () => number) => Number((spec.base * (0.92 + r() * 0.16)).toFixed(2))
const bulkPrice = (spec: Spec, r: () => number) => (spec.id === '1005115' ? 921.0 : jitter(spec, r))

let eventSeq = 0
const allEvents: FixtureEvent[] = []
function emit(opts: {
  user: string
  session: string | null
  start: number
  span: number
  counts: Counts
  product: (r: () => number) => Spec
  price?: Price
}) {
  const seq: Array<keyof Counts> = [
    ...Array.from({ length: opts.counts.view }, () => 'view' as const),
    ...Array.from({ length: opts.counts.cart }, () => 'cart' as const),
    ...Array.from({ length: opts.counts.purchase }, () => 'purchase' as const),
  ]
  const total = seq.length
  const price = opts.price ?? jitter
  seq.forEach((type, idx) => {
    const spec = opts.product(rand)
    const brand = spec.brands[Math.floor(rand() * spec.brands.length)] ?? null
    const t = opts.start + (opts.span * idx) / total + rand() * 20
    allEvents.push({
      event_id: String(++eventSeq),
      event_time: stamp(t),
      event_type: type,
      product_id: spec.id,
      price: price(spec, rand),
      brand_name: brand?.brand_name ?? null,
      brand_id: brand?.brand_id ?? null,
      category_code: spec.category[1],
      user_id: opts.user,
      session_id: opts.session,
    })
  })
}

// ---- 演示 Session 4488e77a（真实画像：11-01 03:38~07:15，504 条 view）----
const demoSessionStart = at(1, 3, 38)
const demoSessionSpan = at(1, 7, 15, 37) - demoSessionStart
emit({
  user: DEMO_SESSION_USER,
  session: DEMO.session,
  start: demoSessionStart,
  span: demoSessionSpan * 0.98,
  counts: { view: 480, cart: 0, purchase: 0 },
  product: (r) => (r() < 0.76 ? pickBrandless(r) : pickAny(r)), // 真实：76% 事件无品牌
})
emit({
  user: DEMO_SESSION_USER_2,
  session: DEMO.session,
  start: demoSessionStart + 600,
  span: demoSessionSpan * 0.9,
  counts: { view: 24, cart: 0, purchase: 0 },
  product: (r) => pickAny(r),
})

// ---- 演示用户 564068124（真实：781 条事件 / 265 购买，bulk 购买 1005115@921.0）----
emit({
  user: DEMO.user,
  session: PURCHASE_SESSION,
  start: at(4, 10, 27),
  span: 48 * 60,
  counts: { view: 18, cart: 4, purchase: 18 },
  product: (r) => (r() < 0.9 ? bulkSpec : pickAny(r)),
  price: bulkPrice,
})
const restPurchases = [31, 31, 31, 31, 31, 31, 31, 30] // 247
const sessionCarts = [2, 2, 2, 2, 1, 1, 1, 1] // 12
restPurchases.forEach((p, k) => {
  emit({
    user: DEMO.user,
    session: uuid(7000 + k),
    start: at(1 + k * 3, 8 + (k % 12), (k * 17) % 60),
    span: 40 * 60,
    counts: { view: 12, cart: sessionCarts[k]!, purchase: p },
    product: (r) => (r() < 0.85 ? bulkSpec : pickAny(r)),
    price: bulkPrice,
  })
})
const demoUserViews = [97, 97, 96, 96] // 386
demoUserViews.forEach((v, k) => {
  emit({
    user: DEMO.user,
    session: uuid(7100 + k),
    start: at(2 + k * 6, 20, k * 13),
    span: 3 * 3600,
    counts: { view: v, cart: 0, purchase: 0 },
    product: (r) => pickAny(r),
  })
})

// ---- 背景会话 9985 个，配比对齐真实 Session 漏斗 ----
// 纯浏览 9244 / 仅加购 168 / 仅购买 382 / 加购+购买 191
for (let s = 0; s < 9985; s++) {
  const start = at(1 + Math.floor(rand() * 27), Math.floor(rand() * 24), Math.floor(rand() * 60))
  const user = userPool[s % 4600]!
  const session = uuid(20_000 + s)
  if (s < 168) {
    emit({
      user,
      session,
      start,
      span: 30 * 60,
      counts: { view: 3 + Math.floor(rand() * 4), cart: 1 + Math.floor(rand() * 2), purchase: 0 },
      product: pickAny,
    })
  } else if (s < 550) {
    emit({
      user,
      session,
      start,
      span: 25 * 60,
      counts: { view: 2 + Math.floor(rand() * 5), cart: 0, purchase: 1 + Math.floor(rand() * 2) },
      product: pickAny,
    })
  } else if (s < 741) {
    emit({
      user,
      session,
      start,
      span: 40 * 60,
      counts: {
        view: 3 + Math.floor(rand() * 5),
        cart: 1 + Math.floor(rand() * 2),
        purchase: 1 + Math.floor(rand() * 2),
      },
      product: pickAny,
    })
  } else {
    emit({
      user,
      session,
      start,
      span: 2 * 3600,
      counts: { view: 1 + Math.floor(rand() * 8), cart: 0, purchase: 0 },
      product: pickAny,
    })
  }
}

// ---- 演示商品 1000978（真实：22 条 view / 0 加购 / 0 购买）----
for (let k = 0; k < 22; k++) {
  const brand = demoSpec.brands[k % 2]!
  allEvents.push({
    event_id: String(++eventSeq),
    event_time: stamp(at(2 + (k % 24), 6 + (k % 14), (k * 7) % 60)),
    event_type: 'view',
    product_id: demoSpec.id,
    price: jitter(demoSpec, rand),
    brand_name: brand.brand_name,
    brand_id: brand.brand_id,
    category_code: demoSpec.category[1],
    user_id: userPool[(k * 61) % 4600]!,
    session_id: uuid(30_000 + k),
  })
}

// ---- 无 Session 事件（真实 10/6750 万，象征性保留）----
for (let k = 0; k < 5; k++) {
  emit({
    user: userPool[(3000 + k * 37) % 4600]!,
    session: null,
    start: at(3 + k * 5, 12, k * 11),
    span: 300,
    counts: { view: 1, cart: 0, purchase: 0 },
    product: pickAny,
  })
}

export const events: FixtureEvent[] = allEvents.sort(
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
  total_categories: categoryDefs.length,
  total_brands: brandList.length + conflictBrands.length,
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
        ? [...brandList, ...conflictBrands].map((b) => ({
            ...b,
            ...summarize(events.filter((e) => e.brand_id === b.brand_id)),
          }))
        : categoryDefs.map(([category_id, category_code]) => ({
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
const flags = [...new Set(events.map((e) => e.session_id))]
  .filter((id): id is string => id !== null)
  .map((id) => new Set(events.filter((e) => e.session_id === id).map((e) => e.event_type)))
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
