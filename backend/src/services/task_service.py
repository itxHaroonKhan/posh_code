from datetime import datetime
from typing import List, Optional
from sqlmodel import Session, select

from ..models import Task, TaskCreate, TaskUpdate


class TaskService:
    @staticmethod
    def get_tasks_by_user(
        session: Session,
        user_id: int,
        completed: Optional[bool] = None
    ) -> List[Task]:
        query = select(Task).where(Task.user_id == user_id)

        if completed is not None:
            query = query.where(Task.completed == completed)

        query = query.order_by(Task.created_at.desc())
        return list(session.exec(query).all())

    @staticmethod
    def get_task_by_id(
        session: Session, task_id: int, user_id: int
    ) -> Optional[Task]:
        task = session.get(Task, task_id)
        if task and task.user_id == user_id:
            return task
        return None

    @staticmethod
    def create_task(
        session: Session, user_id: int, task_data: TaskCreate
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=task_data.title,
            description=task_data.description
        )
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def update_task(
        session: Session,
        task_id: int,
        user_id: int,
        task_data: TaskUpdate
    ) -> Optional[Task]:
        task = TaskService.get_task_by_id(session, task_id, user_id)

        if not task:
            return None

        update_data = task_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(task, field, value)

        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task

    @staticmethod
    def delete_task(
        session: Session, task_id: int, user_id: int
    ) -> bool:
        task = TaskService.get_task_by_id(session, task_id, user_id)

        if not task:
            return False

        session.delete(task)
        session.commit()
        return True

    @staticmethod
    def toggle_task_completion(
        session: Session, task_id: int, user_id: int
    ) -> Optional[Task]:
        task = TaskService.get_task_by_id(session, task_id, user_id)

        if not task:
            return None

        task.completed = not task.completed
        task.updated_at = datetime.utcnow()
        session.add(task)
        session.commit()
        session.refresh(task)
        return task
