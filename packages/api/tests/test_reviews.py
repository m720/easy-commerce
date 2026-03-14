import pytest


@pytest.fixture()
def product_id(client, admin_headers):
    cat = client.post("/api/v1/categories", json={"name": "ReviewCat", "slug": "reviewcat"}, headers=admin_headers).json()
    prod = client.post("/api/v1/products", json={
        "name": "Reviewable Product", "base_price": "20.00", "category_id": cat["id"], "tag_ids": []
    }, headers=admin_headers).json()
    return prod["id"]


def test_list_reviews_empty(client, product_id):
    resp = client.get(f"/api/v1/products/{product_id}/reviews")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_review(client, user_headers, product_id):
    resp = client.post(f"/api/v1/products/{product_id}/reviews", json={
        "rating": 5, "comment": "Great product!"
    }, headers=user_headers)
    assert resp.status_code == 201
    assert resp.json()["rating"] == 5


def test_duplicate_review_rejected(client, user_headers, product_id):
    client.post(f"/api/v1/products/{product_id}/reviews", json={"rating": 4}, headers=user_headers)
    resp = client.post(f"/api/v1/products/{product_id}/reviews", json={"rating": 3}, headers=user_headers)
    assert resp.status_code == 400


def test_approve_review(client, user_headers, admin_headers, product_id):
    review = client.post(f"/api/v1/products/{product_id}/reviews", json={"rating": 4}, headers=user_headers).json()
    resp = client.patch(f"/api/v1/products/{product_id}/reviews/{review['id']}/approve", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["is_approved"] is True


def test_delete_own_review(client, user_headers, product_id):
    review = client.post(f"/api/v1/products/{product_id}/reviews", json={"rating": 3}, headers=user_headers).json()
    resp = client.delete(f"/api/v1/products/{product_id}/reviews/{review['id']}", headers=user_headers)
    assert resp.status_code == 204
