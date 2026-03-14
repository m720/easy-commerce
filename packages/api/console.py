#!/usr/bin/env python
"""
Interactive console for the ecommerce API.
All models and a database session are available out of the box.

Usage:
    python console.py

Available:
    session  - SQLAlchemy database session
    db       - alias for session

Models:
    User, Address, Cart, CartItem, Category, Coupon,
    Order, OrderItem, ReturnRequest, ReturnRequestItem,
    Product, ProductVariant, ProductImage, Review, Tag,
    Wishlist, WishlistItem

Example:
    >>> session.query(User).all()
    >>> session.query(User).filter(User.email == "test@example.com").first()
    >>> u = session.query(User).first(); u.email
"""

import os
import sys

# Ensure the project root is on the path
sys.path.insert(0, os.path.dirname(__file__))

from app.database.base import SessionLocal, engine, Base

# Import all models so they are registered and available in the REPL
from app.models.user import User
from app.models.address import Address
from app.models.cart import Cart, CartItem
from app.models.category import Category
from app.models.coupon import Coupon
from app.models.order import Order, OrderItem, ReturnRequest, ReturnRequestItem
from app.models.product import Product, ProductVariant, ProductImage
from app.models.review import Review
from app.models.tag import Tag
from app.models.wishlist import Wishlist, WishlistItem

session = SessionLocal()
db = session  # alias

BANNER = """
ecommerce console (SQLAlchemy + FastAPI)
----------------------------------------
Models:  User, Address, Cart, CartItem, Category, Coupon,
         Order, OrderItem, ReturnRequest, ReturnRequestItem,
         Product, ProductVariant, ProductImage, Review, Tag,
         Wishlist, WishlistItem
Session: session  (alias: db)

Type 'exit' or Ctrl-D to quit. Session is committed on exit.
"""

namespace = {
    "session": session,
    "db": db,
    "User": User,
    "Address": Address,
    "Cart": Cart,
    "CartItem": CartItem,
    "Category": Category,
    "Coupon": Coupon,
    "Order": Order,
    "OrderItem": OrderItem,
    "ReturnRequest": ReturnRequest,
    "ReturnRequestItem": ReturnRequestItem,
    "Product": Product,
    "ProductVariant": ProductVariant,
    "ProductImage": ProductImage,
    "Review": Review,
    "Tag": Tag,
    "Wishlist": Wishlist,
    "WishlistItem": WishlistItem,
}

try:
    import IPython
    IPython.start_ipython(argv=[], user_ns=namespace, display_banner=False)
    print(BANNER)
except ImportError:
    import code
    import readline
    import rlcompleter
    readline.set_completer(rlcompleter.Completer(namespace).complete)
    readline.parse_and_bind("tab: complete")
    code.interact(banner=BANNER, local=namespace, exitmsg="")
finally:
    try:
        session.commit()
    except Exception:
        session.rollback()
    finally:
        session.close()
