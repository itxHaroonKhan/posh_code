"""
Pydantic schemas for authentication requests and responses.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID
from typing import Optional


class SignupRequest(BaseModel):
    """Request schema for user signup."""
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=72,  # bcrypt limit
        description="User password (min 8 characters, max 72 characters)",
        examples=["SecurePass123"]
    )

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password meets minimum requirements:
        - At least 8 characters
        - Contains at least one uppercase letter
        - Contains at least one lowercase letter
        - Contains at least one digit
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")

        return v


class SigninRequest(BaseModel):
    """Request schema for user signin."""
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePass123"]
    )


class TokenResponse(BaseModel):
    """Response schema for successful authentication."""
    user_id: str = Field(
        ...,
        description="User ID (UUID)",
        examples=["550e8400-e29b-41d4-a716-446655440000"]
    )
    email: str = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    token: str = Field(
        ...,
        description="JWT access token",
        examples=["eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."]
    )

    class Config:
        from_attributes = True  # Enable ORM mode for SQLModel compatibility
        arbitrary_types_allowed = True
        json_schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJleHAiOjE3MzY4NTcyMDB9.xyz..."
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    error: str = Field(
        ...,
        description="Error type",
        examples=["Bad Request", "Unauthorized", "Forbidden"]
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Email already exists", "Invalid credentials"]
    )
    detail: Optional[str] = Field(
        None,
        description="Additional error details (optional)",
        examples=["User with email user@example.com already registered"]
    )
