"""Request context + telemetry middleware.

One pass over every request does three things:

1. Establishes (or adopts) the correlation ID, so every log line, audit row and
   downstream call for this request shares one ``request_id``.
2. Emits a single structured access log line with method, route, status and
   duration.
3. Records the Prometheus request counter/histogram.

The ID is adopted from the inbound ``X-Request-ID`` header when present — that
is what lets a trace span a gateway, this API, and any service it calls — and
is echoed back on the response so clients can quote it in bug reports.
"""

import time
from typing import Optional

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings
from app.core import metrics
from app.core.logging import (
    get_logger,
    new_request_id,
    set_request_id,
    set_user_id,
)
from app.core.security import decode_token

logger = get_logger("app.request")

# Health and scrape endpoints are noisy and uninteresting; keep them out of the
# access log (they still count towards metrics).
_LOG_EXCLUDED_PATHS = frozenset({"/health", "/metrics"})


def _caller_from_token(request: Request) -> Optional[str]:
    """Best-effort user ID for the log context, from the bearer token.

    Identity has to be established *here* rather than in the auth dependency:
    sync endpoints and their dependencies each run in their own threadpool
    context, so a contextvar set inside `get_current_user` is invisible both to
    the endpoint and to this middleware. Setting it once on the outer context
    means every downstream frame — dependencies, handler, background tasks —
    inherits it.

    This is for attribution in logs only. It verifies the signature but does
    not check that the user exists or is active; `get_current_user` remains the
    authority for access control.
    """
    header = request.headers.get("authorization")
    if not header or not header.lower().startswith("bearer "):
        return None
    try:
        return decode_token(header.split(" ", 1)[1].strip())
    except Exception:  # noqa: BLE001 - never fail a request over a log field
        return None


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        header = settings.REQUEST_ID_HEADER
        incoming = request.headers.get(header)
        # Never trust an inbound ID blindly: cap the length so a hostile client
        # cannot bloat every log line downstream of us.
        request_id = incoming[:64] if incoming else new_request_id()

        set_request_id(request_id)
        set_user_id(_caller_from_token(request))
        request.state.request_id = request_id

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers[header] = request_id
            return response
        except Exception:
            # Unhandled errors still get a log line and a metric before the
            # exception propagates to Starlette's error handler.
            logger.exception(
                "request failed",
                extra={
                    "http_method": request.method,
                    "http_path": request.url.path,
                    "http_status": status_code,
                },
            )
            raise
        finally:
            duration = time.perf_counter() - start
            route = metrics.route_template(request)

            if metrics.enabled():
                metrics.http_requests_total.labels(
                    method=request.method, route=route, status=str(status_code)
                ).inc()
                metrics.http_request_duration_seconds.labels(
                    method=request.method, route=route
                ).observe(duration)

            if request.url.path not in _LOG_EXCLUDED_PATHS:
                logger.info(
                    "request completed",
                    extra={
                        "http_method": request.method,
                        "http_route": route,
                        "http_path": request.url.path,
                        "http_status": status_code,
                        "duration_ms": round(duration * 1000, 2),
                        "client_ip": request.client.host if request.client else None,
                        # user_id is added by the formatter from the log context.
                    },
                )

            set_request_id(None)
            set_user_id(None)
