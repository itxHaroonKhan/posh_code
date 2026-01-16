from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .task import Task


class UserBase(SQLModel):
    email: str = Field(unique=True, index=True, max_length=255)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    password_hash: str = Field(max_length=255)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    tasks: List["Task"] = Relationship(back_populates="user")


class UserCreate(SQLModel):
    email: str = Field(max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserRead(SQLModel):
    id: int
    email: str
    created_at: datetime


class UserLogin(SQLModel):
    email: str
    password: str
