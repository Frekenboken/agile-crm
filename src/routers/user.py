from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.crud import user as user_crud
from src.schemas.user import UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, include_in_schema=False)
async def create_user(
    user: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    db_user = await user_crud.create_user(session, user)
    if db_user is None:
        raise HTTPException(400, "User with this email already exists")
    return db_user


@router.get("/{user_id}", response_model=UserRead)
async def read_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_user = await user_crud.get_user(session, user_id)
    if db_user is None:
        raise HTTPException(404, "User not found")
    return db_user


@router.get("/", response_model=list[UserRead])
async def read_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    db_users = await user_crud.get_users(session, skip=skip, limit=limit)
    return db_users


@router.delete("/{user_id}", response_model=UserRead)
async def delete_user(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_user = await user_crud.delete_user(session, user_id)
    if db_user is None:
        raise HTTPException(404, "User not found")
    return db_user


@router.put("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    updates: UserUpdate,
    session: AsyncSession = Depends(get_session)
):
    db_user = await user_crud.update_user(session, user_id, updates)
    if db_user is None:
        raise HTTPException(404, "User not found")
    return db_user


@router.get("/by-email/{email}", response_model=UserRead)
async def get_user_by_email(
    email: str,
    session: AsyncSession = Depends(get_session)
):
    db_user = await user_crud.get_user_by_email(session, email)
    if db_user is None:
        raise HTTPException(404, "User not found")
    return db_user