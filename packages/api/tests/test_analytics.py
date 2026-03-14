def test_revenue(client, admin_headers):
    resp = client.get("/api/v1/analytics/revenue", headers=admin_headers)
    assert resp.status_code == 200
    assert "total_revenue" in resp.json()


def test_orders_by_status(client, admin_headers):
    resp = client.get("/api/v1/analytics/orders", headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_top_products(client, admin_headers):
    resp = client.get("/api/v1/analytics/top-products", headers=admin_headers)
    assert resp.status_code == 200


def test_summary(client, admin_headers):
    resp = client.get("/api/v1/analytics/summary", headers=admin_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "total_revenue" in data
    assert "total_users" in data


def test_low_stock(client, admin_headers):
    resp = client.get("/api/v1/analytics/low-stock", headers=admin_headers)
    assert resp.status_code == 200


def test_export_csv_revenue(client, admin_headers):
    resp = client.get("/api/v1/analytics/export/revenue.csv", headers=admin_headers)
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]


def test_analytics_requires_admin(client, user_headers):
    resp = client.get("/api/v1/analytics/summary", headers=user_headers)
    assert resp.status_code == 403
