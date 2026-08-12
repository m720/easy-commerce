# 3. Idempotency keys for checkout

Date: 2026-08-12

## Status

Accepted.

## Context

`POST /api/v1/orders` is not safe to retry, and clients retry anyway.

The failure needs no unusual conditions. A customer on mobile taps *Place
order*; the API writes the order and commits; the response is lost — connection
dropped, TLS timeout, load balancer recycled, app backgrounded. The client sees
a failure and does the natural thing: it sends the request again. Now there are
two orders, two stock decrements, and — once a payment provider is wired in —
two charges.

Everything upstream of us retries too. HTTP client libraries retry on timeout.
Load balancers retry idle connections. Users double-tap buttons. **The server
cannot distinguish "the customer wants a second order" from "the customer's
first order got lost" without being told.**

Notably, the row-level locking in ADR-0001 does not help: both requests are
perfectly correct, sequential transactions. Concurrency control prevents
interleaving; it does not prevent duplication.

## Decision

Support the industry-standard `Idempotency-Key` header (Stripe, Adyen, PayPal
all expose the same contract): the client generates a key per logical
operation, and the server guarantees at most one side effect per key.

State is a table, `idempotency_keys`, with **a unique constraint on
`(user_id, endpoint, key)`**:

```
POST /orders + Idempotency-Key
        │
        ├─ INSERT reservation ──► wins → run checkout
        │                                   ├─ success → store response, mark completed
        │                                   └─ failure → delete reservation (retryable)
        │
        └─ unique violation ────► inspect the existing row
                                     ├─ completed + same body → replay stored response (201)
                                     ├─ in_progress          → 409, Retry-After
                                     └─ different body       → 422
```

Design points, each chosen against a specific failure:

* **The unique index is the concurrency control.** A check-then-insert has a
  race window wide enough for two simultaneous retries to both pass. `INSERT`
  has no window: the database picks a winner.
* **The reservation commits before the handler runs.** If the process dies
  mid-checkout, the retry sees `in_progress` and gets a 409 instead of placing
  a second order. Choosing the safe side of an ambiguous crash: a customer
  retrying is a nuisance, a customer double-charged is an incident.
* **Failures release the key.** A checkout rejected for an empty cart or a bad
  address has no side effect to protect. Holding the key would strand a client
  that fixed its input behind its own reservation.
* **Reuse with a different body is a 422, not a replay.** Returning the first
  order for a genuinely different request would hide a client bug behind an
  apparently successful response. The fingerprint is a SHA-256 over the
  canonicalised body.
* **Scoped per user.** One customer's key can never collide with — or replay —
  another's order.
* **Keys expire (24h default).** Long enough to cover any realistic retry,
  short enough that the table stays small.

The header remains **optional** (`IDEMPOTENCY_REQUIRED=false`) so existing
clients keep working; the flag flips to required once every client sends one.

## Alternatives considered

**Deduplicate on request content: reject an identical cart within N seconds.**
No client change needed. Rejected as both wrong directions at once — it blocks
a customer legitimately ordering the same thing twice, and it misses a
duplicate that arrives after the window. Guessing intent from content instead
of being told it.

**Client-generated order IDs (the client picks the primary key).** Elegant, and
it makes the write naturally idempotent. Rejected because it hands ID
allocation to untrusted input, leaks nothing useful to us about *which*
duplicate won, and stores no response to replay — the retry gets a conflict
error rather than the order it asked for.

**Redis instead of Postgres for key state.** Faster, with TTL for free.
Rejected because it splits the durability story: the reservation must survive
the same crash as the order it protects, and "the cache lost its data" would
mean "we might double-charge". Postgres already provides the guarantee; the
extra dependency buys latency we do not need on a checkout write.

**Idempotency at the gateway/proxy.** Correct place in a large system, and it
would cover every endpoint uniformly. Rejected here because we do not control a
gateway and the response body must come from the same store as the order write.

## Consequences

**Good.** A network retry is safe: same key in, same order out, no second
charge. The stored response makes the retry indistinguishable from success from
the client's perspective — no special-case handling, no "check whether it
actually worked" round trip.

**Good.** `idempotent_replays_total` is a genuinely useful production signal.
A rising replay rate means clients are timing out before we respond, which is a
latency problem surfacing as a correctness metric.

**Bad.** A crash between the reservation and the response leaves a stuck
`in_progress` row, and that key returns 409 until the TTL sweep clears it. The
client's escape is a fresh key, which is correct but requires the client to
distinguish 409 from a retryable error. A sweeper job (`purge_expired`) exists;
scheduling it is deployment work, not application code.

**Bad.** Two extra round trips on the checkout path (reserve, complete) plus a
JSONB copy of the response. Measured against a transaction that already writes
an order, its items and stock decrements, this is noise — but it is not free.

**Bad.** Correctness depends on clients generating keys correctly: stable
across retries of one logical operation, fresh for each new one. A client that
reuses a key for a genuinely new order gets a 422 rather than an order, which
is loud (good) but is still a client-side failure mode we cannot prevent.
Documented in the endpoint's OpenAPI description.
