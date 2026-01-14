"""
Authentication service for password hashing, JWT token generation, and verification.
"""
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from uuid import UUID

from ..config import settings


# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string (bcrypt format)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_jwt_token(user_id: UUID, email: str) -> str:
    """
    Create a JWT access token for authenticated user.

    Args:
        user_id: User's UUID
        email: User's email address

    Returns:
        JWT token string

    Token payload structure:
        - sub: user_id (subject)
        - email: user's email
        - exp: expiration timestamp
        - iat: issued at timestamp
    """
    # Calculate expiration time
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)

    # Create token payload
    payload = {
        "sub": str(user_id),  # Subject (user ID)
        "email": email,
        "exp": expire,  # Expiration time
        "iat": datetime.utcnow()  # Issued at
    }

    # Encode and sign token
    token = jwt.encode(
        payload,
        settings.BETTER_AUTH_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


def decode_jwt_token(token: str) -> Optional[dict]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded payload dict if valid, None if invalid/expired

    Raises:
        JWTError: If token is invalid, expired, or signature verification fails
    """
    try:
        payload = jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token_signature(token: str) -> bool:
    """
    Verify JWT token signature without decoding.

    Args:
        token: JWT token string

    Returns:
        True if signature is valid, False otherwise
    """
    try:
        jwt.decode(
            token,
            settings.BETTER_AUTH_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_exp": False}  # Don't check expiration, just signature
        )
        return True
    except JWTError:
        return False


def extract_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID (UUID string) if token is valid, None otherwise
    """
    payload = decode_jwt_token(token)
    if payload:
        return payload.get("sub")
    return None
