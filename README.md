# Ecommerce Platform

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)  
[![Node](https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg)](https://nodejs.org/)  
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)  

A full-stack, production-ready e-commerce platform built with FastAPI and React. Features a complete shopping experience for customers and a comprehensive admin dashboard with analytics.

## 🏗️ Architecture

```
ecommerce/
├── shared-docs/              # Shared documentation between packages
│   ├── API_DOCS.md
│   └── ARCHITECTURE.md
├── .github/
│   └── workflows/            # CI/CD pipelines
│       ├── ci.yml
│       └── lint.yml
├── packages/
│   ├── api/                 # FastAPI backend
│   │   ├── app/
│   │   │   └── static/      # Product photos served at /static
│   │   ├── tests/
│   │   ├── alembic/
│   │   ├── scripts/         # Product photo generator
│   │   ├── seed.py
│   │   └── [other backend files]
│   └── web/                # React + TypeScript frontend
│       ├── src/
│       ├── public/
│       └── [other frontend files]
```

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI 0.115, Python 3.12, SQLAlchemy 2.0 |
| Database | PostgreSQL 16, Alembic migrations |
| Auth | JWT (python-jose), Bcrypt |
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

It generates 64 orders with a guaranteed spread across all six statuses, and
deliberately covers the awkward states as well as the happy path — an order with
no account attached, an order with no address snapshot, a line item whose variant
was since deleted, products with no category / photos / description / variants, an
empty category, an unused tag, an empty cart and wishlist, a deactivated user, an
unlabelled address, and coupons that are expired, retired and fully redeemed. The
script prints the status breakdown and the covered edge cases when it finishes.

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

## 📖 Documentation

See [API Reference](packages/api/docs/API_REFERENCE.md) for complete endpoint documentation.

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
