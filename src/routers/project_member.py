from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.crud import project_member as pm_crud
from src.schemas.project_member import (
    ProjectMemberCreate,
    ProjectMemberRead,
    ProjectMemberUpdate
)
from src.models import UserRole

router = APIRouter(prefix="/project-members", tags=["project-members"])


@router.post("/", response_model=ProjectMemberRead)
async def add_member_to_project(
    member: ProjectMemberCreate,
    session: AsyncSession = Depends(get_session)
):
    db_member = await pm_crud.add_member_to_project(
        session,
        project_id=member.project_id,
        user_id=member.user_id,
        role=member.role
    )
    if db_member is None:
        raise HTTPException(400, "User is already a member of this project")
    return db_member


@router.get("/project/{project_id}/user/{user_id}", response_model=ProjectMemberRead)
async def get_project_member(
    project_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_member = await pm_crud.get_project_member(session, project_id, user_id)
    if db_member is None:
        raise HTTPException(404, "Member not found in this project")
    return db_member


@router.get("/user/{user_id}/projects", response_model=list[ProjectMemberRead])
async def get_user_projects(
    user_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    """Get all projects for a user"""
    memberships = await pm_crud.get_user_projects(
        session,
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    return memberships


@router.patch("/project/{project_id}/user/{user_id}", response_model=ProjectMemberRead)
async def update_member_role(
    project_id: int,
    user_id: int,
    updates: ProjectMemberUpdate,
    session: AsyncSession = Depends(get_session)
):
    db_member = await pm_crud.update_member_role(
        session,
        project_id,
        user_id,
        updates
    )
    if db_member is None:
        raise HTTPException(404, "Member not found in this project")
    return db_member


@router.delete("/project/{project_id}/user/{user_id}", response_model=ProjectMemberRead)
async def remove_member_from_project(
    project_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_member = await pm_crud.remove_member_from_project(session, project_id, user_id)
    if db_member is None:
        raise HTTPException(404, "Member not found in this project")
    return db_member


@router.get("/check/{project_id}/{user_id}")
async def check_user_in_project(
    project_id: int,
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Check if user is a member of project"""
    is_member = await pm_crud.check_user_in_project(session, project_id, user_id)
    return {"is_member": is_member}


@router.get("/project/{project_id}/owner", response_model=ProjectMemberRead)
async def get_project_owner(
    project_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get the owner (product owner) of a project"""
    owner = await pm_crud.get_project_owner(session, project_id)
    if owner is None:
        raise HTTPException(404, "Project owner not found")
    return owner