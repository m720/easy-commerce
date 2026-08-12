# Operations

What to look at when something is wrong, and which levers exist when the system
needs to handle more.

## Debugging a single request

Every response carries `X-Request-ID`. Given that value from a customer report,
one query in the log aggregator returns the whole causal chain — the access log
line, every application log line emitted while handling it, and the audit entry
if the request changed something:

```
request_id:"9f2c8b1e4a7d4f10b3c2e5a6d7f80912"
```

The same ID is stored on `audit_logs.request_id` and
`idempotency_keys.request_id`, so a suspicious admin change or a duplicate
checkout can be expanded from the database back into the full request trace.

If the client did not keep the ID, work backwards from `user_id` — set on the
log context as soon as authentication succeeds — plus a time window.

## Dashboards and alerts

`docker-compose --profile monitoring up` brings up Prometheus (`:9090`) and
Grafana (`:3001`) with the API Overview dashboard and alert rules
pre-provisioned from `ops/`.

| Alert | Fires when | First move |
|---|---|---|
| `HighErrorRate` | >5% 5xx for 5m | Group `http_requests_total` by route to find which endpoint. |
| `CheckoutLatencyHigh` | `/api/v1/orders` p99 > 2s for 10m | See "checkout is slow" below. |
| `DatabasePoolSaturated` | Pool >90% in use | See "pool exhaustion" below. |
| `CheckoutFailureSpike` | Rejections rising | Read the `reason` label — it names the cause. |
| `IdempotentReplaySpike` | Replays rising | Clients are timing out before we answer: a latency problem. |
| `AuthBruteForceSuspected` | Sustained 429s on auth | Check source IPs and targeted accounts before relaxing limits. |
| `CacheErrorRateHigh` | >10% cache errors | Redis health. Not customer-facing — the API falls back to the DB — but DB load is now higher than planned. |

## Common incidents

### Checkout is slow, p99 only

p50 flat with p99 climbing is the signature of **row-lock contention**, not
general slowness. Checkout locks variant rows `FOR UPDATE` (ADR-0001), so
concurrent orders for the same product serialise.

Confirm:

```sql
SELECT pid, wait_event_type, wait_event, left(query, 120)
FROM pg_stat_activity
WHERE wait_event_type = 'Lock';

SELECT pid, pg_blocking_pids(pid)
FROM pg_stat_activity
WHERE cardinality(pg_blocking_pids(pid)) > 0;
```

Usual causes, in order of likelihood: a promoted product concentrating all
traffic on a handful of rows; a slow operation added inside the checkout
transaction (**nothing that blocks on a network belongs there**); or a
long-running admin query holding locks.

### Checkout error spike

Read the `reason` label on `order_placement_failures_total` — it is a closed set
chosen so the label names the cause:

| Reason | Meaning |
|---|---|
| `insufficient_stock` | Demand exceeds inventory. Product problem, not a bug. |
| `coupon_invalid` | Usually a campaign that expired or hit its usage cap. |
| `address_not_found` | Client bug or a stale address ID in a cached page. |
| `empty_cart` | Often double-submit: the first request already cleared the cart. |
| `variant_missing` | A variant was deleted while sitting in someone's cart. |

### Duplicate orders reported

They should be impossible for clients sending `Idempotency-Key`. Check whether
the client is sending one:

```sql
SELECT key, status, order_id, request_id, created_at
FROM idempotency_keys
WHERE user_id = '<uuid>'
ORDER BY created_at DESC;
```

No rows means the client is not using the header — the fix is client-side, and
`IDEMPOTENCY_REQUIRED=true` enforces it once every client complies. Two
different keys pointing at similar orders means the client generated a fresh
key for a retry, which is a client bug the server cannot detect.

### Stuck `in_progress` idempotency keys

A crash between reserving a key and returning a response leaves a row that
returns 409 until it expires. Clear expired rows with
`idempotency_service.purge_expired`:

```bash
python -c "from app.database.base import SessionLocal; \
from app.services.idempotency_service import purge_expired; \
db = SessionLocal(); print(purge_expired(db))"
```

Schedule this daily. A key that is stuck but not yet expired is intentional —
the alternative is risking a double order.

### Connection pool exhaustion

`db_pool_connections{state="in_use"}` pinned at `DB_POOL_SIZE` means requests
are queueing on connection checkout, which shows up as latency across every
endpoint at once.

Total connections is `workers × (DB_POOL_SIZE + DB_MAX_OVERFLOW)`, doubled if a
read replica is configured. Compare against Postgres `max_connections` before
scaling workers — adding workers to fix latency can exhaust the database
instead. PgBouncer in transaction mode is the fix once that ceiling is close.

### Redis is down

Expected behaviour: the API keeps serving. Cache reads fall through to the
database, `cache_operations_total{outcome="error"}` climbs, and rate limiting
degrades to per-process counters (each worker enforces the limit independently,
so the effective global limit is `workers × limit`). Watch database load, and
treat prolonged outages as a security consideration for the auth endpoints, not
just a performance one.

### Mail is not being delivered

`app.email` logs every failure with the triggering request's ID. SMTP calls run
in background tasks with a bounded `SMTP_TIMEOUT`, so a dead mail host slows
delivery but cannot exhaust the thread pool or block checkout.

## Scaling levers

Roughly in the order they become worth pulling:

1. **Add API workers.** The tier is stateless; this works until the database
   becomes the constraint.
2. **Turn on Redis** (`REDIS_URL`). Catalogue reads collapse to one round trip;
   rate limits become global rather than per-process.
3. **Tune cache TTLs.** `CACHE_TTL_PRODUCT_LIST` / `CACHE_TTL_PRODUCT_DETAIL`.
   Keep the detail TTL below `S3_PRESIGNED_URL_EXPIRY` so cached image URLs
   cannot outlive their signatures.
4. **Add a read replica** (`DATABASE_REPLICA_URL`). Catalogue endpoints already
   route through `get_read_db`; see ADR-0005 for which traffic may move and
   which must not.
5. **PgBouncer** in front of Postgres when connection count, not query time, is
   the limit.
6. **Move stock reservation to a queue.** The largest change, and the one that
   removes the row-lock ceiling entirely. ADR-0001 explains why it is not the
   starting point — it would be a new ADR superseding it, not an amendment.

## Configuration reference

Operationally significant settings; see `.env.example` for the full list.

| Setting | Default | Notes |
|---|---|---|
| `LOG_FORMAT` | `json` | `console` for local development. |
| `LOG_LEVEL` | `INFO` | |
| `METRICS_ENABLED` | `true` | `/metrics` returns 404 when false. |
| `REDIS_URL` | unset | Unset disables cache; rate limits fall back to per-process. |
| `CACHE_TTL_PRODUCT_LIST` | `60` | |
| `CACHE_TTL_PRODUCT_DETAIL` | `300` | Must stay below `S3_PRESIGNED_URL_EXPIRY`. |
| `RATE_LIMIT_LOGIN_MAX` / `_WINDOW` | `10` / `300s` | Applied per IP and per account. |
| `IDEMPOTENCY_REQUIRED` | `false` | Set true once all clients send the header. |
| `IDEMPOTENCY_TTL_HOURS` | `24` | How long a completed response stays replayable. |
| `DATABASE_REPLICA_URL` | unset | Falls back to the primary when unset. |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | `5` / `10` | Per worker, per engine. |
| `SMTP_TIMEOUT` | `10s` | Bounds background email sends. |

## Before public deployment

Not addressed by this work, and load-bearing:

* CORS is `allow_origins=["*"]` — needs an origin allow-list.
* `/metrics` is unauthenticated — block it at the ingress.
* JWTs cannot be revoked before expiry; deactivating an account does not
  invalidate an issued token until it expires.
* `SECRET_KEY` must not be the default.
