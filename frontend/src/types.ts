export type EventType = 'view' | 'cart' | 'purchase'
export interface Overview {
  total_users: number
  total_products: number
  total_categories: number
  total_brands: number
  total_events: number
  total_views: number
  total_carts: number
  total_purchases: number
}
export interface Page<T> {
  page: number
  page_size: number
  total: number
  items: T[]
}
export interface Product {
  product_id: string
  category_id: string
  category_code: string | null
}
export interface Brand {
  brand_id: string
  brand_name: string
}
export interface ProductDetail extends Product {
  brands: Brand[]
}
export interface ProductStatistics extends Product {
  event_count: number
  view_count: number
  cart_count: number
  purchase_count: number
  sales_amount: number
}
export interface BehaviorEvent {
  event_id: string
  event_time: string
  event_type: EventType
  product_id: string
  price: number
  brand_name: string | null
  category_code: string | null
}
export interface UserEvent extends BehaviorEvent {
  session_id: string | null
}
export interface SessionEvent extends BehaviorEvent {
  user_id: string
}
export interface UserEvents extends Page<UserEvent> {
  user_id: string
}
export interface SessionDetail {
  session_id: string
  start_time: string
  end_time: string
  event_count: number
  events: SessionEvent[]
}
export type RankingKind = 'products' | 'brands' | 'categories'
export interface RankItem {
  product_id?: string
  brand_id?: string
  brand_name?: string
  category_id?: string
  category_code?: string | null
  event_count: number
  purchase_count: number
  sales_amount: number
}
export interface Ranking {
  limit: number
  items: RankItem[]
}
export interface Conversion {
  total_sessions: number
  view_sessions: number
  cart_sessions: number
  purchase_sessions: number
  view_cart_sessions: number
  cart_purchase_sessions: number
  view_purchase_sessions: number
  view_to_cart_rate: number
  cart_to_purchase_rate: number
  view_to_purchase_rate: number
}
