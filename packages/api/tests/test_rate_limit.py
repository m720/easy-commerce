"""Brute-force protection on the authentication endpoints."""

import pytest

from app.config import settings
from app.core import rate_limit


@pytest.fixture()
def strict_limits(rate_limited):
    """Tight budgets so the tests stay fast and obvious."""
    original = (settings.RATE_LIMIT_LOGIN_MAX, settings.RATE_LIMIT_REGISTER_MAX)
    settings.RATE_LIMIT_LOGIN_MAX = 3
    settings.RATE_LIMIT_REGISTER_MAX = 2
    yield
    settings.RATE_LIMIT_LOGIN_MAX, settings.RATE_LIMIT_REGISTER_MAX = original


def test_repeated_failed_logins_are_blocked(client, strict_limits):
    payload = {"email": "victim@test.com", "password": "wrong-guess"}

    for _ in range(settings.RATE_LIMIT_LOGIN_MAX):
        assert client.post("/api/v1/auth/login", json=payload).status_code == 401

    blocked = client.post("/api/v1/auth/login", json=payload)
    assert blocked.status_code == 429
    assert blocked.headers.get("Retry-After")
    assert "Too many attempts" in blocked.json()["detail"]


def test_correct_password_does_not_bypass_the_limit(client, strict_limits):
    """Guessing is capped even when a guess eventually lands."""
    client.post("/api/v1/auth/register", json={
        "email": "target@test.com", "full_name": "Target", "password": "correct-horse",
    })

    for _ in range(settings.RATE_LIMIT_LOGIN_MAX):
        client.post("/api/v1/auth/login", json={"email": "target@test.com", "password": "nope"})

    resp = client.post("/api/v1/auth/login", json={"email": "target@test.com", "password": "correct-horse"})
    assert resp.status_code == 429


def test_registration_is_capped(client, strict_limits):
    for i in range(settings.RATE_LIMIT_REGISTER_MAX):
        resp = client.post("/api/v1/auth/register", json={
            "email": f"signup{i}@test.com", "full_name": "Signup", "password": "password123",
        })
        assert resp.status_code == 201

    blocked = client.post("/api/v1/auth/register", json={
        "email": "one-too-many@test.com", "full_name": "Spam", "password": "password123",
    })
    assert blocked.status_code == 429


def test_limits_are_off_by_default_in_this_suite(client):
    """Sanity check on the fixture: without `rate_limited`, nothing is limited."""
    for _ in range(settings.RATE_LIMIT_LOGIN_MAX + 5):
        resp = client.post("/api/v1/auth/login", json={"email": "nobody@test.com", "password": "x"})
        assert resp.status_code == 401


def test_account_scope_tracks_the_email_not_the_ip(strict_limits):
    """Rotating source IPs must not buy extra guesses against one account."""
    for _ in range(settings.RATE_LIMIT_LOGIN_MAX):
        rate_limit.login_account_limiter.check_identity("victim@test.com")

    with pytest.raises(Exception) as exc_info:
        rate_limit.login_account_limiter.check_identity("victim@test.com")
    assert getattr(exc_info.value, "status_code", None) == 429

    # A different account is unaffected.
    rate_limit.login_account_limiter.check_identity("someone-else@test.com")


def test_window_expiry_restores_access(strict_limits, monkeypatch):
    monkeypatch.setattr(settings, "RATE_LIMIT_LOGIN_WINDOW", 0)
    for _ in range(settings.RATE_LIMIT_LOGIN_MAX + 2):
        # A zero-length window resets on every call, so nothing is ever blocked.
        rate_limit.login_account_limiter.check_identity("rolling@test.com")


def test_forwarded_header_identifies_the_client():
    class FakeRequest:
        headers = {"x-forwarded-for": "203.0.113.7, 10.0.0.1"}
        client = None

    assert rate_limit.client_identity(FakeRequest()) == "203.0.113.7"
