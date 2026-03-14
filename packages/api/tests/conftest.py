import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database.base import Base
from app.dependencies import get_db
from app.models import user, category, tag, product, review, wishlist, coupon, address, cart, order  # noqa: F401

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
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
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
def admin_token(client):
    client.post("/api/v1/auth/register", json={
        "email": "admin@test.com",
        "full_name": "Admin User",
        "password": "adminpass123",
    })
    # Manually set role to admin in DB
    from app.models.user import User
    from app.core.enums import UserRole
    db_session = TestingSessionLocal()
    user_obj = db_session.query(User).filter(User.email == "admin@test.com").first()
    if user_obj:
        user_obj.role = UserRole.admin
        db_session.commit()
    db_session.close()

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
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture()
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}
