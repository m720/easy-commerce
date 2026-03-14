def test_list_categories_empty(client):
    resp = client.get("/api/v1/categories")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_create_category_admin(client, admin_headers):
    resp = client.post("/api/v1/categories", json={
        "name": "Electronics",
        "slug": "electronics",
        "description": "Gadgets and devices",
    }, headers=admin_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Electronics"


def test_create_category_unauthorized(client):
    resp = client.post("/api/v1/categories", json={"name": "X", "slug": "x"})
    assert resp.status_code == 401


def test_create_category_user_forbidden(client, user_headers):
    resp = client.post("/api/v1/categories", json={"name": "Y", "slug": "y"}, headers=user_headers)
    assert resp.status_code == 403


def test_update_category(client, admin_headers):
    create = client.post("/api/v1/categories", json={"name": "Books", "slug": "books"}, headers=admin_headers)
    cat_id = create.json()["id"]
    resp = client.put(f"/api/v1/categories/{cat_id}", json={"description": "All books"}, headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["description"] == "All books"


def test_delete_category(client, admin_headers):
    create = client.post("/api/v1/categories", json={"name": "ToDelete", "slug": "to-delete"}, headers=admin_headers)
    cat_id = create.json()["id"]
    resp = client.delete(f"/api/v1/categories/{cat_id}", headers=admin_headers)
    assert resp.status_code == 204
