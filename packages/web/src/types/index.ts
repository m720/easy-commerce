// Shared primitives
export type UUID = string
export type Decimal = string  // e.g. "29.99"
export type ISODate = string  // e.g. "2026-03-05T12:00:00Z"

// Enums
export type UserRole = "user" | "admin"
export type OrderStatus = "pending" | "processing" | "shipped" | "delivered" | "cancelled" | "returned"
export type CouponType = "percent" | "fixed"
export type ReturnStatus = "pending" | "approved" | "rejected"

// Pagination
export type PaginationParams = { skip?: number; limit?: number }
export type ApiError = { detail: string }

// Auth
export interface User {
  id: UUID
  email: string
  full_name: string
  role: UserRole
  is_active: boolean
  created_at: ISODate
}

export interface TokenResponse {
  access_token: string
  token_type: "bearer"
}

// Category
export interface Category {
  id: number
  name: string
  slug: string
  description: string | null
}

// Tag
export interface Tag {
  id: number
  name: string
  slug: string
}

// Product
export interface ProductVariant {
  id: UUID
  product_id: UUID
  name: string
  sku: string
  price: Decimal
  stock_quantity: number
  low_stock_threshold: number
}

export interface ProductImage {
  id: UUID
  product_id: UUID
  s3_key: string
  is_primary: boolean
  sort_order: number
  url: string | null
}

export interface Product {
  id: UUID
  name: string
  description: string | null
  base_price: Decimal
  category_id: number | null
  is_featured: boolean
  is_active: boolean
  created_at: ISODate
  category: Category | null
  tags: Tag[]
  variants: ProductVariant[]
  images: ProductImage[]
}

// Review
export interface Review {
  id: UUID
  user_id: UUID
  product_id: UUID
  rating: number
  comment: string | null
  is_approved: boolean
  created_at: ISODate
}

// Wishlist
export interface WishlistItem {
  id: UUID
  product_id: UUID
  product: Product
}

export interface Wishlist {
  id: UUID
  items: WishlistItem[]
}

// Address
export interface Address {
  id: UUID
  user_id: UUID
  label: string | null
  street: string
  city: string
  state: string | null
  country: string
  postal_code: string
  is_default: boolean
}

// Coupon
export interface Coupon {
  id: UUID
  code: string
  type: CouponType
  value: Decimal
  min_order_amount: Decimal | null
  max_uses: number | null
  used_count: number
  expires_at: ISODate | null
  is_active: boolean
}

export interface CouponValidateResponse {
  valid: boolean
  discount_amount: Decimal
  coupon: Coupon
}

// Cart
export interface CartItem {
  id: UUID
  variant_id: UUID
  quantity: number
  variant: ProductVariant
  in_stock: boolean
}

export interface Cart {
  id: UUID
  items: CartItem[]
  subtotal: Decimal
}

// Order
export interface OrderItem {
  id: UUID
  variant_id: UUID | null
  product_name: string
  variant_name: string
  unit_price: Decimal
  quantity: number
  subtotal: Decimal
}

export interface Order {
  id: UUID
  user_id: UUID | null
  status: OrderStatus
  total_amount: Decimal
  discount_amount: Decimal
  coupon_id: UUID | null
  shipping_address_snapshot: Address | null
  created_at: ISODate
  items: OrderItem[]
}

// Return Request
export interface ReturnRequestItem {
  id: UUID
  order_item_id: UUID
  quantity: number
}

export interface ReturnRequest {
  id: UUID
  order_id: UUID
  user_id: UUID
  reason: string
  status: ReturnStatus
  admin_notes: string | null
  created_at: ISODate
  items: ReturnRequestItem[]
}

// Analytics
export interface RevenueStat { total_revenue: number }
export interface OrderStatusStat { status: OrderStatus; count: number }
export interface TopProductStat { product_name: string; total_sold: number; total_revenue: number }
export interface TopVariantStat { variant_name: string; total_sold: number }
export interface UserStat { total_users: number; new_users_in_period: number }
export interface AovStat { average_order_value: number }
export interface CouponStat { code: string; used_count: number; max_uses: number | null }
export interface LowStockItem { variant_id: UUID; sku: string; name: string; stock_quantity: number; low_stock_threshold: number }
export interface UserActivitySummary {
  user: User
  total_orders: number
  total_reviews: number
  wishlist_items: number
}

export interface AnalyticsSummary {
  total_revenue: number
  orders_by_status: OrderStatusStat[]
  average_order_value: number
  total_users: number
  new_users_in_period: number
}
