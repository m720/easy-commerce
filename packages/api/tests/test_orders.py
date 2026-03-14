import pytest


@pytest.fixture()
def setup_order(client, admin_headers, user_headers):
    """Sets up a variant in cart + address, returns (address_id, variant_id)."""
    cat = client.post("/api/v1/categories", json={"name": "OrderCat", "slug": "ordercat"}, headers=admin_headers).json()
    prod = client.post("/api/v1/products", json={
        "name": "Order Product", "base_price": "50.00", "category_id": cat["id"], "tag_ids": []
    }, headers=admin_headers).json()
    var = client.post(f"/api/v1/products/{prod['id']}/variants", json={
        "name": "Default", "sku": "ORDER-SKU-001", "price": "50.00", "stock_quantity": 100, "low_stock_threshold": 5,
    }, headers=admin_headers).json()

    client.post("/api/v1/cart/items", json={"variant_id": var["id"], "quantity": 2}, headers=user_headers)

    addr = client.post("/api/v1/addresses", json={
        "street": "123 Main St", "city": "Springfield", "country": "US", "postal_code": "12345"
    }, headers=user_headers).json()

    return addr["id"], var["id"]


def test_place_order(client, user_headers, setup_order):
    address_id, _ = setup_order
    resp = client.post("/api/v1/orders", json={"address_id": str(address_id)}, headers=user_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert len(data["items"]) == 1
    assert float(data["total_amount"]) == 100.0


def test_my_orders(client, user_headers, setup_order):
    address_id, _ = setup_order
    client.post("/api/v1/orders", json={"address_id": str(address_id)}, headers=user_headers)
    resp = client.get("/api/v1/orders", headers=user_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


def test_cancel_order(client, user_headers, setup_order):
    address_id, _ = setup_order
    order = client.post("/api/v1/orders", json={"address_id": str(address_id)}, headers=user_headers).json()
    resp = client.delete(f"/api/v1/orders/{order['id']}", headers=user_headers)
    assert resp.status_code == 204


def test_admin_update_order_status(client, user_headers, admin_headers, setup_order):
    address_id, _ = setup_order
    order = client.post("/api/v1/orders", json={"address_id": str(address_id)}, headers=user_headers).json()
    resp = client.patch(f"/api/v1/orders/admin/{order['id']}/status", json={"status": "processing"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "processing"
