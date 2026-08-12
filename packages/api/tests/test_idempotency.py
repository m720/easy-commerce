"""Checkout retry safety.

The scenario these guard against: the client sends POST /orders, the order is
written, the response is lost, the client retries. Without an idempotency key
that is two orders and two charges.
"""

import uuid

import pytest

from app.models.idempotency import IdempotencyKey
from app.models.order import Order


@pytest.fixture()
def checkout_setup(client, admin_headers, user_headers):
    """A cart with stock and a shipping address. Returns the address id."""
    cat = client.post("/api/v1/categories", json={"name": "IdemCat", "slug": "idemcat"}, headers=admin_headers).json()
    prod = client.post("/api/v1/products", json={
        "name": "Idem Product", "base_price": "25.00", "category_id": cat["id"], "tag_ids": []
    }, headers=admin_headers).json()
    client.post(f"/api/v1/products/{prod['id']}/variants", json={
        "name": "Default", "sku": "IDEM-SKU-001", "price": "25.00",
        "stock_quantity": 50, "low_stock_threshold": 5,
    }, headers=admin_headers)
    variant = client.get(f"/api/v1/products/{prod['id']}/variants").json()[0]

    client.post("/api/v1/cart/items", json={"variant_id": variant["id"], "quantity": 2}, headers=user_headers)
    addr = client.post("/api/v1/addresses", json={
        "street": "1 Retry Way", "city": "Springfield", "country": "US", "postal_code": "12345"
    }, headers=user_headers).json()
    return addr["id"]


def test_retry_with_same_key_returns_original_order(client, user_headers, checkout_setup, db):
    key = str(uuid.uuid4())
    payload = {"address_id": str(checkout_setup)}
    headers = {**user_headers, "Idempotency-Key": key}

    first = client.post("/api/v1/orders", json=payload, headers=headers)
    assert first.status_code == 201
    assert first.headers.get("Idempotency-Replayed") == "false"

    # The retry the client would send after a dropped connection.
    second = client.post("/api/v1/orders", json=payload, headers=headers)
    assert second.status_code == 201
    assert second.headers.get("Idempotency-Replayed") == "true"

    assert second.json()["id"] == first.json()["id"]
    assert db.query(Order).count() == 1


def test_retry_does_not_decrement_stock_twice(client, user_headers, admin_headers, checkout_setup):
    key = str(uuid.uuid4())
    payload = {"address_id": str(checkout_setup)}
    headers = {**user_headers, "Idempotency-Key": key}

    client.post("/api/v1/orders", json=payload, headers=headers)
    products = client.get("/api/v1/products", params={"search": "Idem Product"}).json()
    stock_after_first = products[0]["variants"][0]["stock_quantity"]

    client.post("/api/v1/orders", json=payload, headers=headers)
    products = client.get("/api/v1/products", params={"search": "Idem Product"}).json()

    assert products[0]["variants"][0]["stock_quantity"] == stock_after_first


def test_distinct_keys_place_distinct_orders(client, user_headers, admin_headers, checkout_setup, db):
    payload = {"address_id": str(checkout_setup)}

    first = client.post(
        "/api/v1/orders", json=payload,
        headers={**user_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert first.status_code == 201

    # Refill the cart: a genuinely new checkout, so a new key.
    variant_id = first.json()["items"][0]["variant_id"]
    client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=user_headers)

    second = client.post(
        "/api/v1/orders", json=payload,
        headers={**user_headers, "Idempotency-Key": str(uuid.uuid4())},
    )
    assert second.status_code == 201
    assert second.json()["id"] != first.json()["id"]
    assert db.query(Order).count() == 2


def test_key_reused_with_different_body_is_rejected(client, user_headers, checkout_setup):
    key = str(uuid.uuid4())
    headers = {**user_headers, "Idempotency-Key": key}

    first = client.post("/api/v1/orders", json={"address_id": str(checkout_setup)}, headers=headers)
    assert first.status_code == 201

    # Same key, different payload — a client bug, not a retry.
    conflicting = client.post(
        "/api/v1/orders",
        json={"address_id": str(checkout_setup), "coupon_code": "SOMETHING"},
        headers=headers,
    )
    assert conflicting.status_code == 422
    assert "different request body" in conflicting.json()["detail"]


def test_in_flight_key_returns_409(client, user_headers, checkout_setup, db):
    """A second request arriving while the first is still running must not proceed."""
    key = str(uuid.uuid4())
    payload = {"address_id": str(checkout_setup)}

    # Simulate the concurrent request's reservation already sitting in the table.
    from datetime import datetime, timedelta, timezone

    from app.models.user import User
    from app.services.idempotency_service import fingerprint

    user = db.query(User).filter(User.email == "user@test.com").first()
    db.add(IdempotencyKey(
        key=key,
        user_id=user.id,
        endpoint="POST /api/v1/orders",
        request_fingerprint=fingerprint(payload),
        status="in_progress",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    ))
    db.flush()

    resp = client.post("/api/v1/orders", json=payload, headers={**user_headers, "Idempotency-Key": key})
    assert resp.status_code == 409
    assert db.query(Order).count() == 0


def test_failed_checkout_releases_the_key(client, user_headers, admin_headers, checkout_setup, db):
    """A rejected checkout must leave the key reusable, not stuck in_progress."""
    key = str(uuid.uuid4())
    headers = {**user_headers, "Idempotency-Key": key}
    bad_address = {"address_id": str(uuid.uuid4())}

    failed = client.post("/api/v1/orders", json=bad_address, headers=headers)
    assert failed.status_code == 404
    assert db.query(IdempotencyKey).filter(IdempotencyKey.key == key).count() == 0

    # The same key now works for a corrected request.
    retried = client.post("/api/v1/orders", json={"address_id": str(checkout_setup)}, headers=headers)
    assert retried.status_code == 201


def test_checkout_without_key_still_works(client, user_headers, checkout_setup):
    """Backwards compatibility: the header is optional by default."""
    resp = client.post("/api/v1/orders", json={"address_id": str(checkout_setup)}, headers=user_headers)
    assert resp.status_code == 201


def test_oversized_key_is_rejected(client, user_headers, checkout_setup):
    resp = client.post(
        "/api/v1/orders",
        json={"address_id": str(checkout_setup)},
        headers={**user_headers, "Idempotency-Key": "x" * 300},
    )
    assert resp.status_code == 400
