"""
Task CRUD endpoints with JWT authentication and user-scoped access.
All endpoints require valid JWT token and enforce task ownership.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from uuid import UUID
from typing import List
from app.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services import task_service


router = APIRouter(
    prefix="/api",
    tags=["tasks"],
    responses={
        401: {"description": "Unauthorized - Invalid or missing JWT token"},
        403: {"description": "Forbidden - User not authorized to access this resource"},
        404: {"description": "Not Found - Task does not exist"}
    }
)


@router.get("/{user_id}/tasks", response_model=List[TaskResponse], status_code=status.HTTP_200_OK)
def get_user_tasks(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> List[Task]:
    """
    Get all tasks for a specific user.

    **Authorization**: JWT user_id must match path user_id parameter.

    **Returns**: List of TaskResponse objects (empty array if no tasks).

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: JWT user_id does not match path user_id
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access tasks for this user"
        )

    tasks = task_service.get_user_tasks(session, user_id)
    return tasks


@router.post("/{user_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    user_id: UUID,
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Task:
    """
    Create a new task for a user.

    **Authorization**: JWT user_id must match path user_id parameter.

    **Request Body**: TaskCreate schema (title required, description optional)

    **Returns**: TaskResponse with created task including id and timestamps.

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: JWT user_id does not match path user_id
    - 422: Invalid request body (missing title, validation errors)
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create tasks for this user"
        )

    task = task_service.create_task(session, user_id, task_data)
    return task


@router.get("/{user_id}/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def get_task(
    user_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Task:
    """
    Get a specific task by ID.

    **Authorization**: JWT user_id must match path user_id, and task must belong to user.

    **Returns**: TaskResponse with task details.

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: User not authorized to access this task
    - 404: Task not found
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access tasks for this user"
        )

    task = task_service.get_task_by_id(session, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Verify task belongs to user
    if not task_service.validate_task_ownership(task, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task"
        )

    return task


@router.put("/{user_id}/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def update_task(
    user_id: UUID,
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Task:
    """
    Update a task (full update - all fields).

    **Authorization**: JWT user_id must match path user_id, and task must belong to user.

    **Request Body**: TaskUpdate schema (all fields optional)

    **Returns**: TaskResponse with updated task.

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: User not authorized to update this task
    - 404: Task not found
    - 422: Invalid request body
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update tasks for this user"
        )

    task = task_service.get_task_by_id(session, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Verify task belongs to user
    if not task_service.validate_task_ownership(task, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )

    updated_task = task_service.update_task(session, task, task_data)
    return updated_task


@router.patch("/{user_id}/tasks/{task_id}/complete", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def toggle_task_completion(
    user_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Task:
    """
    Toggle completion status of a task.

    **Authorization**: JWT user_id must match path user_id, and task must belong to user.

    **Returns**: TaskResponse with updated task status.

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: User not authorized to update this task
    - 404: Task not found
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update tasks for this user"
        )

    task = task_service.get_task_by_id(session, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Verify task belongs to user
    if not task_service.validate_task_ownership(task, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )

    updated_task = task_service.toggle_task_completion(session, task)
    return updated_task


@router.patch("/{user_id}/tasks/{task_id}", response_model=TaskResponse, status_code=status.HTTP_200_OK)
def partial_update_task(
    user_id: UUID,
    task_id: UUID,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> Task:
    """
    Partially update a task (only specified fields).

    **Authorization**: JWT user_id must match path user_id, and task must belong to user.

    **Request Body**: TaskUpdate schema (only provided fields will be updated)

    **Returns**: TaskResponse with updated task.

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: User not authorized to update this task
    - 404: Task not found
    - 422: Invalid request body
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update tasks for this user"
        )

    task = task_service.get_task_by_id(session, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Verify task belongs to user
    if not task_service.validate_task_ownership(task, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this task"
        )

    updated_task = task_service.update_task(session, task, task_data)
    return updated_task


@router.delete("/{user_id}/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    user_id: UUID,
    task_id: UUID,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> None:
    """
    Delete a task.

    **Authorization**: JWT user_id must match path user_id, and task must belong to user.

    **Returns**: 204 No Content on success.

    **Errors**:
    - 401: Missing or invalid JWT token
    - 403: User not authorized to delete this task
    - 404: Task not found
    """
    # Verify JWT user_id matches path user_id
    if str(current_user.id) != str(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete tasks for this user"
        )

    task = task_service.get_task_by_id(session, task_id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {task_id} not found"
        )

    # Verify task belongs to user
    if not task_service.validate_task_ownership(task, user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this task"
        )

    task_service.delete_task(session, task)
    return None
