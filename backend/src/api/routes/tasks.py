from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session

from ...database import get_session
from ...models import Task, TaskCreate, TaskRead, TaskUpdate, User
from ...services import TaskService
from ..dependencies import get_current_user

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("", response_model=List[TaskRead])
async def list_tasks(
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
    completed: Annotated[Optional[bool], Query()] = None
):
    tasks = TaskService.get_tasks_by_user(
        session, current_user.id, completed
    )
    return tasks


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED
)
async def create_task(
    task_data: TaskCreate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    task = TaskService.create_task(session, current_user.id, task_data)
    return task


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    task = TaskService.get_task_by_id(session, task_id, current_user.id)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    task_data: TaskUpdate,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    task = TaskService.update_task(
        session, task_id, current_user.id, task_data
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    deleted = TaskService.delete_task(session, task_id, current_user.id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )


@router.patch("/{task_id}/complete", response_model=TaskRead)
async def toggle_task_completion(
    task_id: int,
    session: Annotated[Session, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)]
):
    task = TaskService.toggle_task_completion(
        session, task_id, current_user.id
    )

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task
