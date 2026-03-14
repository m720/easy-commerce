def test_register(client):
    resp = client.post("/api/v1/auth/register", json={
        "email": "newuser@test.com",
        "full_name": "New User",
        "password": "password123",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "newuser@test.com"
    assert data["role"] == "user"


def test_register_duplicate_email(client):
    payload = {"email": "dup@test.com", "full_name": "Dup", "password": "pw123456"}
    client.post("/api/v1/auth/register", json=payload)
    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


def test_login(client):
    client.post("/api/v1/auth/register", json={"email": "login@test.com", "full_name": "L", "password": "pw123456"})
    resp = client.post("/api/v1/auth/login", json={"email": "login@test.com", "password": "pw123456"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client):
    client.post("/api/v1/auth/register", json={"email": "wrong@test.com", "full_name": "W", "password": "correct"})
    resp = client.post("/api/v1/auth/login", json={"email": "wrong@test.com", "password": "incorrect"})
    assert resp.status_code == 401


def test_me(client, user_headers):
    resp = client.get("/api/v1/auth/me", headers=user_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "user@test.com"


def test_change_password(client, user_headers):
    resp = client.put("/api/v1/auth/me/password", json={
        "current_password": "userpass123",
        "new_password": "newpass456",
    }, headers=user_headers)
    assert resp.status_code == 204
