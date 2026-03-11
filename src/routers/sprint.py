from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.core.db import get_session
from src.crud import sprint as sprint_crud
from src.crud import task as task_crud
from src.schemas.sprint import SprintCreate, SprintRead, SprintUpdate
from src.schemas.task import TaskRead

router = APIRouter(prefix="/sprints", tags=["sprints"])


@router.post("/", response_model=SprintRead)
async def create_sprint(
        sprint: SprintCreate,
        session: AsyncSession = Depends(get_session)
):
    return await sprint_crud.create_sprint(session, sprint)


@router.get("/{sprint_id}", response_model=SprintRead)
async def read_sprint(
        sprint_id: int,
        session: AsyncSession = Depends(get_session)
):
    db_sprint = await sprint_crud.get_sprint(session, sprint_id)
    if db_sprint is None:
        raise HTTPException(404, "Sprint not found")
    return db_sprint


@router.get("/", response_model=list[SprintRead])
async def read_sprints(
        project_id: int | None = Query(None),
        is_active: bool | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session)
):
    sprints = await sprint_crud.get_sprints(
        session,
        project_id=project_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )
    return sprints


@router.put("/{sprint_id}", response_model=SprintRead)
async def update_sprint(
        sprint_id: int,
        updates: SprintUpdate,
        session: AsyncSession = Depends(get_session)
):
    db_sprint = await sprint_crud.update_sprint(session, sprint_id, updates)
    if db_sprint is None:
        raise HTTPException(404, "Sprint not found")
    return db_sprint


@router.delete("/{sprint_id}", response_model=SprintRead)
async def delete_sprint(
        sprint_id: int,
        session: AsyncSession = Depends(get_session)
):
    db_sprint = await sprint_crud.delete_sprint(session, sprint_id)
    if db_sprint is None:
        raise HTTPException(404, "Sprint not found")
    return db_sprint


@router.post("/{sprint_id}/start", response_model=SprintRead)
async def start_sprint(
        sprint_id: int,
        start_date: datetime = Query(...),
        end_date: datetime = Query(...),
        session: AsyncSession = Depends(get_session)
):
    """Start a sprint with given dates"""
    if start_date >= end_date:
        raise HTTPException(400, "Start date must be before end date")

    db_sprint = await sprint_crud.start_sprint(session, sprint_id, start_date, end_date)
    if db_sprint is None:
        raise HTTPException(404, "Sprint not found")
    return db_sprint


@router.post("/{sprint_id}/complete", response_model=SprintRead)
async def complete_sprint(
        sprint_id: int,
        session: AsyncSession = Depends(get_session)
):
    """Complete a sprint"""
    db_sprint = await sprint_crud.complete_sprint(session, sprint_id)
    if db_sprint is None:
        raise HTTPException(404, "Sprint not found")
    return db_sprint


@router.get("/{sprint_id}/tasks", response_model=list[TaskRead])
async def get_sprint_tasks(
        sprint_id: int,
        status: str | None = Query(None),
        skip: int = Query(0, ge=0),
        limit: int = Query(100, ge=1, le=1000),
        session: AsyncSession = Depends(get_session)
):
    """Get all tasks in a sprint"""
    tasks = await task_crud.get_tasks(
        session,
        sprint_id=sprint_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return tasks


@router.get("/{sprint_id}/stats", response_model=dict)
async def get_sprint_stats(
        sprint_id: int,
        session: AsyncSession = Depends(get_session)
):
    """Get statistics for a sprint"""
    sprint = await sprint_crud.get_sprint(session, sprint_id)
    if sprint is None:
        raise HTTPException(404, "Sprint not found")

    tasks = await task_crud.get_tasks(session, sprint_id=sprint_id)

    total_tasks = len(tasks)
    completed_tasks = sum(1 for t in tasks if t.status == "done")
    in_progress_tasks = sum(1 for t in tasks if t.status == "in_progress")

    return {
        "sprint_id": sprint_id,
        "sprint_name": sprint.name,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completion_percentage": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }