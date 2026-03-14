"""Seed the database with sample data."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from app.database.base import SessionLocal, engine, Base
from app.models.user import User
from app.models.category import Category
from app.models.tag import Tag
from app.models.product import Product, ProductVariant, ProductImage
from app.models.coupon import Coupon
import bcrypt as _bcrypt

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()
from app.core.enums import UserRole, CouponType
from datetime import datetime, timezone, timedelta


def seed():
    # Import all models so Base.metadata knows about them
    import app.models.address
    import app.models.cart
    import app.models.order
    import app.models.review
    import app.models.wishlist

    db = SessionLocal()
    try:
        # ── Users ──────────────────────────────────────────────────────────────
        admin = User(
            email="admin@example.com",
            full_name="Admin User",
            hashed_password=hash_password("admin1234"),
            role=UserRole.admin,
        )
        customer1 = User(
            email="alice@example.com",
            full_name="Alice Smith",
            hashed_password=hash_password("password123"),
            role=UserRole.user,
        )
        customer2 = User(
            email="bob@example.com",
            full_name="Bob Jones",
            hashed_password=hash_password("password123"),
            role=UserRole.user,
        )
        db.add_all([admin, customer1, customer2])
        db.flush()

        # ── Categories ─────────────────────────────────────────────────────────
        electronics = Category(name="Electronics", slug="electronics", description="Gadgets and devices")
        clothing = Category(name="Clothing", slug="clothing", description="Apparel and accessories")
        books = Category(name="Books", slug="books", description="Fiction, non-fiction, and more")
        db.add_all([electronics, clothing, books])
        db.flush()

        # ── Tags ───────────────────────────────────────────────────────────────
        tag_sale = Tag(name="Sale", slug="sale")
        tag_new = Tag(name="New Arrival", slug="new-arrival")
        tag_popular = Tag(name="Popular", slug="popular")
        tag_eco = Tag(name="Eco-Friendly", slug="eco-friendly")
        db.add_all([tag_sale, tag_new, tag_popular, tag_eco])
        db.flush()

        # ── Products ───────────────────────────────────────────────────────────
        # Electronics
        laptop = Product(
            name="ProBook Laptop 15",
            description="High-performance 15-inch laptop with 16GB RAM and 512GB SSD.",
            base_price=999.99,
            category_id=electronics.id,
            is_featured=True,
            tags=[tag_popular, tag_new],
        )
        headphones = Product(
            name="SoundMax Wireless Headphones",
            description="Over-ear noise-cancelling headphones with 30h battery life.",
            base_price=149.99,
            category_id=electronics.id,
            is_featured=False,
            tags=[tag_sale, tag_popular],
        )

        # Clothing
        tshirt = Product(
            name="Classic Cotton T-Shirt",
            description="Comfortable 100% organic cotton t-shirt.",
            base_price=24.99,
            category_id=clothing.id,
            is_featured=True,
            tags=[tag_eco, tag_new],
        )
        jeans = Product(
            name="Slim Fit Jeans",
            description="Modern slim-fit jeans available in multiple washes.",
            base_price=59.99,
            category_id=clothing.id,
            tags=[tag_popular],
        )

        # Books
        novel = Product(
            name="The Lost Horizon",
            description="A gripping adventure novel set in the Himalayas.",
            base_price=14.99,
            category_id=books.id,
            tags=[tag_sale],
        )
        db.add_all([laptop, headphones, tshirt, jeans, novel])
        db.flush()

        # ── Variants ───────────────────────────────────────────────────────────
        db.add_all([
            # Laptop
            ProductVariant(product_id=laptop.id, name="8GB / 256GB", sku="LAPTOP-8-256", price=799.99, stock_quantity=20),
            ProductVariant(product_id=laptop.id, name="16GB / 512GB", sku="LAPTOP-16-512", price=999.99, stock_quantity=15),
            ProductVariant(product_id=laptop.id, name="32GB / 1TB", sku="LAPTOP-32-1T", price=1399.99, stock_quantity=8),
            # Headphones
            ProductVariant(product_id=headphones.id, name="Black", sku="HP-BLACK", price=149.99, stock_quantity=50),
            ProductVariant(product_id=headphones.id, name="White", sku="HP-WHITE", price=149.99, stock_quantity=30),
            # T-Shirt
            ProductVariant(product_id=tshirt.id, name="White / S", sku="TS-W-S", price=24.99, stock_quantity=100),
            ProductVariant(product_id=tshirt.id, name="White / M", sku="TS-W-M", price=24.99, stock_quantity=100),
            ProductVariant(product_id=tshirt.id, name="White / L", sku="TS-W-L", price=24.99, stock_quantity=80),
            ProductVariant(product_id=tshirt.id, name="Black / M", sku="TS-B-M", price=24.99, stock_quantity=90),
            # Jeans
            ProductVariant(product_id=jeans.id, name="Blue / 30", sku="JN-B-30", price=59.99, stock_quantity=40),
            ProductVariant(product_id=jeans.id, name="Blue / 32", sku="JN-B-32", price=59.99, stock_quantity=40),
            ProductVariant(product_id=jeans.id, name="Black / 32", sku="JN-K-32", price=59.99, stock_quantity=35),
            # Novel (single variant)
            ProductVariant(product_id=novel.id, name="Paperback", sku="NOVEL-PB", price=14.99, stock_quantity=200),
            ProductVariant(product_id=novel.id, name="Hardcover", sku="NOVEL-HC", price=24.99, stock_quantity=50),
        ])

        # ── Coupons ────────────────────────────────────────────────────────────
        db.add_all([
            Coupon(
                code="WELCOME10",
                type=CouponType.percent,
                value=10,
                min_order_amount=None,
                max_uses=1000,
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                is_active=True,
            ),
            Coupon(
                code="SAVE20",
                type=CouponType.fixed,
                value=20,
                min_order_amount=100,
                max_uses=500,
                expires_at=datetime.now(timezone.utc) + timedelta(days=90),
                is_active=True,
            ),
        ])

        db.commit()
        print("Database seeded successfully.")
        print(f"  Users:      admin@example.com (admin1234), alice@example.com, bob@example.com (password123)")
        print(f"  Categories: Electronics, Clothing, Books")
        print(f"  Products:   {5} products with variants")
        print(f"  Coupons:    WELCOME10 (10% off), SAVE20 ($20 off orders $100+)")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
