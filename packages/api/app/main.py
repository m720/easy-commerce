import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import http_exception_handler, validation_exception_handler
from app.routers import auth, users, categories, tags, products, reviews, wishlist, addresses, coupons, cart, orders, analytics

app = FastAPI(
    title="Ecommerce API",
    description="Full-featured ecommerce REST API built with FastAPI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}
