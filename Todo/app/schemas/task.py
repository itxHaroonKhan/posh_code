


"""
Pydantic schemas for Task API request/response validation.
Defines TaskCreate, TaskUpdate, and TaskResponse models.
"""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID
from datetime import datetime
from typing import Optional


class TaskCreate(BaseModel):
    """
    Schema for creating a new task.
    Only title and optional description required; status defaults to "pending".
    """
    title: str = Field(min_length=1, max_length=255, description="Task title (required)")
    description: Optional[str] = Field(default=None, max_length=2000, description="Task description (optional)")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: str) -> str:
        """Ensure title is not just whitespace"""
        if not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip()

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Complete project documentation",
                "description": "Write README and API docs"
            }
        }


class TaskUpdate(BaseModel):
    """
    Schema for updating an existing task.
    All fields are optional; only provided fields will be updated.
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=255, description="Task title")
    description: Optional[str] = Field(default=None, max_length=2000, description="Task description")
    status: Optional[str] = Field(default=None, max_length=50, description="Task status (pending, completed)")

    @field_validator("title")
    @classmethod
    def validate_title_not_empty(cls, v: Optional[str]) -> Optional[str]:
        """Ensure title is not just whitespace if provided"""
        if v is not None and not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")
        return v.strip() if v else None

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        """Validate status is one of allowed values"""
        if v is not None:
            allowed_statuses = ["pending", "completed"]
            if v not in allowed_statuses:
                raise ValueError(f"Status must be one of: {', '.join(allowed_statuses)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated task title",
                "description": "Updated description",
                "status": "completed"
            }
        }


class TaskResponse(BaseModel):
    """
    Schema for task API responses.
    Includes all fields including id, timestamps, and user_id.
    """
    id: UUID
    user_id: UUID
    title: str
    description: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # Enable ORM mode for SQLModel compatibility
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "user_id": "660e9500-f39c-52e5-b827-557766551111",
                "title": "Complete project documentation",
                "description": "Write README and API docs",
                "status": "pending",
                "created_at": "2026-01-14T10:30:00Z",
                "updated_at": "2026-01-14T10:30:00Z"
            }
        }
