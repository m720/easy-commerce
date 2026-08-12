"""Prometheus metrics.

Exposes the three signals you actually page on — request latency, error rate,
and DB pool saturation — plus a handful of domain counters that make checkout
incidents diagnosable (idempotent replays, stock conflicts, cache hit ratio,
rate-limit rejections).

Cardinality note: HTTP labels use the *route template*
(``/api/v1/products/{product_id}``), never the raw path. Labelling by raw path
would mint one time series per product ID and melt the scrape target.
"""

from typing import Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry as _Registry

from app.config import settings

# Dedicated registry rather than the global default: tests can build a fresh
# app without tripping duplicate-timeseries errors on re-import.
REGISTRY: _Registry = CollectorRegistry()

CONTENT_TYPE = "text/plain; version=0.0.4; charset=utf-8"

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests.",
    ["method", "route", "status"],
    registry=REGISTRY,
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds.",
    ["method", "route"],
    # Buckets tuned for a web API: sub-100ms is the happy path, 5s is a timeout.
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

db_pool_connections = Gauge(
    "db_pool_connections",
    "SQLAlchemy connection pool state by kind (in_use, available, overflow).",
    ["pool", "state"],
    registry=REGISTRY,
)

orders_placed_total = Counter(
    "orders_placed_total",
    "Orders successfully written.",
    registry=REGISTRY,
)

order_placement_failures_total = Counter(
    "order_placement_failures_total",
    "Checkout attempts rejected, by reason.",
    ["reason"],
    registry=REGISTRY,
)

idempotent_replays_total = Counter(
    "idempotent_replays_total",
    "Checkout requests served from a stored idempotent response.",
    ["endpoint"],
    registry=REGISTRY,
)

cache_operations_total = Counter(
    "cache_operations_total",
    "Cache lookups by outcome (hit, miss, error) and namespace.",
    ["namespace", "outcome"],
    registry=REGISTRY,
)

cache_invalidations_total = Counter(
    "cache_invalidations_total",
    "Cache namespace invalidations triggered by writes.",
    ["namespace"],
    registry=REGISTRY,
)

rate_limit_rejections_total = Counter(
    "rate_limit_rejections_total",
    "Requests rejected by the rate limiter, by scope.",
    ["scope"],
    registry=REGISTRY,
)

audit_events_total = Counter(
    "audit_events_total",
    "Admin actions written to the audit log, by action.",
    ["action"],
    registry=REGISTRY,
)


def observe_pool(engine, pool_name: str = "primary") -> None:
    """Sample SQLAlchemy pool state at scrape time.

    Gauges are read on demand rather than tracked on every checkout/checkin —
    the pool already keeps these counters, so sampling avoids hot-path work.
    """
    pool = getattr(engine, "pool", None)
    if pool is None:
        return
    try:
        db_pool_connections.labels(pool=pool_name, state="in_use").set(pool.checkedout())
        db_pool_connections.labels(pool=pool_name, state="available").set(pool.checkedin())
        overflow = pool.overflow()
        # QueuePool.overflow() is negative until the base pool is exhausted.
        db_pool_connections.labels(pool=pool_name, state="overflow").set(max(overflow, 0))
    except (AttributeError, NotImplementedError):
        # NullPool/StaticPool (tests, alembic) expose no counters. Nothing to report.
        return


def render() -> bytes:
    """Serialise the registry in Prometheus text exposition format."""
    from app.database.base import engine, read_engine

    observe_pool(engine, "primary")
    if read_engine is not None:
        observe_pool(read_engine, "replica")
    return generate_latest(REGISTRY)


def route_template(request) -> str:
    """Resolve the matched route pattern, falling back to a constant.

    Unmatched paths (404 scans, probes) all collapse to ``<unmatched>`` so a
    scanner cannot inflate cardinality.
    """
    route = request.scope.get("route")
    path: Optional[str] = getattr(route, "path", None)
    if path:
        return path
    return "<unmatched>"


def enabled() -> bool:
    return settings.METRICS_ENABLED
