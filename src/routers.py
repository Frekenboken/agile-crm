from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from src.core.db import get_session
import src.crud as crud
from src.auth.security import get_current_user
from src.auth.schemas import CurrentUserResponse
from src.models import OrganisationRole, ProjectRole, ParticipantRole
from src.schemas import (
    # Organisations
    OrganisationRead, OrganisationCreate, OrganisationUpdate,
    OrganisationMemberRead, OrganisationMemberCreate, OrganisationMemberUpdate,
    # Projects
    ProjectRead, ProjectCreate, ProjectUpdate,
    ProjectMemberRead, ProjectMemberCreate, ProjectMemberUpdate,
    # Sprints
    SprintRead, SprintCreate, SprintUpdate,
    # Tasks
    TaskRead, TaskCreate, TaskUpdate,
    # Task Components
    TaskCommentRead, TaskCommentCreate,
    ChecklistItemRead, ChecklistItemCreate,
    TaskParticipantRead, TaskParticipantCreate
)

router = APIRouter()

# ==============================================================================
# ORGANISATIONS (Управление организациями и их членами)
# ==============================================================================

@router.post("/organisations", response_model=OrganisationRead, tags=["Organisations"])
async def create_organisation(
    schema: OrganisationCreate,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    org = await crud.create_organisation(db, schema)
    # Создатель автоматически становится владельцем
    await crud.add_user_to_organisation(
        db,
        OrganisationMemberCreate(organisation_id=org.id, user_id=current_user.id, role=OrganisationRole.owner)
    )
    return org

@router.get("/organisations/{org_id}", response_model=OrganisationRead, tags=["Organisations"])
async def get_organisation(org_id: UUID, db: AsyncSession = Depends(get_session)):
    org = await crud.get_organisation(db, org_id)
    if not org: raise HTTPException(404, "Organisation not found")
    return org

@router.post("/organisations/{org_id}/members", response_model=OrganisationMemberRead, tags=["Organisations"])
async def add_organisation_member(
    org_id: UUID,
    user_id: UUID,
    role: OrganisationRole = OrganisationRole.member,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    return await crud.add_user_to_organisation(
        db, OrganisationMemberCreate(organisation_id=org_id, user_id=user_id, role=role)
    )

@router.get("/organisations/{org_id}/members", response_model=List[OrganisationMemberRead], tags=["Organisations"])
async def list_organisation_members(org_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_org_members(db, org_id)


# ==============================================================================
# PROJECTS (Управление проектами и их командами)
# ==============================================================================

@router.post("/projects", response_model=ProjectRead, tags=["Projects"])
async def create_project(
    schema: ProjectCreate,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    project = await crud.create_project(db, schema)
    # Создатель становится Scrum Master-ом по умолчанию
    await crud.add_user_to_project(
        db, ProjectMemberCreate(project_id=project.id, user_id=current_user.id, role=ProjectRole.scrum_master)
    )
    return project

@router.get("/projects/organisation/{org_id}", response_model=List[ProjectRead], tags=["Projects"])
async def list_projects_by_org(org_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_projects_by_organisation(db, org_id)

@router.post("/projects/{project_id}/members", response_model=ProjectMemberRead, tags=["Projects"])
async def add_project_member(
    project_id: UUID,
    user_id: UUID,
    role: ProjectRole = ProjectRole.developer,
    db: AsyncSession = Depends(get_session)
):
    return await crud.add_user_to_project(
        db, ProjectMemberCreate(project_id=project_id, user_id=user_id, role=role)
    )


# ==============================================================================
# SPRINTS (Спринты)
# ==============================================================================

@router.post("/sprints", response_model=SprintRead, tags=["Sprints"])
async def create_sprint(schema: SprintCreate, db: AsyncSession = Depends(get_session)):
    return await crud.create_sprint(db, schema)

@router.get("/projects/{project_id}/sprints", response_model=List[SprintRead], tags=["Sprints"])
async def list_sprints(project_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_sprints_by_project(db, project_id)

@router.patch("/sprints/{sprint_id}", response_model=SprintRead, tags=["Sprints"])
async def update_sprint(sprint_id: UUID, schema: SprintUpdate, db: AsyncSession = Depends(get_session)):
    sprint = await crud.update_sprint(db, sprint_id, schema)
    if not sprint: raise HTTPException(404, "Sprint not found")
    return sprint


# ==============================================================================
# TASKS (Задачи и доска)
# ==============================================================================

@router.post("/tasks", response_model=TaskRead, tags=["Tasks"])
async def create_task(
    schema: TaskCreate,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    schema.reporter_id = current_user.id
    return await crud.create_task(db, schema)

@router.patch("/tasks/{task_id}", response_model=TaskRead, tags=["Tasks"])
async def update_task(task_id: UUID, schema: TaskUpdate, db: AsyncSession = Depends(get_session)):
    task = await crud.update_task(db, task_id, schema)
    if not task: raise HTTPException(404, "Task not found")
    return task

@router.get("/projects/{project_id}/tasks", response_model=List[TaskRead], tags=["Tasks"])
async def get_project_tasks(project_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_tasks_by_project(db, project_id)


# ==============================================================================
# TASK COMPONENTS (Комментарии, Чек-листы, Участники)
# ==============================================================================

# Комментарии
@router.post("/tasks/{task_id}/comments", response_model=TaskCommentRead, tags=["Task Components"])
async def add_comment(
    task_id: UUID,
    content: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    return await crud.create_comment(db, TaskCommentCreate(task_id=task_id, author_id=current_user.id, content=content))

@router.get("/tasks/{task_id}/comments", response_model=List[TaskCommentRead], tags=["Task Components"])
async def list_comments(task_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_comments_by_task(db, task_id)

# Чек-лист
@router.post("/tasks/{task_id}/checklist", response_model=ChecklistItemRead, tags=["Task Components"])
async def add_checklist_item(
    task_id: UUID,
    content: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    return await crud.create_checklist_item(
        db, ChecklistItemCreate(task_id=task_id, content=content, created_by=current_user.id)
    )

@router.patch("/checklist/{item_id}/toggle", response_model=ChecklistItemRead, tags=["Task Components"])
async def toggle_checklist(
    item_id: UUID,
    db: AsyncSession = Depends(get_session),
    current_user: CurrentUserResponse = Depends(get_current_user)
):
    item = await crud.toggle_checklist_item(db, item_id, current_user.id)
    if not item: raise HTTPException(404, "Item not found")
    return item

# Участники (Participants)
@router.post("/tasks/{task_id}/participants", response_model=TaskParticipantRead, tags=["Task Components"])
async def add_task_participant(
    task_id: UUID,
    user_id: UUID,
    role: ParticipantRole = ParticipantRole.worker,
    db: AsyncSession = Depends(get_session)
):
    return await crud.add_participant_to_task(db, TaskParticipantCreate(task_id=task_id, user_id=user_id, role=role))

@router.get("/tasks/{task_id}/participants", response_model=List[TaskParticipantRead], tags=["Task Components"])
async def list_task_participants(task_id: UUID, db: AsyncSession = Depends(get_session)):
    return await crud.get_task_participants(db, task_id)

@router.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"])
async def delete_task(task_id: UUID, db: AsyncSession = Depends(get_session)):
    success = await crud.delete_task(db, task_id)
    if not success: raise HTTPException(404, "Task not found")
    return None