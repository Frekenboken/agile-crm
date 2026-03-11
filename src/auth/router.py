from fastapi import APIRouter, Depends, HTTPException, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from src.core.db import get_session
from src.crud import user as user_crud

from src.auth.hashing import verify_password

from authx import TokenPayload
from src.auth.security import security, get_current_user

from src.core.config import settings
from src.schemas.user import UserCreate
from src.auth.schemas import LoginResponse, UserResponse, CurrentUserResponse


class UserLogin(BaseModel):
    email: str
    password: str


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(
        credentials: UserLogin,
        response: Response,
        session: AsyncSession = Depends(get_session)
):
    user = await user_crud.get_user_by_email(session, credentials.email)
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password")
    access_token = security.create_access_token(uid=str(user.id))
    # response.set_cookie(security.config.JWT_ACCESS_COOKIE_NAME, access_token)
    response.set_cookie(key=security.config.JWT_ACCESS_COOKIE_NAME, value=access_token, httponly=True, secure=False,
                        samesite="lax")

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            email=user.email,
            role=user.role
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@router.post("/register", response_model=LoginResponse)
async def register(
        form: UserCreate,
        response: Response,
        session: AsyncSession = Depends(get_session)
):
    user_exist = await user_crud.get_user_by_email(session, form.email)
    if user_exist:
        raise HTTPException(401, "Username or email already registered"
                            )
    new_user = await user_crud.create_user(session, form)
    access_token = security.create_access_token(uid=str(new_user.id))
    response.set_cookie(key=security.config.JWT_ACCESS_COOKIE_NAME, value=access_token, httponly=True, secure=False,
                        samesite="lax")
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse(
            email=new_user.email,
        ),
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(current_user: CurrentUserResponse = Depends(get_current_user),
                                   session: AsyncSession = Depends(get_session)):
    user_id = int(current_user.id)

    # Находим пользователя в базе данных
    user = await user_crud.get_user(session, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        email=user.email,
    )


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie(
        key=security.config.JWT_ACCESS_COOKIE_NAME,
        httponly=True,
        samesite="lax"
    )
    return {"detail": "Logged out"}
