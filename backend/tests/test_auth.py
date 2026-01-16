import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.main import app
from src.database import get_session
from src.models import User


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_register_user(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["email"] == "test@example.com"


def test_register_duplicate_email(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password456"}
    )
    assert response.status_code == 400


def test_login_success(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


def test_login_wrong_password(client: TestClient):
    client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401


def test_login_nonexistent_user(client: TestClient):
    response = client.post(
        "/api/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"}
    )
    assert response.status_code == 401
