"""Audit trail for privileged actions."""

import pytest

from app.models.audit import AuditLog
from app.services.audit_service import AuditAction, diff


@pytest.fixture()
def product(client, admin_headers):
    cat = client.post("/api/v1/categories", json={"name": "AuditCat", "slug": "auditcat"}, headers=admin_headers).json()
    return client.post("/api/v1/products", json={
        "name": "Audited Product", "base_price": "10.00", "category_id": cat["id"], "tag_ids": []
    }, headers=admin_headers).json()


def test_price_change_records_who_and_what(client, admin_headers, product, db):
    client.put(
        f"/api/v1/products/{product['id']}",
        json={"base_price": "19.99"},
        headers=admin_headers,
    )

    entry = (
        db.query(AuditLog)
        .filter(AuditLog.action == AuditAction.PRODUCT_UPDATED)
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert entry is not None
    assert entry.actor_email == "admin@test.com"
    assert entry.entity_id == product["id"]
    assert entry.changes["base_price"] == {"before": "10.00", "after": "19.99"}
    # Ties the entry back to the request log.
    assert entry.request_id


def test_unchanged_fields_are_not_recorded(client, admin_headers, product, db):
    client.put(f"/api/v1/products/{product['id']}", json={"name": "Audited Product"}, headers=admin_headers)

    entry = (
        db.query(AuditLog)
        .filter(AuditLog.action == AuditAction.PRODUCT_UPDATED)
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert entry.changes is None


def test_variant_stock_and_price_edits_are_audited(client, admin_headers, product, db):
    variant = client.post(f"/api/v1/products/{product['id']}/variants", json={
        "name": "Default", "sku": "AUDIT-SKU-1", "price": "10.00", "stock_quantity": 5, "low_stock_threshold": 2,
    }, headers=admin_headers).json()

    client.put(
        f"/api/v1/products/{product['id']}/variants/{variant['id']}",
        json={"price": "12.50", "stock_quantity": 99},
        headers=admin_headers,
    )

    entry = (
        db.query(AuditLog)
        .filter(AuditLog.action == AuditAction.VARIANT_UPDATED)
        .order_by(AuditLog.created_at.desc())
        .first()
    )
    assert entry.changes["price"]["after"] == "12.50"
    assert entry.changes["stock_quantity"] == {"before": 5, "after": 99}
    assert entry.entity_label == "AUDIT-SKU-1"


def test_return_approval_is_attributed(client, admin_headers, user_headers, db):
    """Who approved this refund is exactly the question an audit log answers."""
    cat = client.post("/api/v1/categories", json={"name": "RetCat", "slug": "retcat"}, headers=admin_headers).json()
    prod = client.post("/api/v1/products", json={
        "name": "Returnable", "base_price": "30.00", "category_id": cat["id"], "tag_ids": []
    }, headers=admin_headers).json()
    variant = client.post(f"/api/v1/products/{prod['id']}/variants", json={
        "name": "Default", "sku": "RET-SKU-1", "price": "30.00", "stock_quantity": 10, "low_stock_threshold": 1,
    }, headers=admin_headers).json()
    client.post("/api/v1/cart/items", json={"variant_id": variant["id"], "quantity": 1}, headers=user_headers)
    addr = client.post("/api/v1/addresses", json={
        "street": "9 Return Rd", "city": "Springfield", "country": "US", "postal_code": "12345"
    }, headers=user_headers).json()
    order = client.post("/api/v1/orders", json={"address_id": addr["id"]}, headers=user_headers).json()

    client.patch(f"/api/v1/orders/admin/{order['id']}/status", json={"status": "delivered"}, headers=admin_headers)
    ret = client.post(f"/api/v1/orders/{order['id']}/returns", json={
        "reason": "Damaged in transit",
        "items": [{"order_item_id": order["items"][0]["id"], "quantity": 1}],
    }, headers=user_headers).json()

    client.patch(
        f"/api/v1/orders/admin/returns/{ret['id']}/approve",
        json={"admin_notes": "Refund issued"},
        headers=admin_headers,
    )

    approval = db.query(AuditLog).filter(AuditLog.action == AuditAction.RETURN_APPROVED).first()
    assert approval is not None
    assert approval.actor_email == "admin@test.com"
    assert approval.changes["admin_notes"]["after"] == "Refund issued"

    status_change = db.query(AuditLog).filter(AuditLog.action == AuditAction.ORDER_STATUS_CHANGED).first()
    assert status_change.changes["status"] == {"before": "pending", "after": "delivered"}


def test_user_deactivation_is_audited(client, admin_headers, user_headers, db):
    users = client.get("/api/v1/users", headers=admin_headers).json()
    target = next(u for u in users if u["email"] == "user@test.com")

    client.patch(f"/api/v1/users/{target['id']}/deactivate", headers=admin_headers)

    entry = db.query(AuditLog).filter(AuditLog.action == AuditAction.USER_DEACTIVATED).first()
    assert entry.entity_label == "user@test.com"
    assert entry.changes["is_active"] == {"before": True, "after": False}


def test_audit_log_endpoint_is_admin_only(client, user_headers):
    assert client.get("/api/v1/audit-logs", headers=user_headers).status_code == 403
    assert client.get("/api/v1/audit-logs").status_code == 401


def test_audit_log_endpoint_filters(client, admin_headers, product):
    client.put(f"/api/v1/products/{product['id']}", json={"base_price": "44.00"}, headers=admin_headers)

    all_entries = client.get("/api/v1/audit-logs", headers=admin_headers).json()
    assert len(all_entries) >= 2  # creation + update

    filtered = client.get(
        "/api/v1/audit-logs",
        params={"action": AuditAction.PRODUCT_UPDATED, "entity_id": product["id"]},
        headers=admin_headers,
    ).json()
    assert len(filtered) == 1
    assert filtered[0]["changes"]["base_price"]["after"] == "44.00"


def test_diff_ignores_equal_values_across_types():
    """Decimal('10.00') and '10.00' are the same price, not a change."""
    from decimal import Decimal

    assert diff({"price": Decimal("10.00")}, {"price": "10.00"}) == {}
    assert diff({"price": Decimal("10.00")}, {"price": Decimal("11.00")}) == {
        "price": {"before": "10.00", "after": "11.00"}
    }


def test_audit_failure_does_not_break_the_action(client, admin_headers, product, monkeypatch, db):
    """An admin must not get a 500 because the audit insert failed."""
    from app.services import audit_service

    def exploding_add(*args, **kwargs):
        raise RuntimeError("audit store unavailable")

    monkeypatch.setattr(audit_service, "AuditLog", exploding_add)

    resp = client.put(f"/api/v1/products/{product['id']}", json={"base_price": "77.00"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["base_price"] == "77.00"
