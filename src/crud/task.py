from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload

from src.models import Task, TaskStatus
from src.schemas.task import TaskCreate, TaskUpdate


async def create_task(session: AsyncSession, task_in: TaskCreate) -> Task:
    task = Task(**task_in.model_dump())
    session.add(task)
    await session.commit()
    await session.refresh(task)
    return task


async def get_task(session: AsyncSession, task_id: int) -> Task | None:
    result = await session.execute(
        select(Task).where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def get_tasks(
        session: AsyncSession,
        project_id: int | None = None,
        sprint_id: int | None = None,
        status: TaskStatus | None = None,
        skip: int = 0,
        limit: int = 100
) -> list[Task]:
    query = select(Task)

    filters = []
    if project_id:
        filters.append(Task.project_id == project_id)
    if sprint_id:
        filters.append(Task.sprint_id == sprint_id)
    if status:
        filters.append(Task.status == status)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def update_task(
        session: AsyncSession,
        task_id: int,
        updates: TaskUpdate
) -> Task | None:
    task = await get_task(session, task_id)
    if not task:
        return None

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(task, key, value)

    await session.commit()
    await session.refresh(task)
    return task


async def delete_task(session: AsyncSession, task_id: int) -> Task | None:
    task = await get_task(session, task_id)
    if not task:
        return None

    await session.delete(task)
    await session.commit()
    return task


async def move_task_to_sprint(
        session: AsyncSession,
        task_id: int,
        sprint_id: int | None
) -> Task | None:
    task = await get_task(session, task_id)
    if not task:
        return None

    task.sprint_id = sprint_id
    if sprint_id:
        task.status = TaskStatus.SPRINT
    else:
        task.status = TaskStatus.BACKLOG

    await session.commit()
    await session.refresh(task)
    return task