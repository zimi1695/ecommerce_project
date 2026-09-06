import type { EventType } from './types'
export const number = (value: number) => new Intl.NumberFormat('zh-CN').format(value)
export const money = (value: number) =>
  new Intl.NumberFormat('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(
    value,
  )
export const percent = (value: number) => `${(value * 100).toFixed(2)}%`
export const eventNames: Record<EventType, string> = {
  view: '浏览',
  cart: '加购',
  purchase: '购买',
}
export function utc(value: string) {
  return value
    .replace('T', ' ')
    .replace(/(?:Z|\+00:00)$/, '')
    .slice(0, 19)
}
export function positiveInt(value: unknown, fallback: number, max = Number.MAX_SAFE_INTEGER) {
  const n = Number(value)
  return Number.isSafeInteger(n) && n > 0 && n <= max ? n : fallback
}
export const validId = (value: string) => /^\d{1,20}$/.test(value) && /[1-9]/.test(value)
export const DEMO = {
  product: '1000978',
  user: '564068124',
  session: '4488e77a-9901-4c4b-b162-47a224ceab51',
  category: '2053013555631882655',
}
