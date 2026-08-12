# 5. Read replica routing for catalogue traffic

Date: 2026-08-12

## Status

Accepted — routing seam built, replica not yet deployed.

## Context

Read and write traffic in a storefront are wildly asymmetric: browsing,
searching and product pages vastly outnumber checkouts. Both currently hit one
Postgres primary, which is also the instance holding the row locks that
checkout depends on (ADR-0001). Catalogue load and checkout latency are
therefore coupled — a traffic spike on browsing degrades the ability to take
orders, which is precisely backwards.

The standard remedy is a streaming replica serving reads. The catch is
**replication lag**: a replica is seconds behind, so a read routed there can
miss a write that just committed. Some reads tolerate that; some absolutely do
not. "Your order was placed" followed by an order list that does not contain it
is a support ticket, and worse, the customer places the order again.

The mistake worth avoiding is treating this as a switch to flip later. Retrofitting
read/write splitting means auditing every query in the codebase under time
pressure — usually during the incident that made it necessary.

## Decision

Build the **routing seam now**, deploy the replica when load requires it.

Two engines, two session factories, and a dependency that picks between them:

```python
db: Session = Depends(get_db)       # primary — writes, read-your-own-writes
db: Session = Depends(get_read_db)  # replica when configured, else primary
```

`get_read_db` falls back to the primary session when `DATABASE_REPLICA_URL` is
unset, so every environment runs identical code and adding a replica is a
configuration change rather than a refactor.

The classification is explicit, and it is a **product decision, not a technical
one** — "how stale may this be?" is answered per endpoint:

| Traffic | Routed to | Why |
|---|---|---|
| Product list / detail / featured / variants / images | Replica | Already cached for up to 60s (ADR-0004); replication lag is strictly smaller than the staleness we deliberately accept. |
| Checkout, cart, orders, returns | Primary | Writes, and reads that must observe them. |
| Auth, `/auth/me` | Primary | A just-changed password or deactivated account must take effect immediately — this is a security boundary. |
| Admin reads (orders, users, audit log) | Primary | Admins act on what they read; showing them a stale order status invites a wrong decision. |
| Analytics | Primary for now | The natural replica candidate — heavy aggregates that tolerate lag. Left on the primary until a replica exists and the queries are measured. |

## Alternatives considered

**Automatic routing by statement type (route SELECTs to the replica).**
Available as middleware in several ORMs and superficially attractive. Rejected
because it cannot know intent: the SELECT immediately after a checkout commit
is a read-your-own-write, and a mechanism that routes it to a replica breaks
correctness invisibly and intermittently — the worst failure mode to debug.

**Replica for everything, with `synchronous_commit=remote_apply`.** Removes lag
by making the primary wait for the replica. Rejected: it converts a read
optimisation into a write-latency penalty on the checkout path, and makes the
replica a hard dependency for taking orders.

**Skip replicas; cache harder.** The cache (ADR-0004) already absorbs most
catalogue reads, so the marginal benefit today is small — this is why the
replica is not yet deployed. But caching does not help cold keys, cache
outages, or the analytics queries that will eventually need somewhere to run.

**Read-your-own-writes via `pg_wal_lsn` tracking.** Route to the replica but
wait for the LSN of the caller's last write. Correct and used at scale.
Rejected as significant machinery to make endpoints replica-safe that we are
happy to leave on the primary.

## Consequences

**Good.** The seam exists and is exercised: catalogue endpoints already declare
`get_read_db`, so the split is real code rather than an intention. Deploying a
replica is a URL in the environment.

**Good.** The classification above is written down. The next person to add an
endpoint has a rule to follow rather than a coin to flip.

**Bad.** Two pools per process (each `DB_POOL_SIZE` + overflow) when a replica
is configured. Connection count against Postgres roughly doubles, which needs
sizing — and is an argument for PgBouncer in front of both.

**Bad.** `get_read_db` opens a primary session it may not use, since it takes
`get_db` as a dependency to keep test overrides working. One idle checkout from
the pool per replica-routed request. Cheap, but not zero, and worth revisiting
if pool pressure appears in `db_pool_connections`.

**Bad.** Until a replica is deployed, none of this is load-tested. The lag
behaviour is reasoned about, not measured. First deployment should verify with
`pg_stat_replication` before moving anything beyond the catalogue.

**Watch.** `db_pool_connections{pool="primary"|"replica",state="in_use"}` for
saturation. Once a replica exists, alert on `pg_last_xact_replay_timestamp`
lag exceeding the catalogue cache TTL — beyond that point the replica is
staler than the thing it is meant to be an alternative to.
