from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime

from src.models import Sprint, Task, TaskStatus
from src.schemas.sprint import SprintCreate, SprintUpdate


async def create_sprint(session: AsyncSession, sprint_in: SprintCreate) -> Sprint:
    sprint = Sprint(**sprint_in.model_dump())
    session.add(sprint)
    await session.commit()
    await session.refresh(sprint)
    return sprint


async def get_sprint(session: AsyncSession, sprint_id: int) -> Sprint | None:
    result = await session.execute(
        select(Sprint).where(Sprint.id == sprint_id)
    )
    return result.scalar_one_or_none()


async def get_sprints(
        session: AsyncSession,
        project_id: int | None = None,
        is_active: bool | None = None,
        skip: int = 0,
        limit: int = 100
) -> list[Sprint]:
    query = select(Sprint)

    filters = []
    if project_id:
        filters.append(Sprint.project_id == project_id)
    if is_active is not None:
        filters.append(Sprint.is_active == is_active)

    if filters:
        query = query.where(and_(*filters))

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def update_sprint(
        session: AsyncSession,
        sprint_id: int,
        updates: SprintUpdate
) -> Sprint | None:
    sprint = await get_sprint(session, sprint_id)
    if not sprint:
        return None

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(sprint, key, value)

    await session.commit()
    await session.refresh(sprint)
    return sprint


async def delete_sprint(session: AsyncSession, sprint_id: int) -> Sprint | None:
    sprint = await get_sprint(session, sprint_id)
    if not sprint:
        return None

    # Возвращаем задачи в бэклог
    await session.execute(
        select(Task)
        .where(Task.sprint_id == sprint_id)
        .update({Task.sprint_id: None, Task.status: TaskStatus.BACKLOG})
    )

    await session.delete(sprint)
    await session.commit()
    return sprint


async def start_sprint(
        session: AsyncSession,
        sprint_id: int,
        start_date: datetime,
        end_date: datetime
) -> Sprint | None:
    # Деактивируем другие активные спринты в проекте
    sprint = await get_sprint(session, sprint_id)
    if not sprint:
        return None

    await session.execute(
        select(Sprint)
        .where(
            and_(
                Sprint.project_id == sprint.project_id,
                Sprint.is_active == True,
                Sprint.id != sprint_id
            )
        )
        .update({Sprint.is_active: False})
    )

    sprint.is_active = True
    sprint.start_date = start_date
    sprint.end_date = end_date

    await session.commit()
    await session.refresh(sprint)
    return sprint


async def complete_sprint(session: AsyncSession, sprint_id: int) -> Sprint | None:
    sprint = await get_sprint(session, sprint_id)
    if not sprint:
        return None

    sprint.is_active = False
    sprint.end_date = datetime.now()

    # Задачи, которые не завершены, возвращаются в бэклог
    await session.execute(
        select(Task)
        .where(
            and_(
                Task.sprint_id == sprint_id,
                Task.status != TaskStatus.DONE
            )
        )
        .update({Task.sprint_id: None, Task.status: TaskStatus.BACKLOG})
    )

    await session.commit()
    await session.refresh(sprint)
    return sprint