# Ecommerce API — Frontend Integration Reference

## Base URL

```
http://localhost:8000/api/v1
```

Swagger UI: `http://localhost:8000/docs`

---

## Authentication

All protected endpoints require a **Bearer token** in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain the token from `POST /auth/login`. Store it (e.g. `localStorage`) and attach it to every subsequent request.

### Roles
| Role | Access |
|---|---|
| `user` | Own profile, cart, orders, wishlist, addresses, reviews |
| `admin` | Everything + user management, product/coupon CRUD, analytics |

---

## Pagination

All list endpoints accept:

| Query Param | Default | Max |
|---|---|---|
| `skip` | `0` | — |
| `limit` | `20` | `100` |

Example: `GET /products?skip=20&limit=20`

---

## Enums

```ts
type UserRole     = "user" | "admin"
type OrderStatus  = "pending" | "processing" | "shipped" | "delivered" | "cancelled" | "returned"
type CouponType   = "percent" | "fixed"
type ReturnStatus = "pending" | "approved" | "rejected"
```

---

## Types

```ts
// Shared primitives
type UUID     = string  // "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
type Decimal  = string  // e.g. "29.99" — use parseFloat() or a money lib
type ISODate  = string  // e.g. "2026-03-05T12:00:00Z"

// ─── Auth ─────────────────────────────────────────────────────────────────────

interface User {
  id:         UUID
  email:      string
  full_name:  string
  role:       UserRole
  is_active:  boolean
  created_at: ISODate
}

interface TokenResponse {
  access_token: string
  token_type:   "bearer"
}

// ─── Category ─────────────────────────────────────────────────────────────────

interface Category {
  id:          number
  name:        string
  slug:        string
  description: string | null
}

// ─── Tag ──────────────────────────────────────────────────────────────────────

interface Tag {
  id:   number
  name: string
  slug: string
}

// ─── Product ──────────────────────────────────────────────────────────────────

interface ProductVariant {
  id:                  UUID
  product_id:          UUID
  name:                string   // e.g. "Red / L"
  sku:                 string
  price:               Decimal
  stock_quantity:      number
  low_stock_threshold: number
}

interface ProductImage {
  id:         UUID
  product_id: UUID
  s3_key:     string
  is_primary: boolean
  sort_order: number
  url:        string | null   // pre-signed S3 read URL; may expire
}

interface Product {
  id:          UUID
  name:        string
  description: string | null
  base_price:  Decimal
  category_id: number | null
  is_featured: boolean
  is_active:   boolean
  created_at:  ISODate
  category:    Category | null
  tags:        Tag[]
  variants:    ProductVariant[]
  images:      ProductImage[]
}

// ─── Review ───────────────────────────────────────────────────────────────────

interface Review {
  id:          UUID
  user_id:     UUID
  product_id:  UUID
  rating:      number   // 1–5
  comment:     string | null
  is_approved: boolean
  created_at:  ISODate
}

// ─── Wishlist ─────────────────────────────────────────────────────────────────

interface WishlistItem {
  id:         UUID
  product_id: UUID
  product:    Product
}

interface Wishlist {
  id:    UUID
  items: WishlistItem[]
}

// ─── Address ──────────────────────────────────────────────────────────────────

interface Address {
  id:          UUID
  user_id:     UUID
  label:       string | null
  street:      string
  city:        string
  state:       string | null
  country:     string
  postal_code: string
  is_default:  boolean
}

// ─── Coupon ───────────────────────────────────────────────────────────────────

interface Coupon {
  id:               UUID
  code:             string
  type:             CouponType
  value:            Decimal
  min_order_amount: Decimal | null
  max_uses:         number | null
  used_count:       number
  expires_at:       ISODate | null
  is_active:        boolean
}

interface CouponValidateResponse {
  valid:           boolean
  discount_amount: Decimal
  coupon:          Coupon
}

// ─── Cart ─────────────────────────────────────────────────────────────────────

interface CartItem {
  id:         UUID
  variant_id: UUID
  quantity:   number
  variant:    ProductVariant
  in_stock:   boolean
}

interface Cart {
  id:       UUID
  items:    CartItem[]
  subtotal: Decimal
}

// ─── Order ────────────────────────────────────────────────────────────────────

interface OrderItem {
  id:           UUID
  variant_id:   UUID | null
  product_name: string
  variant_name: string
  unit_price:   Decimal
  quantity:     number
  subtotal:     Decimal
}

interface Order {
  id:                        UUID
  user_id:                   UUID | null
  status:                    OrderStatus
  total_amount:              Decimal
  discount_amount:           Decimal
  coupon_id:                 UUID | null
  shipping_address_snapshot: Address | null
  created_at:                ISODate
  items:                     OrderItem[]
}

// ─── Return Request ───────────────────────────────────────────────────────────

interface ReturnRequestItem {
  id:            UUID
  order_item_id: UUID
  quantity:      number
}

interface ReturnRequest {
  id:          UUID
  order_id:    UUID
  user_id:     UUID
  reason:      string
  status:      ReturnStatus
  admin_notes: string | null
  created_at:  ISODate
  items:       ReturnRequestItem[]
}

// ─── Analytics ────────────────────────────────────────────────────────────────

interface RevenueStat       { total_revenue: number }
interface OrderStatusStat   { status: OrderStatus; count: number }
interface TopProductStat    { product_name: string; total_sold: number; total_revenue: number }
interface TopVariantStat    { variant_name: string; total_sold: number }
interface UserStat          { total_users: number; new_users_in_period: number }
interface AovStat           { average_order_value: number }
interface CouponStat        { code: string; used_count: number; max_uses: number | null }
interface LowStockItem      { variant_id: UUID; sku: string; name: string; stock_quantity: number; low_stock_threshold: number }
interface UserActivitySummary {
  user:           User
  total_orders:   number
  total_reviews:  number
  wishlist_items: number
}
```

---

## Endpoints

### Auth

#### `POST /auth/register` — Register
```ts
// Request
{ email: string; full_name: string; password: string }

// Response 201
User
```

#### `POST /auth/login` — Login
```ts
// Request
{ email: string; password: string }

// Response 200
TokenResponse
```

#### `GET /auth/me` — Get own profile  🔒
```ts
// Response 200
User
```

#### `PUT /auth/me` — Update own profile  🔒
```ts
// Request (all optional)
{ full_name?: string; email?: string }

// Response 200
User
```

#### `PUT /auth/me/password` — Change password  🔒
```ts
// Request
{ current_password: string; new_password: string }

// Response 204  (no body)
```

---

### Users  🔒 Admin

#### `GET /users` — List users
```ts
// Query: skip, limit
// Response 200
User[]
```

#### `GET /users/:id` — Get user
```ts
// Response 200
User
```

#### `PATCH /users/:id/activate` — Activate account
```ts
// Response 200
User
```

#### `PATCH /users/:id/deactivate` — Deactivate account
```ts
// Response 200
User
```

#### `GET /users/:id/activity` — User activity summary
```ts
// Response 200
UserActivitySummary
```

---

### Categories

#### `GET /categories` — List  🌐
```ts
// Response 200
Category[]
```

#### `GET /categories/:id` — Get  🌐
```ts
// Response 200
Category
```

#### `GET /categories/:id/products` — Products in category  🌐
```ts
// Query: skip, limit
// Response 200
Product[]
```

#### `POST /categories` — Create  🔒 Admin
```ts
// Request
{ name: string; slug: string; description?: string }

// Response 201
Category
```

#### `PUT /categories/:id` — Update  🔒 Admin
```ts
// Request (all optional)
{ name?: string; slug?: string; description?: string }

// Response 200
Category
```

#### `DELETE /categories/:id` — Delete  🔒 Admin
```ts
// Response 204
```

---

### Tags

#### `GET /tags` — List  🌐
```ts
// Response 200
Tag[]
```

#### `POST /tags` — Create  🔒 Admin
```ts
// Request
{ name: string; slug: string }

// Response 201
Tag
```

#### `PUT /tags/:id` — Update  🔒 Admin
```ts
// Request (all optional)
{ name?: string; slug?: string }

// Response 200
Tag
```

#### `DELETE /tags/:id` — Delete  🔒 Admin
```ts
// Response 204
```

---

### Products

#### `GET /products` — List & search  🌐
```ts
// Query params (all optional)
search:      string    // case-insensitive name search
category_id: number
tag_id:      number
min_price:   number
max_price:   number
is_featured: boolean
skip:        number
limit:       number

// Response 200
Product[]
```

#### `GET /products/featured` — Featured products  🌐
```ts
// Query: skip, limit
// Response 200
Product[]
```

#### `GET /products/:id` — Get product  🌐
```ts
// Response 200
Product
```

#### `POST /products` — Create  🔒 Admin
```ts
// Request
{
  name:        string
  description?: string
  base_price:  string      // e.g. "29.99"
  category_id?: number
  is_featured?: boolean    // default false
  tag_ids?:    number[]    // default []
}

// Response 201
Product
```

#### `PUT /products/:id` — Update  🔒 Admin
```ts
// Request (all optional)
{
  name?:        string
  description?: string
  base_price?:  string
  category_id?: number
  is_featured?: boolean
  is_active?:   boolean
  tag_ids?:     number[]
}

// Response 200
Product
```

#### `DELETE /products/:id` — Soft-delete  🔒 Admin
```ts
// Response 204
```

#### `PATCH /products/:id/feature` — Toggle featured  🔒 Admin
```ts
// Response 200
Product
```

#### `POST /products/bulk-activate` — Bulk activate  🔒 Admin
```ts
// Request
{ product_ids: UUID[] }

// Response 200
{ updated: number }
```

#### `POST /products/bulk-deactivate` — Bulk deactivate  🔒 Admin
```ts
// Request
{ product_ids: UUID[] }

// Response 200
{ updated: number }
```

---

### Product Variants

#### `GET /products/:id/variants` — List  🌐
```ts
// Response 200
ProductVariant[]
```

#### `POST /products/:id/variants` — Create  🔒 Admin
```ts
// Request
{
  name:                 string
  sku:                  string
  price:                string
  stock_quantity?:      number   // default 0
  low_stock_threshold?: number   // default 5
}

// Response 201
ProductVariant
```

#### `PUT /products/:id/variants/:variantId` — Update  🔒 Admin
```ts
// Request (all optional)
{ name?: string; sku?: string; price?: string; stock_quantity?: number; low_stock_threshold?: number }

// Response 200
ProductVariant
```

#### `DELETE /products/:id/variants/:variantId` — Delete  🔒 Admin
```ts
// Response 204
```

---

### Product Images

#### `GET /products/:id/images` — List  🌐
```ts
// Response 200
ProductImage[]   // each has a pre-signed `url` field
```

#### `POST /products/:id/images/upload-url` — Get S3 upload URL  🔒 Admin

Two-step flow: first get the upload URL, then PUT the file to S3, then confirm.

```ts
// Step 1 — Request upload URL
// POST /products/:id/images/upload-url
{ filename: string; content_type?: string }   // content_type default "image/jpeg"

// Response 200
{ upload_url: string; s3_key: string }

// Step 2 — PUT the binary file directly to S3
fetch(upload_url, { method: "PUT", body: fileBlob, headers: { "Content-Type": content_type } })

// Step 3 — Confirm upload
// POST /products/:id/images
{ s3_key: string; is_primary?: boolean; sort_order?: number }

// Response 201
ProductImage
```

#### `PATCH /products/:id/images/:imageId/primary` — Set primary  🔒 Admin
```ts
// Response 200
ProductImage
```

#### `DELETE /products/:id/images/:imageId` — Delete  🔒 Admin
```ts
// Response 204
```

---

### Reviews

#### `GET /products/:id/reviews` — List  🌐
```ts
// Query params
sort_by?: "created_at" | "rating"   // default "created_at"
skip, limit

// Response 200
Review[]   // only approved reviews
```

#### `POST /products/:id/reviews` — Create  🔒 User
```ts
// One review per user per product
// Request
{ rating: number; comment?: string }   // rating 1–5

// Response 201
Review
```

#### `PUT /products/:productId/reviews/:reviewId` — Update own  🔒 User
```ts
// Request (all optional)
{ rating?: number; comment?: string }

// Response 200
Review
```

#### `DELETE /products/:productId/reviews/:reviewId` — Delete own  🔒 User
```ts
// Response 204
// Note: admins can delete any review
```

#### `PATCH /products/:productId/reviews/:reviewId/approve` — Approve  🔒 Admin
```ts
// Response 200
Review
```

#### `PATCH /products/:productId/reviews/:reviewId/hide` — Hide  🔒 Admin
```ts
// Response 200
Review
```

---

### Wishlist  🔒 User

#### `GET /wishlist` — Get wishlist
```ts
// Response 200
Wishlist   // auto-created on first access
```

#### `POST /wishlist` — Add product
```ts
// Request
{ product_id: UUID }

// Response 201
{ message: "Added to wishlist" }
```

#### `DELETE /wishlist/:itemId` — Remove item
```ts
// Response 204
```

#### `POST /wishlist/:itemId/move-to-cart` — Move to cart
```ts
// Picks the first in-stock variant automatically
// Response 200
{ message: "Moved to cart" }
```

---

### Addresses  🔒 User

#### `GET /addresses` — List
```ts
// Response 200
Address[]
```

#### `POST /addresses` — Create
```ts
// Request
{
  label?:       string
  street:       string
  city:         string
  state?:       string
  country:      string
  postal_code:  string
  is_default?:  boolean   // default false
}

// Response 201
Address
```

#### `PUT /addresses/:id` — Update
```ts
// Request (all optional)
{ label?, street?, city?, state?, country?, postal_code?, is_default? }

// Response 200
Address
```

#### `DELETE /addresses/:id` — Delete
```ts
// Response 204
```

#### `PATCH /addresses/:id/set-default` — Set default
```ts
// Response 200
Address
```

---

### Coupons

#### `POST /coupons/validate` — Validate  🔒 User

Call before placing the order to show the user their discount.

```ts
// Request
{ code: string; order_subtotal: string }

// Response 200
CouponValidateResponse

// Errors 400: expired | limit reached | below min order | inactive | not found
```

#### `GET /coupons` — List  🔒 Admin
```ts
// Query: skip, limit
// Response 200
Coupon[]
```

#### `POST /coupons` — Create  🔒 Admin
```ts
// Request
{
  code:              string
  type:              CouponType
  value:             string
  min_order_amount?: string
  max_uses?:         number
  expires_at?:       ISODate
  is_active?:        boolean   // default true
}

// Response 201
Coupon
```

#### `PUT /coupons/:id` — Update  🔒 Admin
```ts
// Request (all optional)
// Response 200
Coupon
```

#### `DELETE /coupons/:id` — Delete  🔒 Admin
```ts
// Response 204
```

---

### Cart  🔒 User

#### `GET /cart` — Get cart
```ts
// Response 200
Cart   // auto-created; items include in_stock flag
```

#### `POST /cart/items` — Add item
```ts
// Request
{ variant_id: UUID; quantity?: number }   // quantity default 1

// Response 201
Cart
```

#### `PUT /cart/items/:itemId` — Update quantity
```ts
// Request
{ quantity: number }   // set 0 to remove

// Response 200
Cart
```

#### `DELETE /cart/items/:itemId` — Remove item
```ts
// Response 204
```

#### `DELETE /cart` — Clear cart
```ts
// Response 204
```

---

### Orders

#### `POST /orders` — Place order  🔒 User

Atomic: locks stock, applies coupon, decrements inventory, clears cart, sends email.

**Always send an `Idempotency-Key`.** Without it, a network retry places a
second order. With it, the retry returns the original order and nothing is
written twice.

```ts
// Headers
Authorization: Bearer <token>
Idempotency-Key: <uuid>   // generate once per checkout attempt, reuse on retry

// Request
{ address_id: UUID; coupon_code?: string }

// Response 201
Order
// Response header: Idempotency-Replayed: "true" | "false"

// Errors 400: empty cart | insufficient stock | invalid coupon | malformed key
// Errors 404: address not found
// Errors 409: a request with this key is still in flight — back off and retry
// Errors 422: this key was already used with a different request body
```

Client rules:

* Generate the key **once per checkout attempt** and reuse it for every retry
  of that attempt. Generating a fresh key per retry defeats the mechanism.
* Generate a **new** key when the user genuinely starts a new order.
* On `409`, wait for `Retry-After` seconds and retry with the same key.
* On `422`, the key was reused with different content — a client bug. Start a
  new attempt with a new key.

#### `GET /orders` — My orders  🔒 User
```ts
// Query: skip, limit
// Response 200
Order[]
```

#### `GET /orders/:id` — Get order  🔒 User
```ts
// Response 200
Order
```

#### `DELETE /orders/:id` — Cancel order  🔒 User
```ts
// Only allowed when status = "pending"
// Response 204
```

#### `GET /orders/admin/all` — List all orders  🔒 Admin
```ts
// Query params (all optional)
status:    OrderStatus
user_id:   UUID
from_date: string   // YYYY-MM-DD
to_date:   string
skip, limit

// Response 200
Order[]
```

#### `PATCH /orders/admin/:id/status` — Update status  🔒 Admin
```ts
// Request
{ status: OrderStatus }

// Response 200
Order
// Triggers status-change email to the user
```

---

### Returns

#### `POST /orders/:orderId/returns` — Submit return  🔒 User
```ts
// Only allowed when order status = "delivered"
// Request
{
  reason: string
  items: Array<{ order_item_id: UUID; quantity: number }>
}

// Response 201
ReturnRequest
```

#### `GET /orders/:orderId/returns/:returnId` — Get return  🔒 User
```ts
// Response 200
ReturnRequest
```

#### `GET /orders/admin/returns` — List all returns  🔒 Admin
```ts
// Query: skip, limit
// Response 200
ReturnRequest[]
```

#### `PATCH /orders/admin/returns/:returnId/approve` — Approve  🔒 Admin
```ts
// Request
{ admin_notes?: string }

// Response 200
ReturnRequest
// Sets order status → "returned", triggers email
```

#### `PATCH /orders/admin/returns/:returnId/reject` — Reject  🔒 Admin
```ts
// Request
{ admin_notes?: string }

// Response 200
ReturnRequest
// Triggers email
```

---

### Analytics  🔒 Admin

#### `GET /analytics/revenue`
```ts
// Query: from_date?, to_date? (YYYY-MM-DD)
// Response 200
{ total_revenue: number }
```

#### `GET /analytics/orders`
```ts
// Response 200
Array<{ status: OrderStatus; count: number }>
```

#### `GET /analytics/top-products`
```ts
// Query: limit? (default 10, max 50)
// Response 200
Array<{ product_name: string; total_sold: number; total_revenue: number }>
```

#### `GET /analytics/top-variants`
```ts
// Query: limit? (default 10, max 50)
// Response 200
Array<{ variant_name: string; total_sold: number }>
```

#### `GET /analytics/users`
```ts
// Query: from_date?, to_date?
// Response 200
{ total_users: number; new_users_in_period: number }
```

#### `GET /analytics/aov`
```ts
// Response 200
{ average_order_value: number }
```

#### `GET /analytics/coupons`
```ts
// Response 200
Array<{ code: string; used_count: number; max_uses: number | null }>
```

#### `GET /analytics/summary`
```ts
// Response 200
{
  total_revenue:    number
  orders_by_status: Array<{ status: OrderStatus; count: number }>
  average_order_value: number
  total_users:      number
  new_users_in_period: number
}
```

#### `GET /analytics/low-stock`
```ts
// Response 200
Array<{ variant_id: UUID; sku: string; name: string; stock_quantity: number; low_stock_threshold: number }>
```

#### `GET /analytics/export/:report.csv` — Download CSV
```ts
// :report = "revenue" | "top-products" | "top-variants" | "coupons" | "low-stock"
// Response 200  Content-Type: text/csv
```

---

## Error Responses

All errors follow this shape:

```ts
{ detail: string }
// Validation errors:
{ detail: ValidationError[]; body: any }
```

Common status codes:
| Code | Meaning |
|---|---|
| `400` | Bad request / business rule violation |
| `401` | Missing or invalid token |
| `403` | Insufficient role |
| `404` | Resource not found |
| `422` | Request validation failed |

---

## Typical Frontend Flows

### Checkout flow
```
1. GET  /cart                        — show cart with live prices
2. POST /coupons/validate            — optional: preview discount
3. GET  /addresses                   — let user pick address
4. POST /orders  { address_id, coupon_code? }
       header: Idempotency-Key: <uuid generated for this attempt>
5. → order confirmed, cart cleared, email sent
   (a retry with the same key returns the same order — no double charge)
```

### Product listing / filtering
```
GET /products?search=shoes&category_id=2&min_price=20&max_price=100&tag_id=5&skip=0&limit=20
```

### Admin image upload
```
1. POST /products/:id/images/upload-url  { filename, content_type }
   ← { upload_url, s3_key }
2. PUT  <upload_url>  (binary body, no auth header — direct to S3)
3. POST /products/:id/images  { s3_key, is_primary, sort_order }
   ← ProductImage with url
```

### Register + login
```
1. POST /auth/register
2. POST /auth/login  ← store access_token
3. All subsequent requests: Authorization: Bearer <token>
```


---

## Operational endpoints

Not part of `/api/v1`; served from the API root.

#### `GET /health` — Liveness  🌐

Dependency-free. Returns `{"status": "ok"}` whenever the process is up.

#### `GET /health/ready` — Readiness  🌐

```ts
// Response 200 (ready) or 503 (not ready)
{
  status: "ready" | "not_ready",
  checks: { database: string, cache: string }
}
```

A failing cache is reported as `degraded` but does not make the instance
unready — the API serves fine without Redis.

#### `GET /metrics` — Prometheus scrape  🌐

Prometheus text exposition format. Intended for the internal network; block it
at the ingress in production.

---

## Request tracing

Every response carries `X-Request-ID`. Send your own to join a trace across
services:

```
X-Request-ID: <id>   // optional on request; always present on the response
```

Include it in bug reports — it retrieves the entire server-side chain for that
request, including the audit entry if the request changed something.

---

## Audit log  🔒 Admin

#### `GET /audit-logs` — List admin actions

```ts
// Query params (all optional)
{
  action?: string       // e.g. "product.updated", "return.approved"
  entity_type?: string  // "product" | "product_variant" | "coupon" | "order" | ...
  entity_id?: string
  actor_user_id?: UUID
  from_date?: string    // YYYY-MM-DD
  to_date?: string
  skip?: number
  limit?: number
}

// Response 200
Array<{
  id: UUID
  actor_user_id: UUID | null
  actor_email: string | null
  action: string
  entity_type: string
  entity_id: string | null
  entity_label: string | null
  changes: Record<string, { before: unknown; after: unknown }> | null
  request_id: string | null
  ip_address: string | null
  created_at: string
}>
```

Read-only: entries cannot be edited or deleted through the API.

Recorded actions: `product.created`, `product.updated`, `product.deleted`,
`product.featured_toggled`, `product.bulk_activation`, `variant.created`,
`variant.updated`, `variant.deleted`, `coupon.created`, `coupon.updated`,
`coupon.deleted`, `order.status_changed`, `return.approved`, `return.rejected`,
`user.activated`, `user.deactivated`.

---

## Rate limits

Authentication endpoints are capped per IP **and** per account.

| Endpoint | Default budget |
|---|---|
| `POST /auth/login` | 10 attempts / 5 min |
| `POST /auth/register` | 5 / hour |
| `PUT /auth/me/password` | 10 / 5 min |

Exceeding a budget returns `429` with a `Retry-After` header (seconds). Treat
it as backoff, not as a failed login.
