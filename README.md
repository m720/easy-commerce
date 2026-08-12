# Ecommerce Platform

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)  
[![Node](https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg)](https://nodejs.org/)  
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  

A full-stack, production-ready e-commerce platform built with FastAPI and React. Features a complete shopping experience for customers and a comprehensive admin dashboard with analytics.

## 🏗️ Architecture

```
ecommerce/
├── packages/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   ├── core/        # logging, metrics, cache, rate limiting, security
│   │   │   ├── middleware/  # request context + telemetry
│   │   │   ├── models/      # SQLAlchemy models
│   │   │   ├── routers/     # HTTP layer
│   │   │   ├── services/    # business logic (orders, idempotency, audit, …)
│   │   │   └── static/      # Product photos served at /static
│   │   ├── docs/
│   │   │   ├── adr/         # Architecture Decision Records
│   │   │   ├── ARCHITECTURE.md
│   │   │   ├── OPERATIONS.md
│   │   │   └── API_REFERENCE.md
│   │   ├── ops/             # Prometheus config + Grafana dashboards
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── scripts/         # Product photo generator
│   │   └── seed.py
│   └── web/                 # React + TypeScript frontend
│       ├── src/
│       └── public/
```

### Request flow

```mermaid
flowchart LR
    browser["Browser<br/>React"] --> lb["Load balancer<br/>sets X-Request-ID"]
    lb --> api["FastAPI workers<br/>stateless"]

    api -->|"writes + read-your-own-writes"| pg[("PostgreSQL<br/>primary")]
    api -.->|"catalogue reads"| replica[("Read replica<br/>planned")]
    api -->|"cache + rate limits"| redis[("Redis")]
    api -.->|"background tasks"| smtp["SMTP"]
    api --> s3["S3<br/>product images"]

    pg -. streaming replication .-> replica
    prom["Prometheus"] -.->|"scrape /metrics"| api
    prom --> graf["Grafana"]
    api -.->|"JSON logs on stdout"| logs["Log aggregator"]

    classDef planned stroke-dasharray: 5 5
    class replica planned
```

Checkout is the interesting path: a client-supplied `Idempotency-Key` makes it
retry-safe, and stock decrement, order write and cart clear commit as a single
transaction under row-level locks. The sequence diagram, the data model, and
the reasoning behind both live in
[packages/api/docs/ARCHITECTURE.md](packages/api/docs/ARCHITECTURE.md).

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0 |
| Database | PostgreSQL 16, Alembic migrations |
| Cache | Redis 7 (cache-aside, optional — degrades to direct DB reads) |
| Auth | JWT (python-jose), Bcrypt, rate-limited auth endpoints |
| Observability | Structured JSON logs, correlation IDs, Prometheus `/metrics`, Grafana |
| File Storage | AWS S3 with pre-signed URLs |
| Email | SMTP via Python `emails` |
| Frontend | React 19, TypeScript 5.9, Vite 7 |
| Styling | Tailwind CSS 4, Lucide React |
| State | Zustand 5, TanStack React Query 5 |

## 🌟 Features

### Customer Features
- Product browsing with filters (search, category, tag, price)
- Shopping cart with persistent storage
- Checkout flows with address selection and coupon codes
- Order history, tracking, and cancellation
- Wishlist management
- User reviews with admin moderation

### Admin Dashboard
- Product/Coupon/User/Category management
- Revenue analytics and top product reports
- Low-stock alerts
- CSV export functionality
- Return request approval workflow
- Audit trail of every privileged action (who changed a price, who approved a return)

### Operational Features
- **Retry-safe checkout** — `Idempotency-Key` on `POST /orders` means a network
  retry replays the original order instead of placing a second one
- **Request tracing** — one correlation ID per request, adopted from
  `X-Request-ID` or minted, stamped on every log line, audit entry and response
- **Metrics** — `/metrics` exposes request latency, error rate, DB pool usage
  and checkout-specific counters; Prometheus + Grafana ship in the compose file
- **Rate limiting** — login, registration and password change are capped per IP
  and per account
- **Caching** — Redis cache-aside on the catalogue with O(1) invalidation on
  admin writes

## 📦 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose (recommended) or PostgreSQL 16

### Setup

```bash
# Clone and navigate to project
cd ecommerce

# Backend setup (Option A: Docker)
cd packages/api
cp .env.example .env
docker-compose up

# Seed database on a separate terminal
docker-compose exec api python seed.py --yes

# Frontend setup
cd ../web
npm install
npm run dev
```

### API Endpoints
- Swagger UI: http://localhost:8000/docs
- API Base URL: http://localhost:8000/api/v1

## 🌱 Sample Data

`packages/api/seed.py` populates every table — users, addresses, categories, tags,
products with photos and variants, coupons, carts, wishlists, orders, order items,
reviews and return requests — so the storefront, admin dashboard and analytics
reports all have realistic content on a fresh checkout.

```bash
cd packages/api
python seed.py          # prompts before clearing existing rows
python seed.py --yes    # non-interactive
```

Seeding is destructive and idempotent: it truncates the tables above and rebuilds
them from a fixed random seed, so repeat runs give identical data.

| Account | Password | Role |
|---------|----------|------|
| `admin@example.com` | `admin1234` | admin |
| `alice@example.com` (and the other customers) | `password123` | user |

Product photos are flat-vector SVGs committed under `packages/api/app/static/products`
and served by the API at `/static/products/...`, so images work with no S3 bucket
and no network access. Regenerate them with:

```bash
python scripts/generate_product_images.py
```

If the API is not on `http://localhost:8000`, set `PUBLIC_BASE_URL` before seeding —
it is the origin baked into the stored photo URLs.

## 📊 Observability

```bash
cd packages/api
docker-compose --profile monitoring up
```

| Surface | URL | Notes |
|---------|-----|-------|
| Metrics | http://localhost:8000/metrics | Prometheus exposition format |
| Prometheus | http://localhost:9090 | Scrapes the API every 15s; alert rules included |
| Grafana | http://localhost:3001 | Dashboard pre-provisioned (`admin`/`admin` by default) |
| Liveness | http://localhost:8000/health | Dependency-free |
| Readiness | http://localhost:8000/health/ready | Checks Postgres; reports Redis as degraded |

Logs are JSON on stdout, one object per line, each carrying `request_id` (and
`user_id` once authenticated):

```json
{"timestamp":"2026-08-12T14:22:41+0000","level":"INFO","logger":"app.orders",
 "message":"order placed","service":"ecommerce-api","request_id":"9f2c…",
 "user_id":"3a1b…","order_id":"77e1…","total_amount":"149.98","item_count":2}
```

Set `LOG_FORMAT=console` for readable local development output.

## 📖 Documentation

| Document | What it covers |
|----------|----------------|
| [Architecture](packages/api/docs/ARCHITECTURE.md) | Deployment topology, checkout sequence, data model, request lifecycle |
| [ADRs](packages/api/docs/adr/README.md) | Decisions with trade-offs: stock locking, address snapshots, idempotency, caching, read replicas |
| [Operations](packages/api/docs/OPERATIONS.md) | Runbook: alerts, dashboards, scaling levers, common incidents |
| [API Reference](packages/api/docs/API_REFERENCE.md) | Complete endpoint documentation |

## 🔐 Environment Variables

Configure `.env`:
```bash
DATABASE_URL=postgresql://postgres:password@localhost:5432/ecommerce
SECRET_KEY=your-secret-key-change-in-production
AWS_ACCESS_KEY_ID=your-access-key
# See packages/api/.env.example for all options
```

## 🧪 Testing

```bash
# Backend tests
cd packages/api
pytest

# Frontend tests
cd ../web
npm run test
```

## 📄 License

MIT
