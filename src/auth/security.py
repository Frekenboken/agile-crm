from datetime import timedelta
from uuid import UUID
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from authx import AuthX, AuthXConfig, TokenPayload

from src.core.config import settings
from src.core.db import get_session
import src.crud as crud # Импортируем весь crud файл
from src.auth.schemas import CurrentUserResponse

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