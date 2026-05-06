from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
import src.crud as crud
from src.auth.hashing import verify_password  # Убедись, что этот файл есть
from src.auth.security import security, get_current_user
from src.core.config import settings
from src.schemas import UserCreate
from src.auth.schemas import LoginResponse, UserResponse, CurrentUserResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
        credentials: LoginRequest,
        response: Response,
        session: AsyncSession = Depends(get_session)
):
    user = await crud.get_user_by_email(session, credentials.email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Создаем токен, передавая id пользователя (UUID)
    access_token = security.create_access_token(uid=str(user.id))

    response.set_cookie(
        key=security.config.JWT_ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,  # Смени на True в продакшене (HTTPS)
        samesite="lax"
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=user.id,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            avatar_url=user.avatar_url
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@router.post("/register", response_model=LoginResponse)
async def register(
        form: UserCreate,
        response: Response,
        session: AsyncSession = Depends(get_session)
):
    user_exist = await crud.get_user_by_email(session, form.email)
    if user_exist:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = await crud.create_user(session, form)

    access_token = security.create_access_token(uid=str(new_user.id))

    response.set_cookie(
        key=security.config.JWT_ACCESS_COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax"
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            first_name=new_user.first_name,
            last_name=new_user.last_name,
            avatar_url=new_user.avatar_url
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
        current_user: CurrentUserResponse = Depends(get_current_user),
        session: AsyncSession = Depends(get_session)
):
    # Находим пользователя в базе данных (current_user.id уже UUID)
    user = await crud.get_user(session, current_user.id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        avatar_url=user.avatar_url
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=security.config.JWT_ACCESS_COOKIE_NAME,
        httponly=True,
        samesite="lax"
    )
    return {"detail": "Logged out"}