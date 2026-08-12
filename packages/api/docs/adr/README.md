# Architecture Decision Records

Short documents capturing decisions that were expensive to make and would be
expensive to reverse. Each one states the forces at play, the option chosen,
the options rejected and why, and the consequences we accepted — including the
ones we are not happy about.

The format is [Michael Nygard's](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions).
Records are immutable: when a decision changes, a new ADR supersedes the old
one rather than editing history.

| # | Title | Status |
|---|-------|--------|
| [0001](0001-row-level-locking-for-stock.md) | Row-level locking for stock decrement | Accepted |
| [0002](0002-jsonb-address-snapshot.md) | JSONB address snapshot on orders | Accepted |
| [0003](0003-idempotency-keys-for-checkout.md) | Idempotency keys for checkout | Accepted |
| [0004](0004-cache-aside-with-version-invalidation.md) | Cache-aside with version-counter invalidation | Accepted |
| [0005](0005-read-replica-routing.md) | Read replica routing for catalogue traffic | Accepted |

## When to write one

Write an ADR when the decision is hard to reverse (schema shape, consistency
model, a dependency that becomes load-bearing), when reasonable engineers would
disagree, or when the reasoning will not be obvious from the code six months
from now. Do not write one for choices the code already explains.
