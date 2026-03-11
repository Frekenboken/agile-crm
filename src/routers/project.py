from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.crud import project as project_crud
from src.crud import project_member as pm_crud
from src.crud import task as task_crud
from src.crud import sprint as sprint_crud
from src.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from src.schemas.task import TaskRead
from src.schemas.sprint import SprintRead
from src.schemas.project_member import ProjectMemberRead

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=ProjectRead)
async def create_project(
        project: ProjectCreate,
        owner_id: int = Query(..., description="ID of the project owner"),
        session: AsyncSession = Depends(get_session)
):
    db_project = await project_crud.create_project(session, project, owner_id)
    if db_project is None:
        raise HTTPException(400, "Project with this key already exists")
    return db_project


@router.get("/{project_id}", response_model=ProjectRead)
async def read_project(
        project_id: int,
        session: AsyncSession = Depends(get_session)
):
    db_project = await project_crud.get_project(session, project_id)
    if db_project is None:
        raise HTTPException(404, "Project not found")
    return db_project


@router.get("/", response_model=list[ProjectRead])
async def read_projects(
        user_id: int | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session)
):
    projects = await project_crud.get_projects(
        session,
        user_id=user_id,
        skip=skip,
        limit=limit
    )
    return projects


@router.put("/{project_id}", response_model=ProjectRead)
async def update_project(
        project_id: int,
        updates: ProjectUpdate,
        session: AsyncSession = Depends(get_session)
):
    db_project = await project_crud.update_project(session, project_id, updates)
    if db_project is None:
        raise HTTPException(404, "Project not found")
    return db_project


@router.delete("/{project_id}", response_model=ProjectRead)
async def delete_project(
        project_id: int,
        session: AsyncSession = Depends(get_session)
):
    db_project = await project_crud.delete_project(session, project_id)
    if db_project is None:
        raise HTTPException(404, "Project not found")
    return db_project


@router.get("/{project_id}/details", response_model=dict)
async def get_project_details(
        project_id: int,
        session: AsyncSession = Depends(get_session)
):
    """Get project with all related data (sprints, tasks, members)"""
    project = await project_crud.get_project_with_details(session, project_id)
    if project is None:
        raise HTTPException(404, "Project not found")

    return {
        "project": project,
        "sprints": project.sprints,
        "tasks": project.tasks,
        "members": project.members
    }


@router.get("/{project_id}/tasks", response_model=list[TaskRead])
async def get_project_tasks(
        project_id: int,
        status: str | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session)
):
    """Get all tasks for a project"""
    tasks = await task_crud.get_tasks(
        session,
        project_id=project_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return tasks


@router.get("/{project_id}/sprints", response_model=list[SprintRead])
async def get_project_sprints(
        project_id: int,
        is_active: bool | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session)
):
    """Get all sprints for a project"""
    sprints = await sprint_crud.get_sprints(
        session,
        project_id=project_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return sprints


@router.get("/{project_id}/members", response_model=list[ProjectMemberRead])
async def get_project_members(
        project_id: int,
        role: str | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session)
):
    """Get all members of a project"""
    members = await pm_crud.get_project_members(
        session,
        project_id=project_id,
        role=role,
        skip=skip,
        limit=limit
    )
    return members