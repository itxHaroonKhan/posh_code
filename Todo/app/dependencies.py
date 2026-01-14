"""
Dependency injection functions for FastAPI routes.
Includes JWT token verification and user authentication.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlmodel import Session, select
from typing import Optional
from .config import settings
from .database import get_session

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: Session = Depends(get_session)
):
    """
    Dependency function to verify JWT token and extract current user.

    Args:
        credentials: HTTPAuthorizationCredentials from Authorization header
        session: Database session

    Returns:
        User object if token is valid

    Raises:
        HTTPException 401: If token is invalid, expired, or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Extract token from credentials
        token = credentials.credentials

        # Decode JWT token
        payload = jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Extract user_id from token payload
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    # Import User model here to avoid circular imports
    from .models.user import User

    # Fetch user from database
    statement = select(User).where(User.id == user_id)
    user = session.exec(statement).first()

    if user is None:
        raise credentials_exception

    return user


def verify_user_ownership(current_user_id: str, resource_user_id: str) -> None:
    """
    Verify that the current user owns the resource.

    Args:
        current_user_id: ID of the authenticated user
        resource_user_id: ID of the user who owns the resource

    Raises:
        HTTPException 403: If user does not own the resource
    """
    if str(current_user_id) != str(resource_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this resource"
        )
