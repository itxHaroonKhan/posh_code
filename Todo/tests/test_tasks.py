"""
Test suite for Task CRUD endpoints - TDD approach.
Tests verify task creation, retrieval, user-scoped access, and ownership enforcement.
"""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session
from uuid import uuid4
from app.models.user import User
from app.models.task import Task
from app.services.auth_service import hash_password, create_jwt_token


# T048: Contract test for GET /api/{user_id}/tasks
def test_get_user_tasks_success(client: TestClient, session: Session):
    """Test GET /api/{user_id}/tasks returns 200 with user's tasks only"""
    # Create user and authenticate
    user = User(email="taskuser@example.com", password_hash=hash_password("TaskPass123"))
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_jwt_token(user.id, user.email)

    # Create tasks for this user
    task1 = Task(user_id=user.id, title="Task 1", description="Description 1", status="pending")
    task2 = Task(user_id=user.id, title="Task 2", description="Description 2", status="completed")
    session.add_all([task1, task2])
    session.commit()

    # Create another user with tasks (should not be returned)
    other_user = User(email="otheruser@example.com", password_hash=hash_password("OtherPass123"))
    session.add(other_user)
    session.commit()
    session.refresh(other_user)

    other_task = Task(user_id=other_user.id, title="Other Task", description="Not visible", status="pending")
    session.add(other_task)
    session.commit()

    # Request user's tasks
    response = client.get(
        f"/api/{user.id}/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert all(task["user_id"] == str(user.id) for task in data)
    assert any(task["title"] == "Task 1" for task in data)
    assert any(task["title"] == "Task 2" for task in data)
    assert not any(task["title"] == "Other Task" for task in data)


def test_get_user_tasks_unauthorized(client: TestClient, session: Session):
    """Test GET /api/{user_id}/tasks returns 401 without token"""
    user_id = uuid4()
    response = client.get(f"/api/{user_id}/tasks")
    assert response.status_code == 401


def test_get_user_tasks_forbidden_wrong_user(client: TestClient, session: Session):
    """Test GET /api/{user_id}/tasks returns 403 if JWT user_id doesn't match path user_id"""
    # Create two users
    user1 = User(email="user1@example.com", password_hash=hash_password("Pass123"))
    user2 = User(email="user2@example.com", password_hash=hash_password("Pass123"))
    session.add_all([user1, user2])
    session.commit()
    session.refresh(user1)
    session.refresh(user2)

    # User 1 tries to access User 2's tasks
    token = create_jwt_token(user1.id, user1.email)
    response = client.get(
        f"/api/{user2.id}/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


# T049: Contract test for POST /api/{user_id}/tasks
def test_create_task_success(client: TestClient, session: Session):
    """Test POST /api/{user_id}/tasks creates task with 201 response"""
    # Create user and authenticate
    user = User(email="creator@example.com", password_hash=hash_password("CreatePass123"))
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_jwt_token(user.id, user.email)

    # Create task
    task_data = {
        "title": "New Task",
        "description": "Task description"
    }

    response = client.post(
        f"/api/{user.id}/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "New Task"
    assert data["description"] == "Task description"
    assert data["status"] == "pending"  # Default status
    assert data["user_id"] == str(user.id)
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data

    # Verify task exists in database
    task_in_db = session.query(Task).filter(Task.title == "New Task").first()
    assert task_in_db is not None
    assert task_in_db.user_id == user.id


def test_create_task_forbidden_user_mismatch(client: TestClient, session: Session):
    """Test POST /api/{user_id}/tasks returns 403 if JWT user_id doesn't match path user_id"""
    # Create two users
    user1 = User(email="user1@example.com", password_hash=hash_password("Pass123"))
    user2 = User(email="user2@example.com", password_hash=hash_password("Pass123"))
    session.add_all([user1, user2])
    session.commit()
    session.refresh(user1)
    session.refresh(user2)

    # User 1 tries to create task for User 2
    token = create_jwt_token(user1.id, user1.email)
    task_data = {"title": "Unauthorized Task", "description": "Should fail"}

    response = client.post(
        f"/api/{user2.id}/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()


def test_create_task_validation_error(client: TestClient, session: Session):
    """Test POST /api/{user_id}/tasks returns 422 with invalid data (missing title)"""
    user = User(email="validator@example.com", password_hash=hash_password("ValidPass123"))
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_jwt_token(user.id, user.email)

    # Missing required title
    task_data = {"description": "No title provided"}

    response = client.post(
        f"/api/{user.id}/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 422


# T050: Integration test for task ownership
def test_task_ownership_enforcement(client: TestClient, session: Session):
    """Test user A cannot access user B's tasks via API (returns 403)"""
    # Create two users
    user_a = User(email="usera@example.com", password_hash=hash_password("PassA123"))
    user_b = User(email="userb@example.com", password_hash=hash_password("PassB123"))
    session.add_all([user_a, user_b])
    session.commit()
    session.refresh(user_a)
    session.refresh(user_b)

    # User A creates a task
    token_a = create_jwt_token(user_a.id, user_a.email)
    task_data = {"title": "User A Task", "description": "Private to User A"}

    response = client.post(
        f"/api/{user_a.id}/tasks",
        json=task_data,
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 201

    # User B tries to access User A's tasks (should fail with 403)
    token_b = create_jwt_token(user_b.id, user_b.email)
    response = client.get(
        f"/api/{user_a.id}/tasks",
        headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response.status_code == 403
    assert "not authorized" in response.json()["detail"].lower()

    # User B can access their own tasks (should succeed with empty list)
    response = client.get(
        f"/api/{user_b.id}/tasks",
        headers={"Authorization": f"Bearer {token_b}"}
    )

    assert response.status_code == 200
    assert len(response.json()) == 0  # User B has no tasks


def test_empty_task_list(client: TestClient, session: Session):
    """Test GET /api/{user_id}/tasks returns empty array for user with no tasks"""
    user = User(email="notasks@example.com", password_hash=hash_password("NoTasks123"))
    session.add(user)
    session.commit()
    session.refresh(user)

    token = create_jwt_token(user.id, user.email)

    response = client.get(
        f"/api/{user.id}/tasks",
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert response.json() == []
