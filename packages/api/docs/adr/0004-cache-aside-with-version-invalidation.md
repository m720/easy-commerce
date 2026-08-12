# 4. Cache-aside with version-counter invalidation

Date: 2026-08-12

## Status

Accepted.

## Context

Catalogue reads dominate traffic and barely change. `GET /products`,
`GET /products/featured` and `GET /products/{id}` are hit by every visitor,
serve near-identical results, and each one fans out into several queries —
products, plus eager-loaded variants, images, tags and category.

Meanwhile admin writes are rare but must be visible quickly. Nobody accepts
"the price updates within an hour"; a price change is the kind of stale read
that ends up in a support ticket or a chargeback.

The hard part of caching a *listing* endpoint is invalidation. The response
depends on search text, category, tag, price bounds, featured flag and
pagination — a combinatorial space. When a product changes, we cannot enumerate
which cached listings contained it.

## Decision

**Cache-aside** (the application reads the cache, falls back to the database,
writes back) over Redis, with invalidation by **namespace version counter**.

Every cache key embeds the current version of its namespace:

```
catalog:v7:products:q=None:cat=3:feat=True:skip=0:limit=20
        ▲
        └── INCR on any admin write
```

An admin write calls `cache.invalidate()`, which bumps `catalog:version`. Every
subsequent key lookup is built with `v8`, so every `v7` entry is instantly
unreachable and expires on its own TTL. One `INCR` invalidates the entire
derived space, whatever its shape.

Two further commitments:

**A cache failure is not an outage.** Every Redis call is wrapped; a connection
error logs, increments `cache_operations_total{outcome="error"}` and falls
through to the database. Redis is a latency optimisation, and a "performance
improvement" that takes the storefront down when it fails is a net loss. The
same applies at startup: an unset or unreachable `REDIS_URL` leaves the API
fully functional.

**TTLs stay short and below the S3 pre-signed URL expiry.** Listings 60s,
details 300s, against a 3600s signature lifetime. A cached response containing
an expired image URL would render a page of broken images — the cache must
never outlive the credentials embedded in what it stores.

## Alternatives considered

**Delete keys on write (`DEL` by pattern).** The obvious approach, and wrong at
two levels: enumerating which listing keys contain a product is impractical, and
the tool for finding them, `KEYS`/`SCAN` over a large keyspace, is exactly what
you are told never to run against a production Redis — `KEYS` blocks the single
threaded server for the duration of the scan.

**Tag-based invalidation (Redis sets mapping product → dependent keys).**
Precise: only the affected listings are dropped, so unrelated cached pages
survive a write. Rejected as premature — it adds a second data structure that
must be kept consistent with the first, and its benefit (higher hit rate right
after a write) only matters when writes are frequent. Admin writes here are
rare; throwing the namespace away costs one cold period per write.

**Short TTL only, no explicit invalidation.** Simplest possible thing. Rejected
because the staleness window is exactly the TTL, and the TTL that makes a price
change acceptable (a few seconds) is too short to cache usefully.

**Write-through caching.** Keeps the cache warm and consistent by writing both
stores together. Rejected because it makes the cache a participant in the write
path: a Redis failure now fails an admin's price update, converting an optional
dependency into a required one.

**HTTP caching (ETag / Cache-Control) at a CDN.** Complementary rather than
alternative, and genuinely the cheapest way to serve a catalogue at scale. Not
done here because it needs infrastructure this project does not yet have; the
version counter would map cleanly onto a CDN surrogate key if it does.

## Consequences

**Good.** Catalogue reads collapse to one Redis round trip on a hit. A write
invalidates everything derived from it in O(1), with no key enumeration and no
blocking commands.

**Good.** The cache is genuinely optional. Local development, tests and any
deployment without Redis run the same code path with `CACHE_ENABLED=false`.

**Bad.** Invalidation is coarse: changing one product's description drops every
cached listing, including unrelated ones. Every write is followed by a cold
period where reads hit the database. Acceptable while writes are rare; if admin
writes ever become frequent, the tag-based approach above is the upgrade.

**Bad.** Orphaned entries occupy memory until their TTL expires — bounded by
TTL × write rate, which is small, but it is real memory Redis must be sized
for.

**Bad.** Cached responses are read-time-independent: a cached listing shows the
same stock quantity to everyone for up to 60s, so a product can appear in stock
after selling out. Checkout re-validates stock under lock (ADR-0001), so this
is a display artefact rather than an oversell — but it is a display artefact
customers notice.

**Watch.** `cache_operations_total{outcome}` gives the hit ratio;
`cache_invalidations_total` gives write frequency. A hit ratio that collapses
usually means invalidations are outpacing TTLs — the signal that finer-grained
invalidation has become worth building.
