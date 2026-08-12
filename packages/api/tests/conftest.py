import os

# Test defaults, applied before the app (and therefore Settings) is imported.
# Rate limiting is off by default so the suite's many logins do not exhaust a
# window; the tests that exercise it turn it on explicitly via the
# `rate_limited` fixture. Caching is off so tests observe the database rather
# than a previous test's cached response.
os.environ.setdefault("RATE_LIMIT_ENABLED", "false")
os.environ.setdefault("CACHE_ENABLED", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")
os.environ.setdefault("LOG_FORMAT", "console")
# No outbound SMTP from the test suite: notification background tasks run for
# real during checkout tests, and a reachable-looking mail host would make them
# depend on the network.
os.environ["SMTP_USER"] = ""
os.environ["SMTP_PASSWORD"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from app.main import app  # noqa: E402
from app.config import settings  # noqa: E402
from app.core import cache, rate_limit  # noqa: E402
from app.database.base import Base  # noqa: E402
from app.dependencies import get_db  # noqa: E402
from app.models import (  # noqa: F401,E402
    user, category, tag, product, review, wishlist, coupon, address, cart, order,
    audit, idempotency,
)

TEST_DATABASE_URL = "postgresql://postgres:password@localhost:5432/ecommerce_test"

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Session wrapped in a transaction that is rolled back after each test.

    ``join_transaction_mode="create_savepoint"`` matters: application code
    genuinely commits (checkout and the idempotency reservation both do), and
    without savepoint joining those commits would end the fixture's outer
    transaction and leak rows into the next test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture()
def admin_token(client, db):
    client.post("/api/v1/auth/register", json={
        "email": "admin@test.com",
        "full_name": "Admin User",
        "password": "adminpass123",
    })
    # Promote to admin through the *same* session the app is using. A separate
    # session cannot see the row: the fixture transaction is still open and
    # uncommitted, so the promotion would silently no-op and every admin
    # request would 403.
    from app.models.user import User
    from app.core.enums import UserRole
    user_obj = db.query(User).filter(User.email == "admin@test.com").first()
    assert user_obj is not None, "admin registration failed"
    user_obj.role = UserRole.admin
    db.flush()

    resp = client.post("/api/v1/auth/login", json={"email": "admin@test.com", "password": "adminpass123"})
    return resp.json()["access_token"]


@pytest.fixture()
def user_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "user@test.com",
        "full_name": "Regular User",
        "password": "userpass123",
    })
    resp = client.post("/api/v1/auth/login", json={"email": "user@test.com", "password": "userpass123"})
    return resp.json()["access_token"]


@pytest.fixture()
def rate_limited():
    """Turn the rate limiter on for one test, with a clean counter store."""
    rate_limit.reset_local_counters()
    original = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = True
    yield
    settings.RATE_LIMIT_ENABLED = original
    rate_limit.reset_local_counters()


@pytest.fixture()
def cache_enabled():
    """Enable the cache-aside layer, skipping if no Redis is reachable."""
    original_enabled = settings.CACHE_ENABLED
    original_url = settings.REDIS_URL
    settings.CACHE_ENABLED = True
    settings.REDIS_URL = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
    cache.reset_client()

    client = cache.get_client()
    if client is None:
        settings.CACHE_ENABLED = original_enabled
        settings.REDIS_URL = original_url
        cache.reset_client()
        pytest.skip("Redis not available")

    client.flushdb()
    yield client

    client.flushdb()
    settings.CACHE_ENABLED = original_enabled
    settings.REDIS_URL = original_url
    cache.reset_client()


@pytest.fixture()
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
