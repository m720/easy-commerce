def test_create_coupon(client, admin_headers):
    resp = client.post("/api/v1/coupons", json={
        "code": "SAVE10",
        "type": "percent",
        "value": "10",
        "is_active": True,
    }, headers=admin_headers)
    assert resp.status_code == 201
    assert resp.json()["code"] == "SAVE10"


def test_list_coupons(client, admin_headers):
    resp = client.get("/api/v1/coupons", headers=admin_headers)
    assert resp.status_code == 200


def test_validate_coupon(client, user_headers, admin_headers):
    client.post("/api/v1/coupons", json={"code": "FLAT5", "type": "fixed", "value": "5", "is_active": True}, headers=admin_headers)
    resp = client.post("/api/v1/coupons/validate", json={"code": "FLAT5", "order_subtotal": "50"}, headers=user_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["valid"] is True
    assert float(data["discount_amount"]) == 5.0


def test_validate_invalid_coupon(client, user_headers):
    resp = client.post("/api/v1/coupons/validate", json={"code": "INVALID", "order_subtotal": "50"}, headers=user_headers)
    assert resp.status_code == 400


def test_delete_coupon(client, admin_headers):
    c = client.post("/api/v1/coupons", json={"code": "DELME", "type": "fixed", "value": "1"}, headers=admin_headers).json()
    resp = client.delete(f"/api/v1/coupons/{c['id']}", headers=admin_headers)
    assert resp.status_code == 204
