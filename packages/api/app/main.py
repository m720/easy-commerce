import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.core import metrics
from app.core.cache import get_client as get_cache_client
from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.core.logging import configure_logging, get_logger
from app.middleware.observability import RequestContextMiddleware
from app.routers import (
    auth, users, categories, tags, products, reviews, wishlist, addresses,
    coupons, cart, orders, analytics, audit,
)

configure_logging()
logger = get_logger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Connect the cache eagerly so a misconfigured Redis shows up in the
    # startup logs rather than as a surprise on the first cache miss.
    cache_ready = get_cache_client() is not None
    logger.info(
        "api starting",
        extra={
            "environment": settings.ENVIRONMENT,
            "cache_enabled": cache_ready,
            "read_replica": bool(settings.DATABASE_REPLICA_URL),
            "metrics_enabled": settings.METRICS_ENABLED,
            "rate_limiting": settings.RATE_LIMIT_ENABLED,
        },
    )
    yield
    logger.info("api shutting down")


app = FastAPI(
    title="Ecommerce API",
    description="Full-featured ecommerce REST API built with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Middleware order matters: this is added last of the two below and therefore
# runs outermost, so CORS-rejected and preflight requests still get a
# correlation ID and show up in metrics.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[settings.REQUEST_ID_HEADER, "Idempotency-Replayed", "Retry-After"],
)
app.add_middleware(RequestContextMiddleware)

# Static assets (seeded product photos live under app/static/products)
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Routers
PREFIX = "/api/v1"
app.include_router(auth.router, prefix=PREFIX)
app.include_router(users.router, prefix=PREFIX)
app.include_router(categories.router, prefix=PREFIX)
app.include_router(tags.router, prefix=PREFIX)
app.include_router(products.router, prefix=PREFIX)
app.include_router(reviews.router, prefix=PREFIX)
app.include_router(wishlist.router, prefix=PREFIX)
app.include_router(addresses.router, prefix=PREFIX)
app.include_router(coupons.router, prefix=PREFIX)
app.include_router(cart.router, prefix=PREFIX)
app.include_router(orders.router, prefix=PREFIX)
app.include_router(analytics.router, prefix=PREFIX)
app.include_router(audit.router, prefix=PREFIX)


@app.get("/health", tags=["Health"])
def health():
    """Liveness probe: is the process up? Deliberately dependency-free.

    A health check that touches the database will fail a whole fleet during a
    brief DB blip and take the service down with it. Readiness — "can this
    instance serve traffic?" — is a separate question answered by /health/ready.
    """
    return {"status": "ok"}


@app.get("/health/ready", tags=["Health"])
def readiness(response: Response):
    """Readiness probe: can this instance reach its dependencies?

    Redis being down is reported but not disqualifying — the cache is optional
    by design and the API serves fine without it.
    """
    from sqlalchemy import text
    from app.database.base import SessionLocal

    checks: dict[str, str] = {}
    ready = True

    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:  # noqa: BLE001
        checks["database"] = f"error: {exc}"
        ready = False
        logger.error("readiness check failed", extra={"dependency": "database", "error": str(exc)})
    finally:
        db.close()

    if settings.CACHE_ENABLED and settings.REDIS_URL:
        client = get_cache_client()
        try:
            if client is None:
                raise RuntimeError("not connected")
            client.ping()
            checks["cache"] = "ok"
        except Exception as exc:  # noqa: BLE001
            checks["cache"] = f"degraded: {exc}"
    else:
        checks["cache"] = "disabled"

    if not ready:
        response.status_code = 503
    return {"status": "ready" if ready else "not_ready", "checks": checks}


@app.get("/metrics", tags=["Observability"], include_in_schema=False)
def prometheus_metrics():
    """Prometheus scrape endpoint.

    Unauthenticated on purpose — it is meant to be reachable by the scraper on
    the internal network and blocked at the ingress, which is the conventional
    deployment. Nothing here is customer data: labels are route templates and
    counter names only.
    """
    if not settings.METRICS_ENABLED:
        return Response(status_code=404)
    return Response(content=metrics.render(), media_type=metrics.CONTENT_TYPE)
