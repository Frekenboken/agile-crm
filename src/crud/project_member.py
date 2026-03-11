from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, delete
from sqlalchemy.orm import selectinload

from src.models import ProjectMember, UserRole
from src.schemas.project_member import ProjectMemberCreate, ProjectMemberUpdate


async def add_member_to_project(
        session: AsyncSession,
        project_id: int,
        user_id: int,
        role: UserRole = UserRole.DEVELOPER
) -> ProjectMember | None:
    # Проверяем, не состоит ли уже пользователь в проекте
    existing = await get_project_member(session, project_id, user_id)
    if existing:
        return None

    member = ProjectMember(
        project_id=project_id,
        user_id=user_id,
        role=role
    )
    session.add(member)
    await session.commit()
    await session.refresh(member)
    return member


async def get_project_member(
        session: AsyncSession,
        project_id: int,
        user_id: int
) -> ProjectMember | None:
    result = await session.execute(
        select(ProjectMember)
        .where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.user_id == user_id
            )
        )
    )
    return result.scalar_one_or_none()


async def get_project_members(
        session: AsyncSession,
        project_id: int,
        role: UserRole | None = None,
        skip: int = 0,
        limit: int = 100
) -> list[ProjectMember]:
    query = select(ProjectMember).where(ProjectMember.project_id == project_id)

    if role:
        query = query.where(ProjectMember.role == role)

    query = query.offset(skip).limit(limit)
    result = await session.execute(query)
    return result.scalars().all()


async def get_user_projects(
        session: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 100
) -> list[ProjectMember]:
    result = await session.execute(
        select(ProjectMember)
        .where(ProjectMember.user_id == user_id)
        .options(selectinload(ProjectMember.project))
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def update_member_role(
        session: AsyncSession,
        project_id: int,
        user_id: int,
        updates: ProjectMemberUpdate
) -> ProjectMember | None:
    member = await get_project_member(session, project_id, user_id)
    if not member:
        return None

    for key, value in updates.model_dump(exclude_unset=True).items():
        setattr(member, key, value)

    await session.commit()
    await session.refresh(member)
    return member


async def remove_member_from_project(
        session: AsyncSession,
        project_id: int,
        user_id: int
) -> ProjectMember | None:
    member = await get_project_member(session, project_id, user_id)
    if not member:
        return None

    await session.delete(member)
    await session.commit()
    return member


async def check_user_in_project(
        session: AsyncSession,
        project_id: int,
        user_id: int
) -> bool:
    """Проверка, является ли пользователь участником проекта"""
    member = await get_project_member(session, project_id, user_id)
    return member is not None


async def get_project_owner(
        session: AsyncSession,
        project_id: int
) -> ProjectMember | None:
    """Получить владельца проекта"""
    result = await session.execute(
        select(ProjectMember)
        .where(
            and_(
                ProjectMember.project_id == project_id,
                ProjectMember.role == UserRole.PRODUCT_OWNER
            )
        )
    )
    return result.scalar_one_or_none()