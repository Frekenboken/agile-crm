from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.crud import task as task_crud
from src.schemas.task import TaskCreate, TaskRead, TaskUpdate
from src.models import TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskRead)
async def create_task(
    task: TaskCreate,
    session: AsyncSession = Depends(get_session)
):
    return await task_crud.create_task(session, task)


@router.get("/{task_id}", response_model=TaskRead)
async def read_task(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_task = await task_crud.get_task(session, task_id)
    if db_task is None:
        raise HTTPException(404, "Task not found")
    return db_task


@router.get("/", response_model=list[TaskRead])
async def read_tasks(
    project_id: int | None = Query(None),
    sprint_id: int | None = Query(None),
    status: TaskStatus | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session)
):
    tasks = await task_crud.get_tasks(
        session,
        project_id=project_id,
        sprint_id=sprint_id,
        status=status,
        skip=skip,
        limit=limit
    )
    return tasks


@router.put("/{task_id}", response_model=TaskRead)
async def update_task(
    task_id: int,
    updates: TaskUpdate,
    session: AsyncSession = Depends(get_session)
):
    db_task = await task_crud.update_task(session, task_id, updates)
    if db_task is None:
        raise HTTPException(404, "Task not found")
    return db_task


@router.delete("/{task_id}", response_model=TaskRead)
async def delete_task(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_task = await task_crud.delete_task(session, task_id)
    if db_task is None:
        raise HTTPException(404, "Task not found")
    return db_task


@router.patch("/{task_id}/move-to-sprint/{sprint_id}", response_model=TaskRead)
async def move_task_to_sprint(
    task_id: int,
    sprint_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_task = await task_crud.move_task_to_sprint(session, task_id, sprint_id)
    if db_task is None:
        raise HTTPException(404, "Task not found")
    return db_task


@router.patch("/{task_id}/move-to-backlog", response_model=TaskRead)
async def move_task_to_backlog(
    task_id: int,
    session: AsyncSession = Depends(get_session)
):
    db_task = await task_crud.move_task_to_sprint(session, task_id, None)
    if db_task is None:
        raise HTTPException(404, "Task not found")
    return db_task