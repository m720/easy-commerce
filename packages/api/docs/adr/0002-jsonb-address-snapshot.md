# 2. JSONB address snapshot on orders

Date: 2026-08-12

## Status

Accepted.

## Context

An order ships to an address. A customer can edit or delete that address at any
time afterwards — they move house, they fix a typo, they clean up their account.

If `orders` holds a foreign key to `addresses`, then editing an address
**rewrites history**: the order that shipped to the old flat now claims it
shipped to the new one. That breaks dispute resolution ("prove where you sent
it"), breaks courier reconciliation, and quietly corrupts any report that
groups revenue by region. With `ON DELETE SET NULL`, deleting the address makes
the order's destination simply disappear.

This is the general problem of **transactional data referencing mutable master
data**. An order is a record of what was true at a moment; an address row is a
current fact about a customer. They have different lifecycles and must not be
the same object.

The same reasoning applies to the order lines already in this schema:
`order_items` copies `product_name`, `variant_name` and `unit_price` rather
than joining to the product. Renaming a product or repricing it must not
restate old orders.

## Decision

Store a **JSONB snapshot** of the shipping address on the order at checkout:

```python
shipping_address_snapshot = Column(JSONB, nullable=True)
```

The address rows remain the customer's editable address book. The snapshot is
the immutable shipping destination for that order.

JSONB (not `json`, not text): it is stored decomposed and binary, supports
indexing if a query ever needs one, and validates that the payload is real JSON
at write time.

## Alternatives considered

**Foreign key to `addresses`, addresses never mutated (soft-delete + new row
per edit).** Fully normalised and queryable. Rejected because it makes every
address edit an insert plus a re-point, leaves the table growing with revisions
nobody reads, and still needs a "which revision was current at order time"
rule — the snapshot with extra steps.

**Normalised `order_addresses` table (one row per order, columns for each
field).** The rigorous choice, and the right one if shipping addresses were
queried analytically — "orders by postal code" is an index scan rather than a
JSON extraction. Rejected for now because it adds a table and a join to serve a
field that is, in practice, only ever read back whole alongside its order. The
migration path is open: the snapshot has a stable key set, so backfilling a
normalised table from JSONB is a single `INSERT … SELECT`.

**Denormalised columns directly on `orders` (`shipping_street`,
`shipping_city`, …).** No join, no JSON. Rejected because address shape is not
universal — postal codes, states/provinces/prefectures and address lines differ
by country — and every new field is a migration on a large table. JSONB absorbs
shape variation, which is the one thing addresses reliably do.

## Consequences

**Good.** Orders are immutable records. Editing or deleting an address cannot
alter, or erase, where a past order shipped. Rendering an order needs no join.

**Bad.** The snapshot is unvalidated by the database: nothing stops a future
writer storing a different key set. The write path is a single function
(`order_service.place_order`), which is the mitigation, but it is a convention
rather than a constraint. A JSON schema check constraint would close this if the
shape ever drifts.

**Bad.** Querying inside the snapshot is more awkward and slower than a column
(`shipping_address_snapshot->>'country'` cannot use an ordinary B-tree index
without a dedicated expression index). Analytics that group orders by
geography will want either an expression index or the normalised table above.

**Accepted.** Storage duplication. An address copied per order is a few hundred
bytes against an order that already carries line items; not a consideration at
any plausible volume here.
