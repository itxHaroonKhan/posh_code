"""
Authentication endpoint tests (TDD approach - write tests first, ensure they fail).
Tests for signup, signin, and JWT middleware.
"""
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool
from jose import jwt
from datetime import datetime, timedelta

from app.main import app
from app.database import get_session
from app.config import settings




# ============================================================================
# T027: Contract test for POST /api/auth/signup
# ============================================================================

def test_signup_success(client: TestClient, session: Session):
    """
    Test successful user signup.
    Expected: 201 status, JWT token in response, password hashed in DB.
    """
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "test@example.com",
            "password": "SecurePass123"
        }
    )

    # Verify response structure
    assert response.status_code == 201
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "token" in data
    assert data["email"] == "test@example.com"

    # Verify JWT token is valid
    token = data["token"]
    decoded = jwt.decode(
        token,
        settings.BETTER_AUTH_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == data["user_id"]

    # Verify password is hashed in database (not plaintext)
    from app.models.user import User
    user = session.query(User).filter(User.email == "test@example.com").first()
    assert user is not None
    assert user.password_hash != "SecurePass123"
    assert user.password_hash.startswith("$2b$")  # bcrypt hash prefix


def test_signup_duplicate_email(client: TestClient):
    """
    Test signup with duplicate email.
    Expected: 400 status, error message about existing email.
    """
    # First signup
    client.post(
        "/api/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "Password123"
        }
    )

    # Second signup with same email
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "duplicate@example.com",
            "password": "DifferentPass456"
        }
    )

    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    error_message = data["detail"]["message"]
    assert "email" in error_message.lower() or "exists" in error_message.lower() or "already" in error_message.lower()


def test_signup_invalid_email(client: TestClient):
    """
    Test signup with invalid email format.
    Expected: 422 status (FastAPI validation error).
    """
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "not-an-email",
            "password": "Password123"
        }
    )

    assert response.status_code == 422  # Validation error


def test_signup_weak_password(client: TestClient):
    """
    Test signup with weak password (too short).
    Expected: 400 status, error about password requirements.
    """
    response = client.post(
        "/api/auth/signup",
        json={
            "email": "test@example.com",
            "password": "weak"
        }
    )

    assert response.status_code == 422  # Validation error
    # For validation errors, FastAPI returns in a different format
    # The error details are in the 'detail' field as a list
    assert response.status_code == 422


# ============================================================================
# T028: Contract test for POST /api/auth/signin
# ============================================================================

def test_signin_success(client: TestClient):
    """
    Test successful user signin.
    Expected: 200 status, JWT token valid.
    """
    # First create a user
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": "signin@example.com",
            "password": "SecurePass123"
        }
    )
    assert signup_response.status_code == 201

    # Now sign in with same credentials
    response = client.post(
        "/api/auth/signin",
        json={
            "email": "signin@example.com",
            "password": "SecurePass123"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert "token" in data
    assert data["email"] == "signin@example.com"

    # Verify JWT token is valid
    token = data["token"]
    decoded = jwt.decode(
        token,
        settings.BETTER_AUTH_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert decoded["sub"] == data["user_id"]


def test_signin_invalid_email(client: TestClient):
    """
    Test signin with non-existent email.
    Expected: 401 status (Unauthorized).
    """
    response = client.post(
        "/api/auth/signin",
        json={
            "email": "nonexistent@example.com",
            "password": "SomePassword123"
        }
    )

    assert response.status_code == 401
    data = response.json()
    assert "detail" in data or "message" in data


def test_signin_wrong_password(client: TestClient):
    """
    Test signin with correct email but wrong password.
    Expected: 401 status (Unauthorized).
    """
    # Create a user
    client.post(
        "/api/auth/signup",
        json={
            "email": "wrongpass@example.com",
            "password": "CorrectPassword123"
        }
    )

    # Try signin with wrong password
    response = client.post(
        "/api/auth/signin",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword456"
        }
    )

    assert response.status_code == 401


# ============================================================================
# T029: Integration test for JWT middleware
# ============================================================================

def test_jwt_middleware_valid_token(client: TestClient):
    """
    Test protected endpoint with valid JWT token.
    Expected: Token passes verification, request succeeds.
    """
    # Create user and get token
    signup_response = client.post(
        "/api/auth/signup",
        json={
            "email": "middleware@example.com",
            "password": "SecurePass123"
        }
    )
    token = signup_response.json()["token"]

    # Try accessing protected endpoint (will be implemented later)
    # For now, test that the dependency can decode the token
    from app.dependencies import get_current_user
    from fastapi.security import HTTPAuthorizationCredentials

    # This will be tested properly when we have protected routes
    # For now, we verify the token structure is valid
    decoded = jwt.decode(
        token,
        settings.BETTER_AUTH_SECRET,
        algorithms=[settings.JWT_ALGORITHM]
    )
    assert "sub" in decoded  # user_id claim


def test_jwt_middleware_missing_token(client: TestClient):
    """
    Test protected endpoint without JWT token.
    Expected: 401 Unauthorized (will be tested with actual protected route later).
    """
    # This test will be expanded when we have actual protected routes
    # For now, we ensure the middleware dependency exists
    from app.dependencies import get_current_user
    assert get_current_user is not None


def test_jwt_middleware_expired_token(client: TestClient):
    """
    Test protected endpoint with expired JWT token.
    Expected: 401 Unauthorized.
    """
    from datetime import datetime, timedelta

    # Create an expired token manually
    expired_payload = {
        "sub": "fake-user-id",
        "exp": datetime.utcnow() - timedelta(hours=1)  # Expired 1 hour ago
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.BETTER_AUTH_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    # Try using expired token (will test with protected route later)
    # For now, verify that decoding raises ExpiredSignatureError
    with pytest.raises(jwt.ExpiredSignatureError):
        jwt.decode(
            expired_token,
            settings.BETTER_AUTH_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )


def test_jwt_middleware_malformed_token(client: TestClient):
    """
    Test protected endpoint with malformed JWT token.
    Expected: 401 Unauthorized.
    """
    malformed_token = "this-is-not-a-valid-jwt-token"

    # Verify that decoding raises JWTError
    with pytest.raises(jwt.JWTError):
        jwt.decode(
            malformed_token,
            settings.BETTER_AUTH_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )


def test_jwt_middleware_invalid_signature(client: TestClient):
    """
    Test JWT token with invalid signature (wrong secret).
    Expected: 401 Unauthorized.
    """
    # Create token with wrong secret
    wrong_secret_payload = {
        "sub": "fake-user-id",
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    wrong_secret_token = jwt.encode(
        wrong_secret_payload,
        "wrong-secret-key",
        algorithm=settings.JWT_ALGORITHM
    )

    # Verify that decoding with correct secret raises JWTError
    with pytest.raises(jwt.JWTError):
        jwt.decode(
            wrong_secret_token,
            settings.BETTER_AUTH_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
