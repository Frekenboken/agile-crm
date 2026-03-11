from datetime import timedelta

from src.auth.schemas import CurrentUserResponse
from src.core.config import settings

from authx import AuthX, AuthXConfig, TokenPayload
from authx.exceptions import MissingTokenError

from fastapi import HTTPException, status, Depends

from src.core.db import get_session
from src.crud import user as user_crud

from sqlalchemy.ext.asyncio import AsyncSession

config = AuthXConfig()
config.JWT_SECRET_KEY = settings.SECRET_KEY
config.JWT_ACCESS_CSRF_COOKIE_NAME = "access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]
config.JWT_COOKIE_CSRF_PROTECT = False
config.JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

security = AuthX(config=config)


# async def access_token_required():
#     try:
#         return security.access_token_required
#     except MissingTokenError:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Authentication required"
#         )


async def get_current_user(payload: TokenPayload = Depends(security.access_token_required),
                           session: AsyncSession = Depends(get_session)):
    user_id = int(payload.sub)

    # Находим пользователя в базе данных
    user = await user_crud.get_user(session, user_id)

    # if not user:
    #     raise HTTPException(status_code=404, detail="User not found")

    return CurrentUserResponse(
        id=user.id,
        email=user.email,
    )
