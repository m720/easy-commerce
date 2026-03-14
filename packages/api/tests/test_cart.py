import pytest


@pytest.fixture()
def variant_id(client, admin_headers):
    cat = client.post("/api/v1/categories", json={"name": "CartCat", "slug": "cartcat"}, headers=admin_headers).json()
    prod = client.post("/api/v1/products", json={
        "name": "Cart Product", "base_price": "10.00", "category_id": cat["id"], "tag_ids": []
    }, headers=admin_headers).json()
    var = client.post(f"/api/v1/products/{prod['id']}/variants", json={
        "name": "Default", "sku": "CART-SKU-001", "price": "10.00", "stock_quantity": 20, "low_stock_threshold": 2,
    }, headers=admin_headers).json()
    return var["id"]


def test_get_empty_cart(client, user_headers):
    resp = client.get("/api/v1/cart", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["items"] == []


def test_add_to_cart(client, user_headers, variant_id):
    resp = client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 2}, headers=user_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["quantity"] == 2


def test_update_cart_item(client, user_headers, variant_id):
    add = client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=user_headers)
    item_id = add.json()["items"][0]["id"]
    resp = client.put(f"/api/v1/cart/items/{item_id}", json={"quantity": 5}, headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["items"][0]["quantity"] == 5


def test_remove_cart_item(client, user_headers, variant_id):
    add = client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=user_headers)
    item_id = add.json()["items"][0]["id"]
    resp = client.delete(f"/api/v1/cart/items/{item_id}", headers=user_headers)
    assert resp.status_code == 204


def test_clear_cart(client, user_headers, variant_id):
    client.post("/api/v1/cart/items", json={"variant_id": variant_id, "quantity": 1}, headers=user_headers)
    resp = client.delete("/api/v1/cart", headers=user_headers)
    assert resp.status_code == 204
    cart = client.get("/api/v1/cart", headers=user_headers).json()
    assert cart["items"] == []
