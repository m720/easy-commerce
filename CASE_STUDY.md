# Easy Commerce — Portfolio Case Study

A full-stack e-commerce platform: a customer-facing storefront, a complete
back-office admin console, and a backend built to be operated by someone who
didn't write it.

---

## 1. Short descriptions (pick by length)

**One line**
> A full-stack e-commerce platform — storefront, retry-safe checkout and
> back-office admin console — built with FastAPI, PostgreSQL, Redis and React 19.

**Elevator pitch (~50 words)**
> Easy Commerce is a production-shaped online store. Customers browse a
> variant-level catalogue, build a persistent cart, redeem coupons and check out
> against a saved address; admins manage the catalogue, orders, returns and
> users behind an audited console. Checkout is idempotent and lock-protected,
> and every request is traceable end to end.

**Long description (~180 words)**
> Easy Commerce is a full-stack e-commerce platform covering the entire retail
> loop, from browsing to returns — and the operational layer that makes it
> runnable in production.
>
> The storefront lets shoppers search and filter a catalogue of products with
> per-variant SKUs, pricing and stock, save items to a wishlist, build a
> server-persisted cart, apply coupon codes, and check out against a saved
> shipping address. Orders can be tracked, cancelled while pending, and returned
> item-by-item after delivery. The admin console offers full catalogue CRUD, an
> order status pipeline, a return approval workflow, review moderation, user
> management and a revenue analytics dashboard.
>
> Underneath, checkout takes row-level database locks so concurrent buyers can't
> oversell the last unit, and accepts an `Idempotency-Key` so a network retry
> replays the original response instead of placing a second order. The catalogue
> is cached in Redis with O(1) version-counter invalidation and routed to a read
> replica when one is configured. Every privileged admin action is written to an
> append-only audit log with before/after diffs, and every request carries a
> correlation ID through logs, metrics and audit rows.

---

## 2. At a glance

| | |
|---|---|
| **Type** | Full-stack web application (monorepo: API + SPA) |
| **Domain** | E-commerce / retail |
| **Backend** | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0, PostgreSQL 16, Redis 7 |
| **Frontend** | React 19, TypeScript 5.9, Vite 7, Tailwind CSS 4 |
| **Auth** | JWT (python-jose) + bcrypt, role-based, rate-limited |
| **Observability** | Structured JSON logs, correlation IDs, Prometheus, Grafana |
| **REST endpoints** | 85 across 13 routers, plus health, readiness and metrics |
| **Database tables** | 20 |
| **Backend tests** | 98 cases across 14 modules |
| **Frontend pages** | 21 route components (9 shop, 10 admin, 2 auth) |
| **Design docs** | 5 ADRs, architecture guide, operations runbook, API reference |

---

## 3. Feature list

### 3.1 Accounts & authentication
- Email + password registration with server-side duplicate-email rejection
- Login issuing a signed JWT access token (HS256, configurable expiry)
- Bcrypt password hashing via passlib
- `GET /auth/me` session bootstrap; token persisted client-side through a
  Zustand `persist` store so sessions survive a refresh
- Profile editing (name, email) with uniqueness checks
- Password change requiring the current password
- Account deactivation enforced at login *and* on every authenticated request —
  a deactivated user's existing token stops working immediately
- **Rate limiting** on login, registration and password change: per-IP *and*
  per-account fixed windows, shared across workers via Redis, with an
  in-process fallback that documents itself as single-worker only
- `429` responses carry `Retry-After`
- Axios interceptor that auto-logs-out on `401` and redirects to login with a
  `?redirect=` return path
- Route-level `AuthGuard` supporting both "logged in" and "admin only" modes

### 3.2 Catalogue & product browsing
- Product listing with combinable filters: free-text name search, category, tag,
  min price, max price, featured flag, active flag
- `skip`/`limit` pagination (default 20, capped at 100) shared by every list
  endpoint via a reusable `Pagination` dependency
- Featured products endpoint powering the homepage
- Category browse (`/categories/{id}/products`)
- Product detail with description, category, tags, image gallery with
  thumbnail switching, and variant selection
- **Variants as first-class entities** — each variant carries its own SKU
  (unique-enforced), price, stock quantity and low-stock threshold; the
  displayed price and stock follow the selected variant
- Multi-image support with a designated primary image and explicit sort order
- Soft delete: products are deactivated, never destroyed, so historical orders
  keep resolving
- **Redis cache-aside** on list, featured, detail and variant reads, with TTLs
  tuned per endpoint and kept under the S3 pre-signed URL expiry so cached image
  links can never outlive their signatures
- **Read-replica routing** — catalogue reads go through a separate `get_read_db`
  dependency that falls back to the primary when no replica is configured
- Skeleton loading states on list and detail views

### 3.3 Reviews
- One review per user per product, enforced by a unique DB constraint
- 1–5 star rating plus optional comment
- **Moderation workflow** — reviews land unapproved; only approved reviews are
  publicly visible, while an author always sees their own
- Authors can edit or delete their own review; admins can edit, delete, approve
  or hide any review
- Aggregate star display on product cards and detail pages

### 3.4 Wishlist
- One wishlist auto-provisioned per user on first use
- Add / remove products, with a unique constraint preventing duplicates
- **Move-to-cart** in a single action

### 3.5 Cart
- Server-persisted cart, one per user, created lazily
- Add, update quantity, remove, clear
- Adding an existing variant increments rather than duplicating the line
  (unique constraint on `cart_id + variant_id`)
- Stock validated on add and on quantity update
- Setting a quantity to zero removes the line
- Live subtotal computed server-side plus a per-line `in_stock` flag, so the
  cart page can flag items that went out of stock after they were added
- Header cart badge with live item count

### 3.6 Addresses
- Multiple saved addresses per user, each with an optional label
- Full create / update / delete
- **Set-default** action that atomically clears the previous default
- Address picker inline in checkout

### 3.7 Coupons & discounts
- Two coupon types: **percentage** and **fixed amount**
- Validation rules enforced in one shared service: existence, active flag,
  expiry date, max-use ceiling, and minimum order amount
- Fixed discounts clamp to the order subtotal (never negative totals);
  percentage discounts quantize to 2dp
- Pre-checkout `POST /coupons/validate` so the cart can preview the discount
  before the order is placed
- Redemption counter incremented as part of the order transaction

### 3.8 Checkout & orders
- Checkout against a chosen saved address with optional coupon code
- **Idempotent checkout** — `POST /orders` accepts an `Idempotency-Key` header.
  A retry replays the stored response instead of placing a second order;
  concurrent retries are resolved by a unique constraint rather than a
  check-then-insert race; reusing a key with a different body is a `422`; failed
  attempts release the key; completed responses expire after 24h. Responses
  carry an `Idempotency-Replayed` header. Enforcement is opt-in via config so
  existing clients keep working.
- **Concurrency-safe stock handling** — the order service takes
  `SELECT … FOR UPDATE OF product_variants` locks on every variant in the cart,
  ordered by ID so overlapping carts always lock in the same sequence and cannot
  deadlock each other
- Stock decremented, order + line items written, coupon usage incremented and
  the cart cleared inside a **single** transaction — the cart clear no longer
  commits early and release locks mid-flight
- **Price and address snapshots** — product name, variant name and unit price
  are copied onto the order line, and the shipping address is stored as a JSONB
  snapshot, so later catalogue or address edits never rewrite order history
- Order lifecycle: `pending → processing → shipped → delivered`, plus
  `cancelled` and `returned`
- Customer-side cancellation, restricted to `pending` orders
- Order history list and order detail with status badge and line breakdown
- Every rejection reason is counted as a labelled metric from a closed set
  (`insufficient_stock`, `coupon_invalid`, `empty_cart`, `address_not_found`,
  `variant_missing`), so an alert arrives pre-diagnosed
- Automatic low-stock detection at checkout time, dispatched as a background task

### 3.9 Returns
- Item-level return requests against delivered orders — the customer picks which
  line items and what quantity to return, with a free-text reason
- Server validates that each requested item belongs to the order and that the
  quantity does not exceed what was purchased
- Return lifecycle: `pending → approved / rejected`, with admin notes
- Approving a return moves the parent order to `returned`
- Customers can look up the status of their own return requests

### 3.10 Admin — catalogue management
- Product create / edit form with category, tags, pricing, featured flag
- Variant management: add, edit, delete, with SKU-uniqueness enforcement
- Image management: request a pre-signed S3 upload URL, confirm the upload,
  set the primary image, reorder, delete
- Feature/unfeature toggle
- **Bulk activate / deactivate** across a selection of products
- Category CRUD with slug uniqueness and delete-protection when products are
  still attached
- Tag CRUD with the same slug and in-use protections
- Every mutation invalidates the catalogue cache namespace and writes an audit
  entry

### 3.11 Admin — operations
- All-orders view with filtering by status and by user
- Order status transitions from the admin console, each firing a customer
  notification email in the background
- Returns queue with approve / reject and admin notes
- Coupon CRUD with code-uniqueness enforcement and live usage counters
- User directory with search and role filter
- User activate / deactivate
- Per-user activity summary (orders, spend, reviews)
- Review approve / hide from the moderation surface

### 3.12 Admin — audit trail
- **Append-only audit log** of 16 privileged action types across products,
  variants, coupons, orders, returns and users
- Each entry records the actor (id *and* denormalised email), action, entity
  type/id/label, a `{field: {before, after}}` diff of only what actually
  changed, the originating IP, and the request correlation ID
- Denormalised on purpose — "who approved this refund in March" must survive the
  actor being deleted and the entity being renamed
- Actor FK is `SET NULL`, never `CASCADE`: deleting an admin cannot erase their
  trail
- Read-only query API with filters by action, entity type, entity id, actor and
  date range — there is deliberately no edit or delete endpoint

### 3.13 Admin — analytics
- Total revenue, with an optional date range, excluding cancelled orders
- Order counts grouped by status
- Average order value
- Top products by units sold, with revenue
- Top variants by units sold
- Total users and new users in a period
- Coupon redemption stats (used vs. max uses)
- Combined `summary` endpoint powering the dashboard in one request
- **Low-stock report** — every variant at or below its own threshold
- **CSV export** for revenue, top products, top variants, coupons and low stock
- Charts rendered with Recharts

### 3.14 Observability
- **Structured JSON logging** with request-scoped correlation IDs. The ID is
  adopted from an inbound `X-Request-ID` when a gateway supplies one (length-capped
  so a hostile client can't bloat downstream log lines), echoed on every
  response, and stamped on every log line, audit row and idempotency record — so
  one ID reconstructs the whole checkout → order-write chain.
- Caller identity resolved in middleware rather than in the auth dependency,
  because sync endpoints run in their own threadpool contexts and a contextvar
  set inside a dependency never reaches the access log
- **Prometheus `/metrics`** exposing request rate, latency histogram (buckets
  tuned for a web API) and error rate by route template — never raw paths, to
  bound label cardinality — plus DB pool state and domain counters: orders
  placed, checkout failures by reason, idempotent replays, cache hits/misses by
  namespace, cache invalidations, rate-limit rejections and audit events
- **Split health probes** — `/health` is deliberately dependency-free so a brief
  DB blip can't fail a whole fleet's liveness check; `/health/ready` reports
  Postgres and Redis and returns `503` only when the database is unreachable
  (Redis degradation is reported, not disqualifying)
- Prometheus + Grafana ship in the compose file behind a `monitoring` profile,
  with a provisioned dashboard and alert rules
- Startup log line reporting which optional subsystems are actually live

### 3.15 Notifications
- Order confirmation email on checkout
- Order status change email
- Return request decision email, including admin notes
- Low-stock alert email to the configured admin address
- All sent via FastAPI `BackgroundTasks` so the request never blocks on SMTP;
  the connection is timeout-bounded and failures are logged rather than
  swallowed; the mailer degrades to a no-op when SMTP isn't configured

### 3.16 Media & file storage
- S3 integration with **pre-signed URLs on both sides**: pre-signed PUT for
  browser-direct uploads (files never transit the API), pre-signed GET for reads
- Graceful fallback — keys that are already absolute URLs or root-relative paths
  are served verbatim, so the app works with zero AWS configuration
- 55 flat-vector product photos committed to the repo and served from the API's
  `/static` mount, with a generator script to regenerate them

### 3.17 Developer experience & documentation
- OpenAPI/Swagger UI at `/docs` and ReDoc at `/redoc`, auto-generated from the
  Pydantic schemas
- Hand-written API reference for frontend integration, including client-side
  idempotency rules
- `ARCHITECTURE.md` with deployment topology, checkout sequence and data model
  diagrams; `OPERATIONS.md` runbook covering six named incident scenarios
- **Five ADRs** in Nygard format — row-level locking for stock, JSONB address
  snapshots, idempotency keys, cache invalidation strategy, read-replica
  routing — each stating the alternatives rejected and the consequences accepted
- Docker Compose for API + PostgreSQL + Redis + migrations, with monitoring as
  an opt-in profile
- Alembic migrations
- **Deterministic seed script** — fixed RNG seed, populates the full schema:
  10 users, 12 addresses, 6 categories, 8 tags, 24 products, 61 variants,
  55 photos, 7 coupons (including a deliberately expired and a retired one),
  46 orders weighted across statuses to produce a realistic funnel, live carts,
  wishlists, purchase-gated reviews and 7 return requests. Re-running produces
  byte-identical data.
- A dev-only in-app toolbar for one-click switching between seeded accounts
- 98 pytest integration tests across auth, products, cart, orders, coupons,
  categories, addresses, reviews, analytics, audit, cache, idempotency,
  observability and rate limiting

---

## 4. Architecture

```
easy-commerce/
├── packages/api/                 FastAPI service
│   ├── app/
│   │   ├── routers/              13 routers → HTTP surface only
│   │   ├── services/             business logic (orders, cart, coupons, products,
│   │   │                         analytics, idempotency, audit, S3, email)
│   │   ├── models/               12 model modules → 20 tables
│   │   ├── schemas/              Pydantic request/response contracts
│   │   ├── core/                 security, enums, logging, metrics, cache,
│   │   │                         rate limiting, exception handlers
│   │   ├── middleware/           request context + telemetry
│   │   ├── database/base.py      primary + optional replica engines
│   │   ├── dependencies.py       DB session, read session, current user,
│   │   │                         admin guard, audit context, paging
│   │   └── static/products/      committed product photos
│   ├── alembic/                  migrations
│   ├── docs/                     architecture, operations, API reference, ADRs
│   ├── ops/                      Prometheus config + Grafana dashboards
│   ├── tests/                    98 pytest cases
│   └── seed.py                   deterministic full-schema seeder
└── packages/web/                 React + TypeScript SPA
    └── src/
        ├── api/                  one typed module per resource (14)
        ├── pages/                shop / admin / auth route components
        ├── components/           layout, shared UI, dev tooling
        ├── store/                Zustand auth store (persisted)
        └── types/                shared API type definitions
```

**Layering.** Routers stay thin — they resolve dependencies, call a service and
return a schema. All business rules (stock locking, discount math, moderation
gating, snapshotting, idempotency) live in the service layer, which is what
makes them testable without HTTP and reusable between the API and the seeder.

**Middleware order.** The request-context middleware is registered *inside*
CORS, so CORS-rejected and preflight requests still get a correlation ID and
still appear in metrics.

**Auth flow.** `HTTPBearer` → decode JWT → load user → reject if inactive.
`require_admin` composes on top of `get_current_user`; `admin_audit` composes on
top of *that*, so an admin route is one dependency away from being both locked
down and audited.

**Read/write split.** Writes and read-your-own-write paths use `get_db` on the
primary engine. Catalogue reads use `get_read_db`, which resolves to the replica
when `DATABASE_REPLICA_URL` is set and to the primary otherwise — the seam
exists either way, so adding a replica is a config change, not a refactor.

**Frontend data layer.** TanStack Query owns all server state and cache
invalidation; Zustand owns only the auth token and user. No hand-rolled
loading/error state, no duplicated server data in component state.

---

## 5. Data model

20 tables. The relationships worth calling out:

- `products → product_variants` — the catalogue is priced and stocked at the
  variant level, not the product level. Carts and orders reference **variants**,
  never products.
- `products ↔ tags` — many-to-many through `product_tags`.
- `orders → order_items` — line items denormalize product name, variant name and
  unit price at purchase time; the FK to the variant is `SET NULL` on delete so
  order history outlives the catalogue.
- `orders.shipping_address_snapshot` — JSONB, so editing a saved address never
  rewrites past orders.
- `return_requests → return_request_items → order_items` — returns are tracked
  per line item and per quantity, not per order.
- `idempotency_keys` — unique on `(user_id, endpoint, key)`. That constraint
  *is* the concurrency control: two simultaneous retries race to INSERT and the
  loser is told the original is still in flight.
- `audit_logs` — append-only, denormalised actor and entity labels, JSONB
  change diff, indexed on action, `(entity_type, entity_id)` and `created_at`.
- Unique constraints doing real work: one review per user+product, one cart line
  per cart+variant, one wishlist entry per wishlist+product, unique SKUs, unique
  coupon codes, unique category/tag slugs.

---

## 6. Engineering highlights

These are the parts worth talking through in an interview.

**Overselling is prevented at the database, not in application logic.**
Checkout acquires `SELECT … FOR UPDATE OF product_variants` locks on every
variant in the cart in a single query, ordered by ID, then validates, decrements,
writes the order and clears the cart in one transaction. Two concurrent
checkouts for the last unit serialize; the second fails cleanly with a 400
naming the variant and the available quantity. Consistent lock ordering makes
deadlock between overlapping carts structurally impossible.

**Checkout survives the network.** A dropped response on `POST /orders` is the
classic double-charge bug. An `Idempotency-Key` header makes the call replayable:
the first request reserves the key, stores its response on completion, and
returns it verbatim on retry. The reservation is an INSERT against a unique
constraint rather than a check-then-insert, so concurrent retries can't both win.
A key reused with a *different* body is treated as a client bug (`422`), not a
retry — silently returning the first order for a different request would be
worse than failing.

**Order history is immutable by construction.** Instead of joining live
catalogue rows at read time, orders carry their own copies of the product name,
variant name and unit price, and a JSONB snapshot of the shipping address.
Renaming a product, repricing a variant or editing an address cannot retroactively
change what a customer sees they paid. The audit log applies the same reasoning
to admin actions.

**Cache invalidation without a key scan.** The catalogue cache is namespaced by
a version counter: keys are built as `catalog:v3:products:…`, and any admin write
bumps the counter, orphaning every key in the namespace in one `INCR`. No
`KEYS` scan, no per-key bookkeeping, no invalidation logic that has to know
which keys a given write affects. A cache outage degrades to direct DB reads
rather than erroring.

**Optional dependencies are genuinely optional.** Redis, S3, SMTP and the read
replica are all configured for production and all degrade to working no-ops
locally: image keys that are already URLs bypass S3, the mailer returns early
without credentials, the cache falls through to the database, the read session
falls back to the primary, and the rate limiter drops to an in-process counter
that documents itself as single-worker only. The whole app — storefront, admin,
analytics, product photography — runs from `docker-compose up` plus one seed
command, with no cloud account and no network access.

**Operability was treated as a feature.** One correlation ID reconstructs a
request across access logs, application logs, audit rows and idempotency records.
Checkout failures are counted by reason from a closed label set, so an alert
arrives already diagnosed — a spike in `insufficient_stock` is an inventory
problem, a spike in `coupon_invalid` is usually a broken campaign. HTTP metrics
are labelled by route template, never raw path, so cardinality stays bounded.
Liveness and readiness are deliberately different questions.

**Five bugs the observability work surfaced.** Adding tests and telemetry to
existing code found real defects:
- Checkout was **completely broken on PostgreSQL** — `SELECT FOR UPDATE`
  combined with an eager-loaded `product` relationship produced *"FOR UPDATE
  cannot be applied to the nullable side of an outer join"*, so every
  `POST /orders` returned 500. Fixed by locking `product_variants` explicitly.
- The admin test fixture promoted its user through a **second DB session that
  couldn't see the fixture's open transaction**, so the promotion silently
  no-op'd and every admin test 403'd — which is what had been masking the
  checkout bug. The suite went from 17 passing with 33 broken to 98 passing.
- SMTP had **no timeout**, so an unreachable mail host pinned a background-task
  thread indefinitely.
- The exception handler **dropped `HTTPException` headers**, discarding
  `Retry-After` on 429 and 409 responses and leaving clients to guess a backoff.
- Checkout **committed mid-transaction** when clearing the cart, releasing its
  row locks early and reopening the oversell window it was built to close.

**Decisions are written down.** Five ADRs record the choices that were expensive
to make and would be expensive to reverse, each naming the alternatives rejected
and the consequences accepted — including the unwelcome ones. Deciding *not* to
use optimistic concurrency, *not* to invalidate cache keys individually, and
*not* to make idempotency mandatory are all documented with their reasoning.

**A shared pagination dependency, not 20 copies of `skip`/`limit`.** One
`Pagination` class is injected into every list endpoint, giving uniform defaults
and a uniform 100-row ceiling across the entire API surface.

---

## 7. Design system

The UI runs on a custom Tailwind 4 theme rather than a component library:

- **Palette** — charcoal `#171e19` in place of pure black, sage `#b7c6c2`,
  cream `#eeebe3`, and a single brand red `#ca0013` used sparingly for primary
  actions and selection
- **Type** — Nunito, with a 10px bold uppercase wide-tracked label style for
  metadata
- **Shape** — a two-tier radius scale: 40px for top-level cards, 24px for nested
  elements, plus one soft elevation shadow
- **Motion** — native CSS view transitions on navigation, gated behind
  `prefers-reduced-motion`
- **Accessibility** — explicit brand-colored `:focus-visible` rings and matching
  `::selection` styling
- Responsive layouts throughout, with a mobile nav drawer

---

## 8. What I'd do next

Honest gaps, in the order I'd close them:

1. **Payments** — checkout ends at order creation; there's no payment provider
   integration. The idempotency layer was built with this in mind.
2. **Refresh tokens** — access tokens expire in 30 minutes with no refresh flow.
3. **Frontend tests** — the backend has 98 integration tests; the SPA has none,
   and no test runner is configured.
4. **CI** — no pipeline is wired up; tests and lint run locally only.
5. **Admin UI for the audit log** — the API is complete and filterable, but no
   admin page consumes it yet.
6. **Total-count pagination metadata** — list endpoints return a page of rows
   but no total, so the UI can't render "page 3 of 12".
7. **CORS lockdown and a configurable API base URL** — origins are `*` and the
   frontend's base URL is hardcoded to `localhost:8000`; both need pinning
   before deployment.
8. **Distributed tracing** — correlation IDs cover the single-service case;
   OpenTelemetry spans would be the next step if this grew a second service.
