"""Seed the database with a full sample data set.

Populates every table in the schema — users, addresses, categories, tags,
products with photos and variants, coupons, carts, wishlists, orders, order
items, reviews and return requests — so the storefront, the admin dashboard and
the analytics reports all have something realistic to show.

The product photos live in ``app/static/products`` and are served by the API at
``/static/products/...``; no S3 bucket or network access is required. Regenerate
them with ``python scripts/generate_product_images.py``.

Usage::

    python seed.py           # wipe the seeded tables and reseed
    python seed.py --yes     # same, without the confirmation prompt

Data is generated from a fixed random seed, so repeated runs produce the same
catalogue, orders and reviews.
"""
import argparse
import random
import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(__file__))

import bcrypt as _bcrypt
from sqlalchemy import null, text

from app.config import settings
from app.database.base import SessionLocal
from app.core.enums import CouponType, OrderStatus, ReturnStatus, UserRole
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.coupon import Coupon
from app.models.order import Order, OrderItem, ReturnRequest, ReturnRequestItem
from app.models.product import Product, ProductImage, ProductVariant
from app.models.review import Review
from app.models.tag import Tag
from app.models.user import User
from app.models.wishlist import Wishlist, WishlistItem

RNG = random.Random(20240517)
NOW = datetime.now(timezone.utc)

# Tables emptied before reseeding, children first.
SEEDED_TABLES = [
    "return_request_items",
    "return_requests",
    "order_items",
    "orders",
    "cart_items",
    "carts",
    "wishlist_items",
    "wishlists",
    "reviews",
    "product_tags",
    "product_images",
    "product_variants",
    "products",
    "tags",
    "categories",
    "coupons",
    "addresses",
    "users",
]

_password_cache: dict[str, str] = {}


def hash_password(password: str) -> str:
    # bcrypt is deliberately slow; the seed only uses a couple of distinct passwords.
    if password not in _password_cache:
        _password_cache[password] = _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
    return _password_cache[password]


def days_ago(days: float) -> datetime:
    return NOW - timedelta(days=days)


def image_url(slug: str, index: int) -> str:
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/static/products/{slug}-{index}.svg"


# ── Reference data ─────────────────────────────────────────────────────────

CATEGORIES = [
    ("Electronics", "electronics", "Laptops, audio, wearables and cameras."),
    ("Clothing", "clothing", "Everyday apparel and footwear."),
    ("Home & Kitchen", "home-kitchen", "Coffee gear, cookware and soft furnishings."),
    ("Books", "books", "Fiction, reference and design titles."),
    ("Sports & Outdoors", "sports-outdoors", "Packs, mats and trail equipment."),
    ("Beauty", "beauty", "Skincare and everyday grooming tools."),
    # Description omitted and no products yet: an empty category the admin has
    # created but not stocked.
    ("Gifts & Cards", "gifts-cards", None),
]

TAGS = [
    ("Sale", "sale"),
    ("New Arrival", "new-arrival"),
    ("Popular", "popular"),
    ("Eco-Friendly", "eco-friendly"),
    ("Premium", "premium"),
    ("Bestseller", "bestseller"),
    ("Limited Edition", "limited-edition"),
    ("Clearance", "clearance"),
    ("Back in Stock", "back-in-stock"),  # deliberately unused
]

USERS = [
    # email, full name, role, password, active, account age in days
    ("admin@example.com", "Admin User", UserRole.admin, "admin1234", True, 400),
    ("ops@example.com", "Priya Raman", UserRole.admin, "admin1234", True, 220),
    ("alice@example.com", "Alice Smith", UserRole.user, "password123", True, 365),
    ("bob@example.com", "Bob Jones", UserRole.user, "password123", True, 310),
    ("carla@example.com", "Carla Nguyen", UserRole.user, "password123", True, 268),
    ("dmitri@example.com", "Dmitri Petrov", UserRole.user, "password123", True, 204),
    ("erin@example.com", "Erin O'Connell", UserRole.user, "password123", True, 151),
    ("farid@example.com", "Farid Haddad", UserRole.user, "password123", True, 96),
    ("grace@example.com", "Grace Kim", UserRole.user, "password123", True, 47),
    ("hugo@example.com", "Hugo Almeida", UserRole.user, "password123", True, 12),
    ("ivy@example.com", "Ivy Watson", UserRole.user, "password123", False, 88),
]

# email -> list of (label, street, city, state, country, postal_code, is_default)
ADDRESSES = {
    "admin@example.com": [
        ("Office", "1 Commerce Way", "Austin", "TX", "USA", "78701", True),
    ],
    "ops@example.com": [
        # Unlabelled address — the label is optional in the schema and the UI.
        (None, "88 Warehouse Row", "Reno", "NV", "USA", "89501", True),
    ],
    "alice@example.com": [
        ("Home", "742 Evergreen Terrace", "Portland", "OR", "USA", "97205", True),
        ("Work", "500 SW Broadway, Suite 210", "Portland", "OR", "USA", "97205", False),
    ],
    "bob@example.com": [
        ("Home", "88 Fulton Street", "Brooklyn", "NY", "USA", "11201", True),
    ],
    "carla@example.com": [
        ("Home", "19 Rue des Lilas", "Lyon", None, "France", "69003", True),
        ("Parents", "4 Chemin du Moulin", "Annecy", None, "France", "74000", False),
    ],
    "dmitri@example.com": [
        ("Home", "12 Kastanienallee", "Berlin", None, "Germany", "10435", True),
    ],
    "erin@example.com": [
        ("Home", "27 Harbour View", "Galway", None, "Ireland", "H91 X2P4", True),
    ],
    "farid@example.com": [
        ("Home", "310 Al Wasl Road", "Dubai", None, "UAE", "00000", True),
    ],
    "grace@example.com": [
        ("Home", "55 Bukit Timah Road", "Singapore", None, "Singapore", "229832", True),
    ],
    "hugo@example.com": [
        ("Home", "R. Augusta 240", "Lisbon", None, "Portugal", "1100-053", True),
    ],
    "ivy@example.com": [
        ("Home", "9 Pinehurst Lane", "Manchester", None, "United Kingdom", "M1 4BT", True),
    ],
}

# slug, name, category slug, tag slugs, featured, active, base price, image count,
# description, variants [(name, sku, price, stock[, low stock threshold])]
#
# A category slug of None, a description of None, an image count of 0 and an
# empty variant list are all valid and deliberately exercised below.
PRODUCTS = [
    (
        "probook-laptop-15", "ProBook Laptop 15", "electronics",
        ["popular", "new-arrival", "premium"], True, True, "999.99", 3,
        "A 15-inch aluminium notebook with an all-day battery, a colour-accurate display and enough headroom for builds, edits and everything in between.",
        [("8GB / 256GB", "LAPTOP-8-256", "799.99", 20),
         ("16GB / 512GB", "LAPTOP-16-512", "999.99", 15),
         ("32GB / 1TB", "LAPTOP-32-1T", "1399.99", 4, 3)],
    ),
    (
        "soundmax-wireless-headphones", "SoundMax Wireless Headphones", "electronics",
        ["sale", "popular"], False, True, "149.99", 3,
        "Over-ear active noise cancellation with 30 hours of playback, memory-foam cushions and multipoint pairing.",
        [("Midnight Black", "HP-BLACK", "149.99", 50),
         ("Cloud White", "HP-WHITE", "149.99", 30),
         ("Sage Green", "HP-SAGE", "159.99", 12)],
    ),
    (
        "pulse-smartwatch-series-5", "Pulse Smartwatch Series 5", "electronics",
        ["new-arrival", "bestseller"], True, True, "249.00", 2,
        "Continuous heart-rate and sleep tracking, built-in GPS and a always-on display that survives a full weekend off the charger.",
        [("40mm / Graphite", "PW-40-GR", "249.00", 25),
         ("44mm / Graphite", "PW-44-GR", "279.00", 18),
         ("44mm / Rose Gold", "PW-44-RS", "279.00", 3)],
    ),
    (
        "lumen-4k-action-camera", "Lumen 4K Action Camera", "electronics",
        ["popular"], False, True, "329.50", 2,
        "Pocket-sized 4K60 capture with in-body stabilisation, waterproof to 10 metres without a case.",
        [("Standard Kit", "CAM-STD", "329.50", 22),
         ("Adventure Bundle", "CAM-ADV", "419.00", 9)],
    ),
    (
        "classic-cotton-tshirt", "Classic Cotton T-Shirt", "clothing",
        ["eco-friendly", "new-arrival"], True, True, "24.99", 3,
        "A midweight tee cut from 100% organic combed cotton, pre-shrunk so it keeps its shape past the first wash.",
        [("White / S", "TS-W-S", "24.99", 100),
         ("White / M", "TS-W-M", "24.99", 100, 25),
         ("White / L", "TS-W-L", "24.99", 80),
         ("Black / M", "TS-B-M", "24.99", 90),
         ("Sage / L", "TS-S-L", "26.99", 35)],
    ),
    (
        "slim-fit-jeans", "Slim Fit Jeans", "clothing",
        ["popular", "clearance"], False, True, "59.99", 2,
        "Slim through the leg with a touch of stretch, in a mid-weight denim that breaks in fast.",
        [("Indigo / 30", "JN-I-30", "59.99", 40),
         ("Indigo / 32", "JN-I-32", "59.99", 40),
         ("Indigo / 34", "JN-I-34", "59.99", 28),
         ("Black / 32", "JN-K-32", "59.99", 35)],
    ),
    (
        "alpine-wool-sweater", "Alpine Wool Sweater", "clothing",
        ["premium", "bestseller"], False, True, "119.00", 2,
        "Crew-neck knit in traceable merino wool, warm enough for a cold platform and light enough to wear indoors.",
        [("Oatmeal / M", "SW-O-M", "119.00", 22),
         ("Oatmeal / L", "SW-O-L", "119.00", 17),
         ("Charcoal / M", "SW-C-M", "119.00", 5)],
    ),
    (
        "everyday-canvas-sneakers", "Everyday Canvas Sneakers", "clothing",
        ["sale", "popular"], False, True, "69.90", 3,
        "Vulcanised rubber sole, organic canvas upper and a padded collar that skips the break-in period.",
        [("US 8", "SN-8", "69.90", 24),
         ("US 9", "SN-9", "69.90", 31, 12),
         ("US 10", "SN-10", "69.90", 28),
         ("US 11", "SN-11", "69.90", 12)],
    ),
    (
        "barista-pro-espresso-machine", "Barista Pro Espresso Machine", "home-kitchen",
        ["premium", "bestseller"], True, True, "549.00", 3,
        "A 15-bar pump, PID temperature control and a built-in conical grinder — cafe shots without the cafe queue.",
        [("Stainless Steel", "ESP-SS", "549.00", 10, 10),
         ("Matte Black", "ESP-MB", "569.00", 5)],
    ),
    (
        "ceramic-pour-over-set", "Ceramic Pour-Over Set", "home-kitchen",
        ["eco-friendly"], False, True, "42.00", 2,
        "A stoneware dripper and 600ml carafe, glazed by hand and sized for two generous cups.",
        [("Cream", "POV-CR", "42.00", 40),
         ("Charcoal", "POV-CH", "42.00", 28)],
    ),
    (
        "cast-iron-skillet-12", 'Cast Iron Skillet 12"', "home-kitchen",
        ["bestseller"], False, True, "54.00", 2,
        "Pre-seasoned cast iron with a milled cooking surface, oven safe to 260°C and effectively unbreakable.",
        [("10 inch", "SKL-10", "44.00", 30),
         ("12 inch", "SKL-12", "54.00", 26)],
    ),
    (
        "linen-throw-blanket", "Linen Throw Blanket", "home-kitchen",
        ["eco-friendly", "sale"], False, True, "89.00", 2,
        "Stonewashed European flax with hand-knotted fringing — breathable in summer, layerable in winter.",
        [("Fog", "BLK-FOG", "89.00", 18),
         ("Clay", "BLK-CLAY", "89.00", 2)],
    ),
    (
        "the-lost-horizon", "The Lost Horizon", "books",
        ["sale"], False, True, "14.99", 2,
        "A gripping adventure novel set in the Himalayas, following a survey team that walks off every map they carry.",
        [("Paperback", "LH-PB", "14.99", 200),
         ("Hardcover", "LH-HC", "24.99", 50)],
    ),
    (
        "atlas-of-quiet-places", "Atlas of Quiet Places", "books",
        ["new-arrival", "popular"], True, True, "32.00", 2,
        "Forty essays and hand-drawn maps on the last genuinely quiet corners of a very loud world.",
        [("Hardcover", "AQP-HC", "32.00", 60),
         ("Collector's Edition", "AQP-CE", "58.00", 8)],
    ),
    (
        "the-pragmatic-kitchen", "The Pragmatic Kitchen", "books",
        ["bestseller"], False, True, "28.50", 2,
        "Ninety weeknight recipes built around eight techniques, with the reasoning spelled out for each one.",
        [("Hardcover", "PK-HC", "28.50", 45),
         ("Signed Copy", "PK-SG", "39.00", 5)],
    ),
    (
        "foundations-of-modern-design", "Foundations of Modern Design", "books",
        ["premium"], False, False, "45.00", 2,
        "A survey of the movements behind contemporary product design. Currently out of print pending a second edition.",
        [("Hardcover", "FMD-HC", "45.00", 0),
         ("Paperback", "FMD-PB", "29.00", 0)],
    ),
    (
        "trailhead-45l-backpack", "Trailhead 45L Backpack", "sports-outdoors",
        ["popular", "bestseller"], True, True, "179.00", 3,
        "A load-hauling weekend pack with an adjustable harness, roll-top closure and recycled ripstop shell.",
        [("Moss / 45L", "BP-MOSS-45", "179.00", 20),
         ("Slate / 45L", "BP-SLATE-45", "179.00", 14),
         ("Slate / 60L", "BP-SLATE-60", "209.00", 6)],
    ),
    (
        "grip-pro-yoga-mat", "Grip Pro Yoga Mat", "sports-outdoors",
        ["eco-friendly", "new-arrival"], False, True, "64.00", 2,
        "Natural tree rubber with a closed-cell top layer that stays grippy through a hot class. Ships with a carry strap.",
        [("4mm / Terracotta", "YM-4-TC", "64.00", 35),
         ("6mm / Forest", "YM-6-FR", "74.00", 21)],
    ),
    (
        "summit-insulated-bottle-1l", "Summit Insulated Bottle 1L", "sports-outdoors",
        ["sale", "popular"], False, True, "34.00", 2,
        "Double-walled stainless steel: 24 hours cold, 12 hours hot, and a lid that actually survives being dropped.",
        [("Steel", "BTL-ST", "34.00", 60, 20),
         ("Matte Black", "BTL-MB", "34.00", 44),
         ("Brick", "BTL-BR", "36.00", 4)],
    ),
    (
        "carbon-trekking-poles", "Carbon Trekking Poles", "sports-outdoors",
        ["premium"], False, True, "139.00", 2,
        "Three-section carbon poles with cork grips and flick locks, folding down small enough for a daypack.",
        [("Standard Pair", "TP-STD", "139.00", 16),
         ("Ultralight Pair", "TP-UL", "189.00", 7)],
    ),
    (
        "botanical-face-serum", "Botanical Face Serum", "beauty",
        ["new-arrival", "bestseller"], True, True, "48.00", 3,
        "A lightweight vitamin C and squalane serum in an amber glass dropper bottle. Fragrance free.",
        [("30ml", "SER-30", "48.00", 55),
         ("50ml", "SER-50", "72.00", 30)],
    ),
    (
        "rosewater-hydrating-mist", "Rosewater Hydrating Mist", "beauty",
        ["eco-friendly", "popular"], False, True, "26.00", 2,
        "Steam-distilled rosewater with aloe and glycerin, in a refillable bottle with a fine-mist pump.",
        [("100ml", "MST-100", "26.00", 70),
         ("200ml", "MST-200", "38.00", 25)],
    ),
    (
        "clay-purifying-mask", "Clay Purifying Mask", "beauty",
        ["sale"], False, True, "32.00", 2,
        "Kaolin and green clay with oat extract — draws out congestion in ten minutes without stripping the skin.",
        [("Original", "MSK-ORG", "32.00", 48),
         ("Sensitive", "MSK-SEN", "32.00", 3)],
    ),
    (
        "bamboo-bristle-brush-set", "Bamboo Bristle Brush Set", "beauty",
        ["eco-friendly", "limited-edition"], False, True, "58.00", 2,
        "Bamboo handles and vegan taklon bristles in a washable canvas roll. Made in a small annual run.",
        [("5-Piece Set", "BRS-5", "58.00", 26),
         ("9-Piece Set", "BRS-9", "92.00", 11)],
    ),
    (
        # No category and no photos: a non-physical product that never got
        # artwork, so listings fall back to the "No image" placeholder.
        "digital-gift-card", "Digital Gift Card", None,
        ["popular"], False, True, "50.00", 0,
        "Delivered by email within minutes, redeemable against anything in the store and valid for two years.",
        [("$25", "GC-25", "25.00", 999, 50),
         ("$50", "GC-50", "50.00", 999, 50),
         ("$100", "GC-100", "100.00", 999, 50)],
    ),
    (
        # No description and no variants: announced but not yet purchasable.
        "aurora-desk-lamp", "Aurora Desk Lamp", "home-kitchen",
        ["new-arrival"], False, True, "98.00", 2, None,
        [],
    ),
]

# code, type, value, min order, max uses, expires in days (None = never), active,
# starting used_count. Between them these cover every rejection branch in
# validate_coupon: inactive, expired, usage limit reached and minimum order.
COUPONS = [
    ("WELCOME10", CouponType.percent, "10", None, 1000, 365, True, 0),
    ("SAVE20", CouponType.fixed, "20", "100", 500, 90, True, 0),
    ("FREESHIP5", CouponType.fixed, "5", "25", None, 180, True, 0),
    ("SUMMER15", CouponType.percent, "15", "75", 200, 30, True, 0),
    ("VIP25", CouponType.percent, "25", "200", 50, 60, True, 0),
    ("SPRING10", CouponType.percent, "10", None, 300, -14, True, 41),  # expired
    ("LEGACY5", CouponType.fixed, "5", None, None, None, False, 118),  # retired
    ("FLASH30", CouponType.percent, "30", "150", 25, 21, True, 25),    # fully redeemed
]

REVIEW_COMMENTS = [
    (1, "Stopped working within a fortnight and I'm still waiting on a reply about the replacement."),
    (1, "Nothing like the listing. Packaging was damaged and the item inside was worse."),
    (2, "Underwhelming for the money. It does technically work, but I wouldn't buy it again."),
    (3, "Perfectly average. No real complaints, no real enthusiasm either."),
    (5, "Exactly what I hoped for. Shipping was quick and the packaging was minimal, which I appreciated."),
    (5, "Second one I've bought. The first is still going strong after two years of daily use."),
    (4, "Really solid overall. Knocking off a star only because the sizing runs slightly small."),
    (4, "Great quality for the price. Would have liked a couple more colour options."),
    (5, "Better in person than in the photos. Genuinely well made."),
    (3, "Does the job, but it feels a bit lighter than I expected from the description."),
    (4, "Arrived two days early and works perfectly. No complaints."),
    (5, "Bought this as a gift and ended up ordering a second for myself."),
    (2, "Mine arrived with a scuff on the side. Support sorted a replacement quickly, so not all bad."),
    (4, "Comfortable and holds up well. The finish attracts fingerprints, which is my only gripe."),
    (5, "Replaced a much more expensive one with this and honestly can't tell the difference."),
    (3, "Fine, but nothing special. It works as advertised."),
]

RETURN_REASONS = [
    "Ordered the wrong size — would like to exchange for the next size up.",
    "Arrived with a scratch on the casing.",
    "Not quite the colour shown in the photos.",
    "Received a duplicate of an item I already own.",
    "Stopped holding a charge after the first week.",
    "Changed my mind, item is unopened.",
]


# ── Seeding ────────────────────────────────────────────────────────────────

def _existing_row_count(db) -> int:
    total = 0
    for table in SEEDED_TABLES:
        total += db.execute(text(f"SELECT count(*) FROM {table}")).scalar() or 0
    return total


def _wipe(db) -> None:
    db.execute(text(f"TRUNCATE TABLE {', '.join(SEEDED_TABLES)} RESTART IDENTITY CASCADE"))


def seed(assume_yes: bool = False) -> None:
    db = SessionLocal()
    try:
        existing = _existing_row_count(db)
        if existing and not assume_yes and sys.stdin.isatty():
            print(f"The target database already holds {existing} rows across the seeded tables.")
            answer = input("Delete them and reseed? [y/N] ").strip().lower()
            if answer not in ("y", "yes"):
                print("Aborted; nothing was changed.")
                return
        if existing:
            print(f"Clearing {existing} existing rows...")
        _wipe(db)

        # ── Users ──────────────────────────────────────────────────────────
        users: dict[str, User] = {}
        for email, name, role, password, is_active, age in USERS:
            user = User(
                email=email,
                full_name=name,
                hashed_password=hash_password(password),
                role=role,
                is_active=is_active,
                created_at=days_ago(age),
            )
            users[email] = user
        db.add_all(users.values())
        db.flush()

        # ── Addresses ──────────────────────────────────────────────────────
        addresses: dict[str, list[Address]] = {}
        for email, entries in ADDRESSES.items():
            addresses[email] = []
            for label, street, city, state, country, postal, is_default in entries:
                address = Address(
                    user_id=users[email].id,
                    label=label,
                    street=street,
                    city=city,
                    state=state,
                    country=country,
                    postal_code=postal,
                    is_default=is_default,
                )
                addresses[email].append(address)
                db.add(address)
        db.flush()

        # ── Categories & tags ──────────────────────────────────────────────
        categories = {slug: Category(name=name, slug=slug, description=desc) for name, slug, desc in CATEGORIES}
        tags = {slug: Tag(name=name, slug=slug) for name, slug in TAGS}
        db.add_all(categories.values())
        db.add_all(tags.values())
        db.flush()

        # ── Products, photos and variants ──────────────────────────────────
        products: dict[str, Product] = {}
        variants: list[ProductVariant] = []
        for offset, (
            slug, name, category_slug, tag_slugs, featured, active,
            base_price, image_count, description, variant_specs,
        ) in enumerate(PRODUCTS):
            product = Product(
                name=name,
                description=description,
                base_price=Decimal(base_price),
                category_id=categories[category_slug].id if category_slug else None,
                is_featured=featured,
                is_active=active,
                # Stagger creation dates so "newest first" listings look natural.
                created_at=days_ago(300 - offset * 9),
                tags=[tags[t] for t in tag_slugs],
            )
            products[slug] = product
            db.add(product)
            db.flush()

            for i in range(image_count):
                db.add(ProductImage(
                    product_id=product.id,
                    s3_key=image_url(slug, i + 1),
                    is_primary=(i == 0),
                    sort_order=i,
                ))

            for spec in variant_specs:
                variant_name, sku, price, stock = spec[:4]
                variant = ProductVariant(
                    product_id=product.id,
                    name=variant_name,
                    sku=sku,
                    price=Decimal(price),
                    stock_quantity=stock,
                    # Most products use the default threshold; a few carry their own.
                    low_stock_threshold=spec[4] if len(spec) > 4 else 5,
                )
                variants.append(variant)
                db.add(variant)
        db.flush()

        # ── Coupons ────────────────────────────────────────────────────────
        coupons: dict[str, Coupon] = {}
        for code, ctype, value, min_amount, max_uses, expires_in, is_active, used in COUPONS:
            coupon = Coupon(
                code=code,
                type=ctype,
                value=Decimal(value),
                min_order_amount=Decimal(min_amount) if min_amount else None,
                max_uses=max_uses,
                used_count=used,
                expires_at=NOW + timedelta(days=expires_in) if expires_in is not None else None,
                is_active=is_active,
            )
            coupons[code] = coupon
            db.add(coupon)
        db.flush()

        # Coupons customers may have used at checkout (redeemable ones only).
        redeemable = [coupons[c] for c in ("WELCOME10", "SAVE20", "FREESHIP5", "SUMMER15", "VIP25")]
        customers = [users[email] for email, _, role, _, active, _ in USERS if role == UserRole.user and active]
        sellable = [v for v in variants if v.stock_quantity > 0]

        # ── Orders & order items ───────────────────────────────────────────
        # An explicit plan rather than weighted random draws, so every status is
        # guaranteed a meaningful number of orders instead of whatever the RNG
        # happens to produce. Shaped like a real funnel: most orders end up
        # delivered, fewer are still in flight, a minority fail or come back.
        status_plan = (
            [OrderStatus.delivered] * 26
            + [OrderStatus.shipped] * 10
            + [OrderStatus.processing] * 8
            + [OrderStatus.cancelled] * 7
            + [OrderStatus.returned] * 7
            + [OrderStatus.pending] * 6
        )
        RNG.shuffle(status_plan)
        orders: list[Order] = []
        purchases: dict[tuple, list] = {}  # (user_id, product_id) -> [order, ...]

        for status in status_plan:
            customer = RNG.choice(customers)
            chosen = RNG.sample(sellable, RNG.randint(1, 3))
            placed_at = days_ago(RNG.uniform(1, 165))

            order_items = []
            subtotal = Decimal("0")
            for variant in chosen:
                quantity = RNG.randint(1, 3)
                unit_price = Decimal(str(variant.price))
                line_total = unit_price * quantity
                subtotal += line_total
                order_items.append(OrderItem(
                    variant_id=variant.id,
                    product_name=variant.product.name,
                    variant_name=variant.name,
                    unit_price=unit_price,
                    quantity=quantity,
                    subtotal=line_total,
                ))

            # Apply a coupon to roughly a third of orders, using the same rules
            # the checkout enforces.
            coupon = None
            discount = Decimal("0")
            if RNG.random() < 0.35:
                candidate = RNG.choice(redeemable)
                min_amount = Decimal(str(candidate.min_order_amount)) if candidate.min_order_amount else Decimal("0")
                if subtotal >= min_amount:
                    coupon = candidate
                    if coupon.type == CouponType.percent:
                        discount = (subtotal * Decimal(str(coupon.value)) / Decimal("100")).quantize(Decimal("0.01"))
                    else:
                        discount = min(Decimal(str(coupon.value)), subtotal)
                    coupon.used_count += 1

            default_address = next(a for a in addresses[customer.email] if a.is_default)
            order = Order(
                user_id=customer.id,
                status=status,
                total_amount=subtotal - discount,
                discount_amount=discount,
                coupon_id=coupon.id if coupon else None,
                shipping_address_snapshot={
                    "label": default_address.label,
                    "street": default_address.street,
                    "city": default_address.city,
                    "state": default_address.state,
                    "country": default_address.country,
                    "postal_code": default_address.postal_code,
                },
                created_at=placed_at,
            )
            order.items = order_items
            db.add(order)
            orders.append(order)

            for variant in chosen:
                purchases.setdefault((customer.id, variant.product_id), []).append(order)
        db.flush()

        # ── Carts ──────────────────────────────────────────────────────────
        # A few customers have left something in the basket; one has a cart
        # record with nothing in it.
        cart_owners = RNG.sample(customers, 6)
        empty_cart_owner = cart_owners[0]
        for customer in cart_owners:
            cart = Cart(user_id=customer.id)
            db.add(cart)
            db.flush()
            if customer is empty_cart_owner:
                continue
            for variant in RNG.sample(sellable, RNG.randint(1, 3)):
                db.add(CartItem(cart_id=cart.id, variant_id=variant.id, quantity=RNG.randint(1, 2)))

        # ── Wishlists ──────────────────────────────────────────────────────
        # Every customer has a wishlist; the newest signup has not saved
        # anything to theirs yet.
        wishlistable = [p for p in products.values() if p.is_active]
        empty_wishlist_owner = customers[-1]
        for customer in customers:
            wishlist = Wishlist(user_id=customer.id)
            db.add(wishlist)
            db.flush()
            if customer is empty_wishlist_owner:
                continue
            for product in RNG.sample(wishlistable, RNG.randint(2, 5)):
                db.add(WishlistItem(wishlist_id=wishlist.id, product_id=product.id))

        # ── Reviews ────────────────────────────────────────────────────────
        # Only from customers who actually bought the product, one per pair.
        # The first few are assigned deterministically so that every star
        # rating, rating-only reviews and the moderation queue are all covered
        # however the RNG falls.
        by_rating: dict[int, list] = {}
        for rating, comment in REVIEW_COMMENTS:
            by_rating.setdefault(rating, []).append(comment)

        reviewed = [key for key in purchases if RNG.random() < 0.55]
        for i, (user_id, product_id) in enumerate(reviewed):
            placed = purchases[(user_id, product_id)]
            first_order = min(placed, key=lambda o: o.created_at)
            if i < 5:
                rating = i + 1                       # guarantees one of each 1-5
                comment = RNG.choice(by_rating[rating])
            else:
                rating, comment = RNG.choice(REVIEW_COMMENTS)
            db.add(Review(
                user_id=user_id,
                product_id=product_id,
                rating=rating,
                # A couple of customers leave a rating and no words at all.
                comment=None if i in (5, 6) else comment,
                # Most reviews are published; a steady minority await moderation.
                is_approved=(i % 7 != 3),
                created_at=first_order.created_at + timedelta(days=RNG.uniform(2, 20)),
            ))
        review_count = len(reviewed)
        db.flush()

        # ── Return requests ────────────────────────────────────────────────
        # Every returned order is backed by an approved request, and a handful
        # of delivered orders have requests still working through the queue.
        returned_orders = [o for o in orders if o.status == OrderStatus.returned]
        delivered_orders = [o for o in orders if o.status == OrderStatus.delivered]
        open_requests = RNG.sample(delivered_orders, min(8, len(delivered_orders)))
        return_plan = (
            [(o, ReturnStatus.approved) for o in returned_orders]
            + [(o, RNG.choice([ReturnStatus.pending] * 2 + [ReturnStatus.rejected]))
               for o in open_requests]
        )

        return_count = 0
        for order, status in return_plan:
            request = ReturnRequest(
                order_id=order.id,
                user_id=order.user_id,
                reason=RNG.choice(RETURN_REASONS),
                status=status,
                admin_notes={
                    ReturnStatus.approved: "Approved — refund issued to the original payment method.",
                    ReturnStatus.rejected: "Outside the 30-day return window.",
                }.get(status),
                created_at=order.created_at + timedelta(days=RNG.uniform(3, 14)),
            )
            db.add(request)
            db.flush()
            for item in RNG.sample(order.items, RNG.randint(1, len(order.items))):
                db.add(ReturnRequestItem(
                    return_request_id=request.id,
                    order_item_id=item.id,
                    quantity=RNG.randint(1, item.quantity),
                ))
            return_count += 1
        db.flush()

        # ── Nullable relationships ─────────────────────────────────────────
        # The schema lets orders outlive the accounts and variants they point
        # at (both are ON DELETE SET NULL) and lets the address snapshot be
        # absent. Nothing in the generated data above hits those branches, so
        # seed one of each — the admin order list renders them differently.
        untouched = [
            o for o in orders
            if o.status in (OrderStatus.delivered, OrderStatus.cancelled)
            and o not in returned_orders and o not in open_requests
        ]
        closed_account_order, no_address_order, discontinued_order = untouched[:3]
        closed_account_order.user_id = None          # customer deleted their account
        # A plain None on a JSONB column persists as the JSON value `null`;
        # null() forces a real SQL NULL, which is what nullable=True means here.
        no_address_order.shipping_address_snapshot = null()
        discontinued_order.items[0].variant_id = None  # variant removed from the catalogue

        db.commit()

        status_counts = {}
        for order in orders:
            status_counts[order.status.value] = status_counts.get(order.status.value, 0) + 1

        print("Database seeded successfully.\n")
        print(f"  Users:      {len(USERS)} (admin@example.com / admin1234, everyone else / password123)")
        print(f"  Addresses:  {sum(len(v) for v in ADDRESSES.values())}")
        print(f"  Categories: {len(CATEGORIES)}    Tags: {len(TAGS)}")
        print(f"  Products:   {len(PRODUCTS)} with {len(variants)} variants "
              f"and {sum(p[7] for p in PRODUCTS)} photos")
        print(f"  Coupons:    {len(COUPONS)}")
        print(f"  Orders:     {len(orders)} with {sum(len(o.items) for o in orders)} line items")
        for status in OrderStatus:
            print(f"                {status.value:<12} {status_counts.get(status.value, 0)}")
        print(f"  Reviews:    {review_count}    Returns: {return_count}")
        print("\n  Edge cases covered: order with no account, order with no address")
        print("  snapshot, line item with a discontinued variant, product with no")
        print("  category / no photos / no description / no variants, empty category,")
        print("  unused tag, empty cart, empty wishlist, exhausted + expired +")
        print("  inactive coupons, deactivated user, unlabelled address.")
        print(f"\n  Photos are served from {settings.PUBLIC_BASE_URL.rstrip('/')}/static/products/")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-y", "--yes", action="store_true", help="skip the confirmation prompt")
    args = parser.parse_args()
    seed(assume_yes=args.yes)
