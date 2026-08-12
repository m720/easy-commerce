# Architecture

How the system fits together, what happens on the critical path, and where the
data lives. Decisions with real trade-offs are recorded separately as
[ADRs](adr/README.md); this document describes the shape that resulted.

## Deployment topology

```mermaid
flowchart TB
    subgraph clients[" "]
        browser["Browser<br/>React 19 + Vite"]
    end

    subgraph edge["Edge"]
        lb["Load balancer / ingress<br/>terminates TLS, sets X-Request-ID"]
    end

    subgraph app["Application tier — stateless, horizontally scalable"]
        api1["FastAPI worker"]
        api2["FastAPI worker"]
        api3["FastAPI worker"]
    end

    subgraph data["Data tier"]
        pg[("PostgreSQL 16<br/>primary — all writes")]
        replica[("Read replica<br/>catalogue reads — ADR-0005")]
        redis[("Redis<br/>cache + rate-limit counters")]
    end

    subgraph ext["External"]
        s3["S3<br/>product images"]
        smtp["SMTP<br/>transactional email"]
    end

    subgraph obs["Observability"]
        prom["Prometheus<br/>scrapes /metrics"]
        graf["Grafana"]
        logs["Log aggregator<br/>JSON lines on stdout"]
    end

    browser --> lb --> api1 & api2 & api3
    api1 & api2 & api3 --> pg
    api1 & api2 & api3 -.catalogue.-> replica
    api1 & api2 & api3 --> redis
    pg -. streaming replication .-> replica
    api1 & api2 & api3 --> s3
    api1 & api2 & api3 -. background tasks .-> smtp
    prom -.scrape.-> api1 & api2 & api3
    prom --> graf
    api1 & api2 & api3 -.stdout.-> logs

    classDef planned stroke-dasharray: 5 5
    class replica planned
```

The application tier holds no state: sessions are JWTs, the cart lives in
Postgres, and the cache is shared. Any worker can serve any request, so scaling
is adding workers until the database becomes the constraint — at which point
ADR-0005 (replicas) and ADR-0004 (caching) are the levers.

Dashed = designed and wired, not yet deployed.

## Checkout: the critical path

The one flow where correctness, concurrency and money intersect. Every numbered
step is instrumented with the same `request_id`.

```mermaid
sequenceDiagram
    autonumber
    participant C as Client
    participant M as RequestContextMiddleware
    participant R as Orders router
    participant I as Idempotency service
    participant O as Order service
    participant DB as PostgreSQL
    participant BG as Background tasks

    C->>M: POST /orders<br/>Idempotency-Key: k1
    M->>M: adopt or mint request_id<br/>(bind to log context)
    M->>R: dispatch

    R->>I: reserve(k1, fingerprint(body))
    alt key already completed
        I-->>R: stored response
        R-->>C: 201 + Idempotency-Replayed: true
        Note over R,C: retry served — no second order
    else key in flight
        I-->>R: conflict
        R-->>C: 409 + Retry-After
    else key is ours
        I->>DB: INSERT reservation (COMMIT)
        I-->>R: proceed

        R->>O: place_order()
        O->>DB: BEGIN
        O->>DB: SELECT variants … ORDER BY id FOR UPDATE
        Note over O,DB: row locks held — ADR-0001
        O->>O: validate stock, apply coupon
        O->>DB: INSERT order + order_items
        O->>DB: UPDATE stock_quantity
        O->>DB: DELETE cart_items
        O->>DB: COMMIT
        Note over O,DB: order, stock and cart commit as one unit

        O-->>R: order
        R->>I: complete(k1, response, order_id)
        I->>DB: store response for replay
        R-->>C: 201 + order

        R->>BG: order_placed / low_stock_alert
        BG->>BG: SMTP send (bounded timeout, off the request path)
    end

    M->>M: log request completed<br/>+ record latency & status metrics
```

Two properties this diagram is meant to make obvious:

* **Nothing that touches the network sits inside the database transaction.**
  Email happens after commit, in a background task with a bounded timeout —
  because a slow SMTP host inside the transaction would hold row locks and
  serialise every other checkout for the same product.
* **The idempotency reservation commits before the work starts.** That is what
  makes a crash mid-checkout produce a 409 on retry rather than a second order.

## Data model

```mermaid
erDiagram
    users ||--o{ orders : places
    users ||--o{ addresses : "address book"
    users ||--|| carts : has
    users ||--o{ reviews : writes
    users ||--|| wishlists : has
    users ||--o{ return_requests : raises
    users ||--o{ idempotency_keys : owns
    users ||--o{ audit_logs : "acts (SET NULL)"

    categories ||--o{ products : groups
    products ||--o{ product_variants : "sold as"
    products ||--o{ product_images : has
    products }o--o{ tags : tagged
    products ||--o{ reviews : receives

    carts ||--o{ cart_items : holds
    product_variants ||--o{ cart_items : "referenced by"

    orders ||--o{ order_items : contains
    orders ||--o{ return_requests : "may be returned"
    coupons ||--o{ orders : discounts
    product_variants ||--o{ order_items : "referenced by"
    return_requests ||--o{ return_request_items : itemises
    order_items ||--o{ return_request_items : "returned as"

    orders {
        uuid id PK
        uuid user_id FK "SET NULL — orders outlive accounts"
        enum status
        numeric total_amount
        jsonb shipping_address_snapshot "immutable copy — ADR-0002"
    }
    order_items {
        uuid id PK
        string product_name "copied, not joined"
        string variant_name "copied, not joined"
        numeric unit_price "price at time of sale"
    }
    product_variants {
        uuid id PK
        string sku UK
        int stock_quantity "locked FOR UPDATE at checkout"
    }
    idempotency_keys {
        uuid id PK
        string key UK "unique per (user, endpoint, key)"
        string request_fingerprint
        jsonb response_body "replayed on retry"
    }
    audit_logs {
        uuid id PK
        string action
        jsonb changes "before/after, changed fields only"
        string request_id "joins to the request log"
    }
```

The recurring theme: **transactional records copy what they need instead of
referencing it.** Order items copy product name and price; orders copy the
shipping address; audit entries copy the actor's email. Master data changes,
history must not (ADR-0002).

## Request lifecycle

Every request passes through the same envelope, which is what makes the system
observable without per-endpoint instrumentation:

```mermaid
flowchart LR
    in([Request]) --> rid["Adopt or mint<br/>X-Request-ID"]
    rid --> ctx["Bind request_id to<br/>log context (contextvar)"]
    ctx --> cors[CORS]
    cors --> route[Route handler]
    route --> auth["Auth dependency<br/>binds user_id to context"]
    auth --> work["Handler<br/>cache → replica → primary"]
    work --> resp["Response<br/>+ X-Request-ID header"]
    resp --> log["One structured log line:<br/>method, route, status, duration"]
    log --> met["Metrics: counter + histogram<br/>labelled by route template"]
    met --> out([Client])
```

A single `request_id` therefore joins: the access log line, every application
log line emitted while handling it, the audit entry if the request changed
something, and the idempotency record if it was a checkout. Given a customer
complaint and one ID, the entire causal chain is one query in the log
aggregator.

## Operational surface

| Endpoint | Purpose | Notes |
|---|---|---|
| `GET /health` | Liveness | No dependencies. A DB blip must not restart the fleet. |
| `GET /health/ready` | Readiness | Checks Postgres; reports Redis as degraded, not fatal. |
| `GET /metrics` | Prometheus scrape | Route-template labels only — no IDs, no cardinality explosion. |
| `GET /api/v1/audit-logs` | Admin audit trail | Read-only; no edit or delete path exists. |

### The three signals

| Signal | Metric | What it answers |
|---|---|---|
| Latency | `http_request_duration_seconds` | Is checkout slow? Is p99 diverging from p50 (contention)? |
| Error rate | `http_requests_total{status}` | What fraction of requests fail, by route? |
| Saturation | `db_pool_connections{state="in_use"}` | Are we about to exhaust the connection pool? |

Domain counters (`orders_placed_total`, `order_placement_failures_total{reason}`,
`idempotent_replays_total`, `cache_operations_total{outcome}`,
`rate_limit_rejections_total`) turn an alert into a diagnosis: a checkout error
spike with `reason="insufficient_stock"` is inventory, with
`reason="coupon_invalid"` is a broken campaign, and a rising replay rate means
clients are timing out before we answer.

## Security posture

* **Rate limiting** on login, registration and password change — per IP *and*
  per account, so neither a single host spraying accounts nor many hosts
  targeting one account gets unlimited guesses.
* **Audit log** on every privileged mutation: who, what changed (before/after),
  from which IP, tied to a request ID.
* **Password verification endpoints** are treated as guessing oracles and rate
  limited accordingly, not just the login route.
* **Bounded external calls**: SMTP has an explicit timeout, so a hung mail
  provider cannot exhaust the background-task thread pool.

Known gaps, deliberately not addressed here: CORS is `*` and needs an origin
allow-list before public deployment; JWTs are not revocable before expiry; and
`/metrics` is unauthenticated and must be blocked at the ingress.
