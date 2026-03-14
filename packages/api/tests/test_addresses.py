def test_create_address(client, user_headers):
    resp = client.post("/api/v1/addresses", json={
        "label": "Home",
        "street": "1 Main St",
        "city": "Anytown",
        "country": "US",
        "postal_code": "90210",
    }, headers=user_headers)
    assert resp.status_code == 201
    assert resp.json()["city"] == "Anytown"


def test_list_addresses(client, user_headers):
    resp = client.get("/api/v1/addresses", headers=user_headers)
    assert resp.status_code == 200


def test_set_default_address(client, user_headers):
    a1 = client.post("/api/v1/addresses", json={"street": "A", "city": "C", "country": "US", "postal_code": "1"}, headers=user_headers).json()
    a2 = client.post("/api/v1/addresses", json={"street": "B", "city": "C", "country": "US", "postal_code": "2"}, headers=user_headers).json()
    resp = client.patch(f"/api/v1/addresses/{a2['id']}/set-default", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["is_default"] is True


def test_delete_address(client, user_headers):
    addr = client.post("/api/v1/addresses", json={"street": "X", "city": "C", "country": "US", "postal_code": "9"}, headers=user_headers).json()
    resp = client.delete(f"/api/v1/addresses/{addr['id']}", headers=user_headers)
    assert resp.status_code == 204
