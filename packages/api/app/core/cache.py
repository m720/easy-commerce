"""Cache-aside layer over Redis for the read-heavy catalogue endpoints.

Two properties matter more than raw hit rate here:

**Failure is not an outage.** Redis is a latency optimisation, not a source of
truth. Every operation is wrapped so that a connection error degrades to a
direct database read instead of a 500. The alternative — a cache outage taking
down the storefront — is the classic way a "performance improvement" becomes an
incident.

**Invalidation is O(1), not a key scan.** Each namespace carries a version
counter in Redis. Cache keys embed the current version, so an admin write only
has to ``INCR`` the counter to orphan every derived key at once — no ``KEYS``
scan (which blocks the server) and no attempt to enumerate the filter
combinations a list endpoint can produce. Orphaned entries expire on their TTL.

See docs/adr/0004-cache-aside-with-version-invalidation.md.
"""

import json
from typing import Any, Callable, Optional

from app.config import settings
from app.core import metrics
from app.core.logging import get_logger

logger = get_logger("app.cache")

CATALOG_NAMESPACE = "catalog"

_client: Optional[Any] = None
_client_initialised = False

# Fallback version counters, used when Redis is unavailable. They keep the key
# builder total; they intentionally do not synchronise across processes.
_local_versions: dict[str, int] = {}


def get_client():
    """Lazily connect to Redis. Returns None when caching is unavailable."""
    global _client, _client_initialised

    if _client_initialised:
        return _client

    _client_initialised = True
    if not settings.CACHE_ENABLED or not settings.REDIS_URL:
        _client = None
        return None

    try:
        import redis

        client = redis.Redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
            health_check_interval=30,
        )
        client.ping()
        _client = client
        logger.info("cache connected", extra={"backend": "redis"})
    except Exception as exc:  # noqa: BLE001 - any failure means "no cache"
        logger.warning(
            "cache unavailable, serving reads from the database",
            extra={"error": str(exc)},
        )
        _client = None
    return _client


def reset_client() -> None:
    """Drop the memoised client. Used by tests and after config changes."""
    global _client, _client_initialised
    _client = None
    _client_initialised = False
    _local_versions.clear()


def _version(namespace: str) -> int:
    client = get_client()
    if client is None:
        return _local_versions.get(namespace, 1)
    try:
        raw = client.get(f"{namespace}:version")
        return int(raw) if raw else 1
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache version read failed", extra={"error": str(exc)})
        return _local_versions.get(namespace, 1)


def build_key(namespace: str, *parts: Any) -> str:
    """Version-scoped cache key: ``catalog:v3:products:featured=true``."""
    suffix = ":".join(str(p) for p in parts if p is not None)
    return f"{namespace}:v{_version(namespace)}:{suffix}"


def invalidate(namespace: str = CATALOG_NAMESPACE) -> None:
    """Orphan every key in a namespace by bumping its version counter."""
    if metrics.enabled():
        metrics.cache_invalidations_total.labels(namespace=namespace).inc()

    client = get_client()
    if client is None:
        _local_versions[namespace] = _local_versions.get(namespace, 1) + 1
        return
    try:
        version_key = f"{namespace}:version"
        pipe = client.pipeline()
        # Materialise the implicit v1 first: INCR on a missing key yields 1,
        # which is the version already baked into live cache keys — the bump
        # would be a no-op and serve stale data.
        pipe.set(version_key, 1, nx=True)
        pipe.incr(version_key)
        pipe.execute()
        logger.info("cache invalidated", extra={"namespace": namespace})
    except Exception as exc:  # noqa: BLE001
        logger.warning("cache invalidation failed", extra={"error": str(exc)})


def get_or_set(
    key: str,
    ttl: int,
    loader: Callable[[], Any],
    namespace: str = CATALOG_NAMESPACE,
) -> Any:
    """Return the cached JSON value for ``key``, otherwise load and store it.

    ``loader`` must return JSON-serialisable data (already-dumped Pydantic
    models, not ORM instances).
    """
    client = get_client()
    if client is None:
        return loader()

    try:
        cached = client.get(key)
        if cached is not None:
            if metrics.enabled():
                metrics.cache_operations_total.labels(namespace=namespace, outcome="hit").inc()
            return json.loads(cached)
        if metrics.enabled():
            metrics.cache_operations_total.labels(namespace=namespace, outcome="miss").inc()
    except Exception as exc:  # noqa: BLE001
        if metrics.enabled():
            metrics.cache_operations_total.labels(namespace=namespace, outcome="error").inc()
        logger.warning("cache read failed", extra={"cache_key": key, "error": str(exc)})
        return loader()

    value = loader()

    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:  # noqa: BLE001
        if metrics.enabled():
            metrics.cache_operations_total.labels(namespace=namespace, outcome="error").inc()
        logger.warning("cache write failed", extra={"cache_key": key, "error": str(exc)})

    return value
