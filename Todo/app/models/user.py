"""
User model for authentication and task ownership.
SQLModel table with UUID primary key, unique email, and password hash.
"""
from sqlmodel import SQLModel, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional


class User(SQLModel, table=True):
    """
    User table for authentication.
    Each user can have multiple tasks (1:N relationship).
    """
    __tablename__ = "users"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        index=True,
        nullable=False
    )

    email: str = Field(
        unique=True,
        index=True,
        nullable=False,
        max_length=255,
        sa_column_kwargs={"unique": True}
    )

    password_hash: str = Field(
        nullable=False,
        max_length=255
    )

    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )

    # Note: tasks relationship will be added in Phase 3 (User Story 2)
    # when we create the Task model
    # tasks: list["Task"] = Relationship(back_populates="owner")

    class Config:
        """Pydantic model configuration."""
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "created_at": "2026-01-14T10:30:00Z"
            }
        }

    def __repr__(self) -> str:
        return f"<User {self.email}>"
