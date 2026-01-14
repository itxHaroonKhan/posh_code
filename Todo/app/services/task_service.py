"""
Task service layer for business logic.
Handles task retrieval, creation, updates, and ownership validation.
"""

from sqlmodel import Session, select
from uuid import UUID
from datetime import datetime
from typing import List, Optional
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate


def get_user_tasks(session: Session, user_id: UUID) -> List[Task]:
    """
    Retrieve all tasks for a specific user.

    Args:
        session: Database session
        user_id: UUID of the user

    Returns:
        List of Task objects belonging to the user (empty list if none)
    """
    statement = select(Task).where(Task.user_id == user_id).order_by(Task.created_at.desc())
    tasks = session.exec(statement).all()
    return list(tasks)


def create_task(session: Session, user_id: UUID, task_data: TaskCreate) -> Task:
    """
    Create a new task for a user.

    Args:
        session: Database session
        user_id: UUID of the task owner
        task_data: TaskCreate schema with title and optional description

    Returns:
        Created Task object with auto-generated id and timestamps
    """
    task = Task(
        user_id=user_id,
        title=task_data.title,
        description=task_data.description,
        status="pending",  # Default status for new tasks
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    return task


def get_task_by_id(session: Session, task_id: UUID) -> Optional[Task]:
    """
    Retrieve a single task by its ID.

    Args:
        session: Database session
        task_id: UUID of the task

    Returns:
        Task object if found, None otherwise
    """
    statement = select(Task).where(Task.id == task_id)
    task = session.exec(statement).first()
    return task


def update_task(session: Session, task: Task, task_data: TaskUpdate) -> Task:
    """
    Update an existing task with provided data.
    Only updates fields that are explicitly provided (not None).

    Args:
        session: Database session
        task: Existing Task object to update
        task_data: TaskUpdate schema with optional fields

    Returns:
        Updated Task object
    """
    update_data = task_data.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(task, field, value)

    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    return task


def delete_task(session: Session, task: Task) -> None:
    """
    Delete a task from the database.

    Args:
        session: Database session
        task: Task object to delete
    """
    session.delete(task)
    session.commit()


def validate_task_ownership(task: Task, user_id: UUID) -> bool:
    """
    Verify that a task belongs to a specific user.

    Args:
        task: Task object to check
        user_id: UUID of the user claiming ownership

    Returns:
        True if task belongs to user, False otherwise
    """
    return task.user_id == user_id


def toggle_task_completion(session: Session, task: Task) -> Task:
    """
    Toggle the completion status of a task.
    If the task is pending, change to completed. If completed, change to pending.

    Args:
        session: Database session
        task: Task object to update

    Returns:
        Updated Task object
    """
    if task.status == "completed":
        task.status = "pending"
    else:
        task.status = "completed"

    task.updated_at = datetime.utcnow()

    session.add(task)
    session.commit()
    session.refresh(task)

    return task
