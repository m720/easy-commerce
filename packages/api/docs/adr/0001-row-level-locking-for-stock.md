# 1. Row-level locking for stock decrement

Date: 2026-08-12

## Status

Accepted.

## Context

Checkout must not sell the same unit twice. The dangerous interleaving is
ordinary read-modify-write:

```
T1: SELECT stock_quantity FROM product_variants WHERE id = X   -- reads 1
T2: SELECT stock_quantity FROM product_variants WHERE id = X   -- reads 1
T1: UPDATE ... SET stock_quantity = 0                          -- sells the last unit
T2: UPDATE ... SET stock_quantity = 0                          -- sells it again
```

Both transactions committed, both customers were charged, one unit exists. At
low traffic this is rare; on a promoted product it is the normal case, because
that is exactly when concurrent checkouts collide on the same rows.

Constraints that shaped the decision:

* Overselling is a **customer-visible, money-losing** failure. Someone has to
  cancel an order and apologise, and in some categories (event tickets,
  limited drops) it is a legal problem.
* Traffic today is a single Postgres primary and a handful of API workers.
  Peak concurrency on any one variant row is low.
* Stock and the order write must agree. A design where they can disagree needs
  reconciliation, and reconciliation needs an on-call human.

## Decision

Take **`SELECT … FOR UPDATE` row-level locks** on every variant in the cart, in
a single statement ordered by primary key, then validate stock, write the
order, decrement, and clear the cart in **one transaction**.

```python
variants = (
    db.query(ProductVariant)
    .filter(ProductVariant.id.in_(variant_ids))
    .order_by(ProductVariant.id)
    .with_for_update(of=ProductVariant)
    .all()
)
```

Three details are load-bearing:

1. **One statement, not a loop.** Locking rows one at a time widens the window
   in which another transaction takes the second lock first.
2. **`ORDER BY id`.** Two carts sharing variants A and B, locking in opposite
   orders, deadlock. Postgres detects it and kills one transaction — a 500 for
   a customer who did nothing wrong. A consistent lock order makes the cycle
   impossible.
3. **`of=ProductVariant`.** The query eager-loads `product` via LEFT OUTER
   JOIN, and Postgres rejects `FOR UPDATE` against the nullable side of an
   outer join. Naming the table locks the rows that matter and leaves the
   joined product untouched.

The cart clear participates in the same transaction (`clear_cart(commit=False)`)
so the whole checkout commits or aborts as a unit, and the locks are held until
the end rather than released early by an interior commit.

## Alternatives considered

**Optimistic concurrency (version column, retry on conflict).** Cheaper under
contention because nothing blocks, and it is the right answer at high write
volume. Rejected for now: it pushes retry logic into the checkout path, and a
retry loop around a transaction that also charges money is precisely where
double-charge bugs are born. Revisit if lock waits appear in the latency
histogram.

**Eventual consistency: accept the order, reserve stock asynchronously via a
queue.** This is how large marketplaces do it, and it scales far past row
locking. Rejected because it changes the product, not just the code — the
customer gets "order received" rather than "order confirmed", and every
oversell becomes a cancellation email plus a refund path plus a compensating
transaction. That machinery is worth building when write volume demands it; at
this scale it would be a lot of moving parts to solve a problem one line of SQL
already solves.

**Database `CHECK (stock_quantity >= 0)` alone.** A useful backstop and cheap
to add, but a constraint violation surfaces as a failed transaction after the
customer has submitted, with no way to distinguish "sold out" from "bug". It
guards the invariant; it does not coordinate the decision.

**Serializable isolation for the whole transaction.** Correct, and Postgres
implements it well, but it converts contention into serialisation failures the
application must retry — the same retry problem as optimistic locking, applied
to every statement rather than the rows we care about.

## Consequences

**Good.** Overselling is impossible for concurrent checkouts within a single
Postgres instance; the invariant is enforced where the data lives, not in
application logic that a future caller might bypass. Reasoning about checkout
requires no distributed-systems thinking: it is one transaction.

**Bad.** Concurrent checkouts of the same variant serialise. A hot product is a
lock queue, and if the transaction ever grows slow work (an external payment
call, an email), that queue becomes a latency spike. **Nothing that blocks on a
network belongs inside this transaction** — the notification sends are
background tasks for exactly this reason.

**Bad.** The lock lives in the primary database, so this does not extend to
multi-primary or sharded topologies without redesign. That redesign is the
queue-based option above, and this ADR would be superseded rather than amended.

**Watch.** `order_placement_failures_total{reason="insufficient_stock"}` shows
demand exceeding inventory. Lock waits show up as p99 latency on
`POST /api/v1/orders` in `http_request_duration_seconds`. If p99 climbs while
the p50 stays flat, contention is the first suspect.
