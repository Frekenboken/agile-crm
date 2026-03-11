from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from src.models import Project, UserRole
from src.schemas.project import ProjectCreate, ProjectUpdate
from src.crud import project_member as pm_crud


async def create_project(
        session: AsyncSession,
        project_in: ProjectCreate,
        owner_id: int
) -> Project | None:
    # Проверка уникальности ключа
    existing = await get_project_by_key(session, project_in.key)
    if existing:
        return None

    project = Project(**project_in.model_dump())
    session.add(project)
    await session.flush()  # Чтобы получить id проекта

    # Добавляем создателя как владельца проекта
    await pm_crud.add_member_to_project(
        session,
        project_id=project.id,
        user_id=owner_id,
        role=UserRole.PRODUCT_OWNER
    )

    await session.commit()
    await session.refresh(project)
    return project


async def get_project(session: AsyncSession, project_id: int) -> Project | None:
    result = await session.execute(
        select(Project).where(Project.id == project_id)
    )
    return result.scalar_one_or_none()


async def get_project_by_key(session: AsyncSession, key: str) -> Project | None:
    result = await session.execute(
        select(Project).where(Project.key == key)
    )
    return result.scalar_one_or_none()


async def get_projects(
        session: AsyncSession,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 100
) -> list[Project]:
    query = select(Project)

    if user_id:
        query = query.join(Project.members).where(
            ProjectMember.user_id == user_id
        )

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def update_project(
        session: AsyncSession,
        project_id: int,
        updates: ProjectUpdate
) -> Project | None:
    project = await get_project(session, project_id)
    if not project:
        return None

    # Проверка уникальности ключа при обновлении
    if updates.key and updates.key != project.key:
        existing = await get_project_by_key(session, updates.key)
        if existing:
            return None

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(project, key, value)

    await session.commit()
    await session.refresh(project)
    return project


async def delete_project(session: AsyncSession, project_id: int) -> Project | None:
    project = await get_project(session, project_id)
    if not project:
        return None

    await session.delete(project)
    await session.commit()
    return project


async def get_project_with_details(session: AsyncSession, project_id: int) -> Project | None:
    """Получить проект со всеми связанными данными"""
    result = await session.execute(
        select(Project)
        .where(Project.id == project_id)
        .options(
            selectinload(Project.sprints),
            selectinload(Project.tasks),
            selectinload(Project.members).selectinload(ProjectMember.user)
        )
    )
    return result.scalar_one_or_none()