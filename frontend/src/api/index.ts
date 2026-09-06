import { request } from './client'
import type {
  Overview,
  Page,
  Product,
  ProductDetail,
  ProductStatistics,
  UserEvents,
  SessionDetail,
  Ranking,
  RankingKind,
  Conversion,
} from '../types'
export const api = {
  overview: (signal?: AbortSignal) => request<Overview>('/dashboard/overview', {}, signal),
  products: (page: number, size: number, signal?: AbortSignal) =>
    request<Page<Product>>('/products', { page, page_size: size }, signal),
  product: (id: string, signal?: AbortSignal) =>
    request<ProductDetail>(`/products/${encodeURIComponent(id)}`, {}, signal),
  statistics: (id: string, signal?: AbortSignal) =>
    request<ProductStatistics>(`/products/${encodeURIComponent(id)}/statistics`, {}, signal),
  userEvents: (id: string, page: number, size: number, type: string, signal?: AbortSignal) =>
    request<UserEvents>(
      `/users/${encodeURIComponent(id)}/events`,
      { page, page_size: size, event_type: type || undefined },
      signal,
    ),
  session: (id: string, signal?: AbortSignal) =>
    request<SessionDetail>(`/sessions/${encodeURIComponent(id)}`, {}, signal),
  ranking: (kind: RankingKind, limit: number, signal?: AbortSignal) =>
    request<Ranking>(`/analytics/top-${kind}`, { limit }, signal),
  conversion: (signal?: AbortSignal) => request<Conversion>('/analytics/conversion', {}, signal),
}
