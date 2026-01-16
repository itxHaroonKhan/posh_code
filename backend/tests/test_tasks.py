import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from src.main import app
from src.database import get_session
from src.models import User, Task
from src.services import AuthService


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


@pytest.fixture(name="auth_headers")
def auth_headers_fixture(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={"email": "test@example.com", "password": "password123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_create_task(client: TestClient, auth_headers: dict):
    response = client.post(
        "/api/tasks",
        json={"title": "Test Task", "description": "Test Description"},
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["completed"] is False


def test_create_task_unauthorized(client: TestClient):
    response = client.post(
        "/api/tasks",
        json={"title": "Test Task"}
    )
    assert response.status_code == 403


def test_list_tasks(client: TestClient, auth_headers: dict):
    client.post(
        "/api/tasks",
        json={"title": "Task 1"},
        headers=auth_headers
    )
    client.post(
        "/api/tasks",
        json={"title": "Task 2"},
        headers=auth_headers
    )

    response = client.get("/api/tasks", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_task(client: TestClient, auth_headers: dict):
    create_response = client.post(
        "/api/tasks",
        json={"title": "Test Task"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "Test Task"


def test_update_task(client: TestClient, auth_headers: dict):
    create_response = client.post(
        "/api/tasks",
        json={"title": "Original Title"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    response = client.put(
        f"/api/tasks/{task_id}",
        json={"title": "Updated Title"},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_delete_task(client: TestClient, auth_headers: dict):
    create_response = client.post(
        "/api/tasks",
        json={"title": "Task to Delete"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]

    response = client.delete(f"/api/tasks/{task_id}", headers=auth_headers)
    assert response.status_code == 204

    get_response = client.get(f"/api/tasks/{task_id}", headers=auth_headers)
    assert get_response.status_code == 404


def test_toggle_task_completion(client: TestClient, auth_headers: dict):
    create_response = client.post(
        "/api/tasks",
        json={"title": "Task to Toggle"},
        headers=auth_headers
    )
    task_id = create_response.json()["id"]
    assert create_response.json()["completed"] is False

    response = client.patch(f"/api/tasks/{task_id}/complete", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["completed"] is True

    response = client.patch(f"/api/tasks/{task_id}/complete", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["completed"] is False


def test_filter_completed_tasks(client: TestClient, auth_headers: dict):
    client.post(
        "/api/tasks",
        json={"title": "Pending Task"},
        headers=auth_headers
    )
    completed_response = client.post(
        "/api/tasks",
        json={"title": "Completed Task"},
        headers=auth_headers
    )
    task_id = completed_response.json()["id"]
    client.patch(f"/api/tasks/{task_id}/complete", headers=auth_headers)

    response = client.get("/api/tasks?completed=true", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Completed Task"

    response = client.get("/api/tasks?completed=false", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Pending Task"
