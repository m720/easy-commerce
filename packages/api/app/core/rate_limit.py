"""Fixed-window rate limiting for authentication endpoints.

Brute-forcing `/auth/login` is the cheapest attack against any commerce API, so
login and registration are capped per client identity.

Backend selection is deliberate: Redis when configured (counters are shared by
every API worker, which is the only way a limit means anything behind a load
balancer), otherwise an in-process dictionary. The in-process path is a
degraded mode — it still blocks a naive attacker hitting one worker, and it is
documented as such rather than silently pretending to be a global limit.

The window is fixed rather than sliding: it costs one ``INCR`` plus one
``EXPIRE``, and the worst case (2x the limit across a window boundary) is
irrelevant at brute-force timescales.
"""

import time
from typing import Optional

from fastapi import HTTPException, Request, status

from app.config import settings
from app.core import metrics
from app.core.cache import get_client
from app.core.logging import get_logger

logger = get_logger("app.rate_limit")

# scope-key -> (window_started_at, count)
_local_counters: dict[str, tuple[float, int]] = {}


def reset_local_counters() -> None:
    """Test hook — clears the in-process fallback state."""
    _local_counters.clear()


def client_identity(request: Request) -> str:
    """Best-effort caller identity.

    ``X-Forwarded-For`` is only meaningful when a trusted proxy sets it; behind
    an untrusted network a client can forge it. We take the left-most entry
    (the original client per the RFC) and fall back to the socket peer.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _hit_redis(key: str, window: int) -> Optional[int]:
    client = get_client()
    if client is None:
        return None
    try:
        pipe = client.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        count, _ = pipe.execute()
        return int(count)
    except Exception as exc:  # noqa: BLE001
        logger.warning("rate limit backend failed", extra={"error": str(exc)})
        return None


def _hit_local(key: str, window: int) -> int:
    now = time.monotonic()
    started, count = _local_counters.get(key, (now, 0))
    if now - started >= window:
        started, count = now, 0
    count += 1
    _local_counters[key] = (started, count)
    return count


def check(scope: str, identity: str, limit: int, window: int) -> None:
    """Count one attempt; raise 429 once the window budget is spent."""
    if not settings.RATE_LIMIT_ENABLED:
        return

    key = f"ratelimit:{scope}:{identity}"
    count = _hit_redis(key, window)
    if count is None:
        count = _hit_local(key, window)

    if count > limit:
        if metrics.enabled():
            metrics.rate_limit_rejections_total.labels(scope=scope).inc()
        logger.warning(
            "rate limit exceeded",
            extra={"scope": scope, "identity": identity, "limit": limit, "window": window},
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(window)},
        )


class RateLimiter:
    """FastAPI dependency that limits by caller IP.

    Limits are read from settings on every call rather than captured at import
    time, so they stay tunable without a redeploy (and testable without
    reloading the router module)::

        @router.post("/login", dependencies=[Depends(login_ip_limiter)])
    """

    def __init__(self, scope: str, limit_setting: str, window_setting: str):
        self.scope = scope
        self.limit_setting = limit_setting
        self.window_setting = window_setting

    @property
    def limit(self) -> int:
        return getattr(settings, self.limit_setting)

    @property
    def window(self) -> int:
        return getattr(settings, self.window_setting)

    def __call__(self, request: Request) -> None:
        check(self.scope, client_identity(request), self.limit, self.window)

    def check_identity(self, identity: str) -> None:
        """Apply the same budget to a non-IP identity (e.g. an email address)."""
        check(self.scope, identity, self.limit, self.window)


login_ip_limiter = RateLimiter(
    "login-ip", "RATE_LIMIT_LOGIN_MAX", "RATE_LIMIT_LOGIN_WINDOW"
)
# Keyed by account, so rotating source IPs does not buy an attacker more
# guesses against one victim's password.
login_account_limiter = RateLimiter(
    "login-account", "RATE_LIMIT_LOGIN_MAX", "RATE_LIMIT_LOGIN_WINDOW"
)
register_ip_limiter = RateLimiter(
    "register-ip", "RATE_LIMIT_REGISTER_MAX", "RATE_LIMIT_REGISTER_WINDOW"
)
password_change_limiter = RateLimiter(
    "password-change", "RATE_LIMIT_LOGIN_MAX", "RATE_LIMIT_LOGIN_WINDOW"
)
