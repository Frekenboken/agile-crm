from datetime import timedelta
from uuid import UUID
from fastapi import HTTPException, status, Depends, Path, Header, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from authx import AuthX, AuthXConfig, TokenPayload

from src.core.config import settings
from src.core.db import get_session
import src.crud as crud  # Импортируем весь crud файл
from src.auth.schemas import CurrentUserResponse

from src.models import UserRole, OrganisationRole, ProjectRole, ParticipantRole

config = AuthXConfig()
config.JWT_SECRET_KEY = settings.SECRET_KEY
config.JWT_ACCESS_CSRF_COOKIE_NAME = "access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_COOKIE_CSRF_PROTECT = False
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

security = AuthX(config=config)


async def get_current_user(
        payload: TokenPayload = Depends(security.access_token_required),
        session: AsyncSession = Depends(get_session)
):
    # В payload.sub (или uid) у нас лежит UUID в виде строки
    user_id = payload.sub

    user = await crud.get_user(session, user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or session expired"
        )

    return CurrentUserResponse(
        id=user.id,
        email=user.email,
    )


# Вспомогательная функция для поиска ID в разных частях запроса
async def get_id_from_request(request: Request, param_name: str) -> UUID:
    value = None

    # 1. Поиск в Path
    value = request.path_params.get(param_name)

    # 2. Поиск в Query
    if value is None:
        value = request.query_params.get(param_name)

    # 3. Поиск в Body (JSON)
    if value is None:
        try:
            # .json() кэшируется в FastAPI, так что это безопасно
            body = await request.json()
            if isinstance(body, dict):
                value = body.get(param_name)
        except Exception:
            pass

    if value is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Parameter '{param_name}' is required (path, query, or body)"
        )

    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid UUID format for {param_name}"
        )


def require_organisation_minimum_role(allowed_role: OrganisationRole):
    async def role_checker(
            request: Request,
            db: AsyncSession = Depends(get_session),
            current_user: CurrentUserResponse = Depends(get_current_user)
    ) -> CurrentUserResponse:
        organisation_id = await get_id_from_request(request, "organisation_id")

        organisation_member = await crud.get_organisation_member_by_user_and_org(db, current_user.id, organisation_id)

        if not organisation_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not a member of the organisation."
            )

        if organisation_member.role < allowed_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_role}. Your role: {organisation_member.role}"
            )

        return current_user

    return role_checker


def require_project_minimum_role(allowed_role: ProjectRole):
    async def role_checker(
            request: Request,
            db: AsyncSession = Depends(get_session),
            current_user: CurrentUserResponse = Depends(get_current_user)
    ) -> CurrentUserResponse:
        project_id = await get_id_from_request(request, "project_id")

        project_member = await crud.get_project_member_by_user_and_project(db, current_user.id, project_id)

        if not project_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not a member of the project."
            )

        if project_member.role < allowed_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_role}. Your role: {project_member.role}"
            )

        return current_user

    return role_checker


def require_task_minimum_role(allowed_role: ParticipantRole):
    async def role_checker(
            request: Request,
            db: AsyncSession = Depends(get_session),
            current_user: CurrentUserResponse = Depends(get_current_user)
    ) -> CurrentUserResponse:
        task_id = await get_id_from_request(request, "task_id")

        task_role = await crud.get_task_participant_by_user_and_project(db, current_user.id, task_id)

        if not task_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied. You are not a participant of the task."
            )

        if task_role.role < allowed_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required role: {allowed_role}. Your role: {task_role.role}"
            )

        return current_user

    return role_checker