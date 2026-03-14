import pytest


@pytest.fixture()
def category(client, admin_headers):
    resp = client.post("/api/v1/categories", json={"name": "TestCat", "slug": "testcat"}, headers=admin_headers)
    return resp.json()


@pytest.fixture()
def product(client, admin_headers, category):
    resp = client.post("/api/v1/products", json={
        "name": "Test Product",
        "description": "A test product",
        "base_price": "29.99",
        "category_id": category["id"],
        "is_featured": False,
        "tag_ids": [],
    }, headers=admin_headers)
    assert resp.status_code == 201
    return resp.json()


@pytest.fixture()
def variant(client, admin_headers, product):
    resp = client.post(f"/api/v1/products/{product['id']}/variants", json={
        "name": "Default",
        "sku": "SKU-001",
        "price": "29.99",
        "stock_quantity": 10,
        "low_stock_threshold": 2,
    }, headers=admin_headers)
    assert resp.status_code == 201
    return resp.json()


def test_list_products(client):
    resp = client.get("/api/v1/products")
    assert resp.status_code == 200


def test_create_product(client, admin_headers, category):
    resp = client.post("/api/v1/products", json={
        "name": "New Product",
        "base_price": "49.99",
        "category_id": category["id"],
        "tag_ids": [],
    }, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["name"] == "New Product"


def test_get_product(client, product):
    resp = client.get(f"/api/v1/products/{product['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Test Product"


def test_search_products(client, product):
    resp = client.get("/api/v1/products?search=Test")
    assert resp.status_code == 200
    assert any(p["name"] == "Test Product" for p in resp.json())


def test_featured_products(client, admin_headers, product):
    client.patch(f"/api/v1/products/{product['id']}/feature", headers=admin_headers)
    resp = client.get("/api/v1/products/featured")
    assert resp.status_code == 200


def test_soft_delete_product(client, admin_headers, product):
    resp = client.delete(f"/api/v1/products/{product['id']}", headers=admin_headers)
    assert resp.status_code == 204
    # Should not be found after soft delete
    get = client.get(f"/api/v1/products/{product['id']}")
    assert get.status_code == 404


def test_create_variant(client, admin_headers, product):
    resp = client.post(f"/api/v1/products/{product['id']}/variants", json={
        "name": "Red/M",
        "sku": "SKU-RED-M",
        "price": "25.00",
        "stock_quantity": 5,
        "low_stock_threshold": 1,
    }, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["sku"] == "SKU-RED-M"


def test_bulk_activate_deactivate(client, admin_headers, product):
    resp = client.post("/api/v1/products/bulk-deactivate", json={"product_ids": [product["id"]]}, headers=admin_headers)
    assert resp.status_code == 200
    resp2 = client.post("/api/v1/products/bulk-activate", json={"product_ids": [product["id"]]}, headers=admin_headers)
    assert resp2.status_code == 200
