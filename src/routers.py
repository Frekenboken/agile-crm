from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from uuid import UUID

from src.core.db import get_session
import src.crud as crud
from src.auth.security import get_current_user, require_organisation_minimum_role, require_project_minimum_role, \
    require_task_minimum_role
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
    TaskParticipantRead, TaskParticipantCreate, TaskParticipantUpdate,
    # Users
    UserUpdate, TaskCommentUpdate
)

router = APIRouter()


# ==============================================================================
# USERS (Управление пользователями)
# ==============================================================================


@router.get("/users/{user_id}", response_model=CurrentUserResponse, tags=["Users"])
async def get_user(
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    user = await crud.get_user(db, user_id)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get("/users", response_model=List[CurrentUserResponse], tags=["Users"])
async def list_users(
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    return await crud.get_all_users(db)


@router.patch("/users/{user_id}", response_model=CurrentUserResponse, tags=["Users"])
async def update_user(
        user_id: UUID,
        schema: UserUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only update your own profile")

    user = await crud.update_user(db, user_id, schema)
    if not user:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.delete("/users/{user_id}", status_code=204, tags=["Users"])
async def delete_user(
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    if current_user.id != user_id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own account")

    success = await crud.delete_user(db, user_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return None


# ==============================================================================
# ORGANISATIONS
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


@router.patch("/organisations/{organisation_id}", response_model=OrganisationRead, tags=["Organisations"])
async def update_organisation(
        organisation_id: UUID,
        schema: OrganisationUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.admin))
):
    org = await crud.update_organisation(db, organisation_id, schema)
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organisation not found")
    return org


@router.get("/organisations/{organisation_id}", response_model=OrganisationRead, tags=["Organisations"])
async def get_organisation(
        organisation_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    org = await crud.get_organisation(db, organisation_id)
    if not org:
        raise HTTPException(404, "Organisation not found")
    return org


@router.get("/organisations", response_model=List[OrganisationRead], tags=["Organisations"])
async def list_organisations(
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    return await crud.get_all_organisations(db)


@router.delete("/organisations/{organisation_id}", status_code=204, tags=["Organisations"])
async def delete_organisation(
        organisation_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.owner))
):
    success = await crud.delete_organisation(db, organisation_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organisation not found")
    return None


# ==============================================================================
# ORGANISATIONS MEMBERS
# ==============================================================================

@router.post("/organisations/{organisation_id}/members/{user_id}", response_model=OrganisationMemberRead,
             tags=["Organisations"])
async def add_organisation_member(
        organisation_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.admin))
):
    return await crud.add_user_to_organisation(
        db, OrganisationMemberCreate(organisation_id=organisation_id, user_id=user_id)
    )


@router.delete("/organisations/{organisation_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               tags=["Organisations"])
async def remove_organisation_member(
        organisation_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.owner))
):
    member = await crud.get_organisation_member_by_user_and_org(db, user_id, organisation_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    await crud.delete_organisation_member(db, member.id)
    return None


@router.get("/organisations/{organisation_id}/members/{user_id}", response_model=OrganisationMemberRead,
            tags=["Organisations"])
async def get_organisation_member(
        organisation_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.member))
):
    member = await crud.get_organisation_member_by_user_and_org(db, user_id, organisation_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return member


@router.get("/organisations/{organisation_id}/members", response_model=List[OrganisationMemberRead],
            tags=["Organisations"])
async def list_organisation_members(
        organisation_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.member))
):
    org = await crud.get_organisation(db, organisation_id)
    if not org:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Organisation not found")
    return await crud.get_organisation_members(db, organisation_id)


@router.patch("/organisations/{organisation_id}/members/{user_id}", response_model=OrganisationMemberRead,
              tags=["Organisations"])
async def update_organisation_member(
        organisation_id: UUID,
        user_id: UUID,
        schema: OrganisationMemberUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.admin))
):
    member = await crud.get_organisation_member_by_user_and_org(db, user_id, organisation_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return await crud.update_organisation_member(db, member.id, schema)


# ==============================================================================
# PROJECTS (Управление проектами и их командами)
# ==============================================================================

@router.post("/projects", response_model=ProjectRead, tags=["Projects"])
async def create_project(
        schema: ProjectCreate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.member))
):
    project = await crud.create_project(db, schema)
    # Создатель становится Product Owner-ом по умолчанию
    await crud.add_user_to_project(
        db, ProjectMemberCreate(project_id=project.id, user_id=current_user.id, role=ProjectRole.product_owner)
    )
    return project


@router.get("/projects/{project_id}", response_model=ProjectRead, tags=["Projects"])
async def get_project(
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.patch("/projects/{project_id}", response_model=ProjectRead, tags=["Projects"])
async def update_project(
        project_id: UUID,
        schema: ProjectUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.product_owner))
):
    project = await crud.update_project(db, project_id, schema)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.delete("/projects/{project_id}", status_code=204, tags=["Projects"])
async def delete_project(
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.product_owner))
):
    success = await crud.delete_project(db, project_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return None


@router.get("/projects", response_model=List[ProjectRead], tags=["Projects"])
async def list_projects_by_org(
        organisation_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_organisation_minimum_role(OrganisationRole.member))
):
    return await crud.get_projects_by_organisation(db, organisation_id)


# ==============================================================================
# PROJECT MEMBERS
# ==============================================================================

@router.post("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberRead, tags=["Projects"])
async def add_project_member(
        project_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.product_owner))
):
    return await crud.add_user_to_project(
        db, ProjectMemberCreate(project_id=project_id, user_id=user_id)
    )


@router.delete("/projects/{project_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Projects"])
async def remove_project_member(
        project_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.product_owner))
):
    member = await crud.get_project_member_by_user_and_project(db, user_id, project_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    await crud.remove_user_from_project(db, member.id)
    return None


@router.get("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberRead, tags=["Projects"])
async def get_project_member(
        project_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    member = await crud.get_project_member_by_user_and_project(db, user_id, project_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return member


@router.get("/projects/{project_id}/members", response_model=List[ProjectMemberRead], tags=["Projects"])
async def list_project_members(
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    project = await crud.get_project(db, project_id)
    if not project:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return await crud.get_project_members(db, project_id)


@router.patch("/projects/{project_id}/members/{user_id}", response_model=ProjectMemberRead, tags=["Projects"])
async def update_project_member(
        project_id: UUID,
        user_id: UUID,
        schema: ProjectMemberUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.product_owner))
):
    member = await crud.get_project_member_by_user_and_project(db, user_id, project_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return await crud.update_project_member(db, member.id, schema)


# ==============================================================================
# SPRINTS (Спринты)
# ==============================================================================

@router.post("/sprints", response_model=SprintRead, tags=["Sprints"])
async def create_sprint(
        schema: SprintCreate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    return await crud.create_sprint(db, schema)


@router.get("/sprints", response_model=List[SprintRead], tags=["Sprints"])
async def list_sprints(
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    return await crud.get_sprints_by_project(db, project_id)


@router.patch("/sprints/{sprint_id}", response_model=SprintRead, tags=["Sprints"])
async def update_sprint(
        sprint_id: UUID,
        schema: SprintUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    sprint = await crud.update_sprint(db, sprint_id, schema)
    if not sprint:
        raise HTTPException(404, "Sprint not found")
    return sprint


@router.get("/sprints/{sprint_id}", response_model=SprintRead, tags=["Sprints"])
async def get_sprint(
        sprint_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    sprint = await crud.get_sprint(db, sprint_id)
    if not sprint:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint


@router.delete("/sprints/{sprint_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Sprints"])
async def delete_sprint(
        sprint_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    success = await crud.delete_sprint(db, sprint_id)
    if not success:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprint not found")
    return None


@router.post("/project/{project_id}/sprints/{sprint_id}/start", response_model=SprintRead, tags=["Sprints"])
async def start_sprint(
        sprint_id: UUID,
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    try:
        sprint = await crud.start_sprint(db, sprint_id)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    if not sprint:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint


@router.post("/project/{project_id}/sprints/{sprint_id}/complete", response_model=SprintRead, tags=["Sprints"])
async def complete_sprint(
        sprint_id: UUID,
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    sprint = await crud.complete_sprint(db, sprint_id)
    if not sprint:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Sprint not found")
    return sprint


# ==============================================================================
# TASKS (Задачи и доска)
# ==============================================================================

@router.post("/projects/{project_id}/tasks", response_model=TaskRead, tags=["Tasks"])
async def create_task(
        project_id: UUID,
        schema: TaskCreate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    schema.reporter_id = current_user.id
    schema.project_id = project_id  # Переопределяем project_id из пути
    return await crud.create_task(db, schema)


@router.patch("/projects/{project_id}/tasks/{task_id}", response_model=TaskRead, tags=["Tasks"])
async def update_task(
        project_id: UUID,
        task_id: UUID,
        schema: TaskUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    try:
        task = await crud.update_task(db, task_id, schema)
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.get("/projects/{project_id}/tasks", response_model=List[TaskRead], tags=["Tasks"])
async def get_project_tasks(
        project_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    return await crud.get_tasks_by_project(db, project_id)


@router.get("/projects/{project_id}/tasks/{task_id}", response_model=TaskRead, tags=["Tasks"])
async def get_task(
        project_id: UUID,
        task_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return task


@router.delete("/projects/{project_id}/tasks/{task_id}", status_code=204, tags=["Tasks"])
async def delete_task(
        project_id: UUID,
        task_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    success = await crud.delete_task(db, task_id)
    if not success:
        raise HTTPException(404, "Task not found")
    return None


# ==============================================================================
# TASK COMPONENTS (Комментарии, Чек-листы, Участники)
# ==============================================================================

@router.post("/projects/{project_id}/tasks/{task_id}/comments", response_model=TaskCommentRead,
             tags=["Task Components"])
async def add_comment(
        project_id: UUID,
        task_id: UUID,
        content: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return await crud.create_comment(db, TaskCommentCreate(task_id=task_id, author_id=current_user.id, content=content))


@router.get("/projects/{project_id}/tasks/{task_id}/comments", response_model=List[TaskCommentRead],
            tags=["Task Components"])
async def list_comments(
        project_id: UUID,
        task_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return await crud.get_comments_by_task(db, task_id)


@router.get("/projects/{project_id}/tasks/{task_id}/comments/{comment_id}", response_model=TaskCommentRead,
            tags=["Task Components"])
async def get_comment(
        project_id: UUID,
        task_id: UUID,
        comment_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    comment = await crud.get_comment(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    return comment


@router.patch("/projects/{project_id}/tasks/{task_id}/comments/{comment_id}", response_model=TaskCommentRead,
              tags=["Task Components"])
async def update_comment(
        project_id: UUID,
        task_id: UUID,
        comment_id: UUID,
        schema: TaskCommentUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    comment = await crud.get_comment(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only edit your own comments")
    return await crud.update_comment(db, comment_id, schema)


@router.delete("/projects/{project_id}/tasks/{task_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT,
               tags=["Task Components"])
async def delete_comment(
        project_id: UUID,
        task_id: UUID,
        comment_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user)
):
    comment = await crud.get_comment(db, comment_id)
    if not comment or comment.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Comment not found")
    # Только автор или Scrum Master могут удалять комментарии
    if comment.author_id != current_user.id:
        # Проверяем, является ли пользователь Scrum Master
        task = await crud.get_task(db, task_id)
        member = await crud.get_project_member_by_user_and_project(db, current_user.id, task.project_id)
        if not member or member.role < ProjectRole.scrum_master:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You can only delete your own comments")
    await crud.delete_comment(db, comment_id)
    return None


# Чек-лист

@router.post("/projects/{project_id}/tasks/{task_id}/checklist", response_model=ChecklistItemRead,
             tags=["Task Components"])
async def add_checklist_item(
        project_id: UUID,
        task_id: UUID,
        content: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return await crud.create_checklist_item(
        db, ChecklistItemCreate(task_id=task_id, content=content, created_by=current_user.id)
    )


@router.get("/projects/{project_id}/tasks/{task_id}/checklist", response_model=List[ChecklistItemRead],
            tags=["Task Components"])
async def list_checklist(
        project_id: UUID,
        task_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return await crud.get_checklist_by_task(db, task_id)


@router.get("/projects/{project_id}/tasks/{task_id}/checklist/{item_id}", response_model=ChecklistItemRead,
            tags=["Task Components"])
async def get_checklist_item(
        project_id: UUID,
        task_id: UUID,
        item_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    item = await crud.get_checklist_item(db, item_id)
    if not item or item.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist item not found")
    return item


@router.patch("/projects/{project_id}/tasks/{task_id}/checklist/{item_id}", response_model=ChecklistItemRead,
              tags=["Task Components"])
async def update_checklist_item(
        project_id: UUID,
        task_id: UUID,
        item_id: UUID,
        content: str = Body(..., embed=True),
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    item = await crud.get_checklist_item(db, item_id)
    if not item or item.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist item not found")
    return await crud.update_checklist_item(db, item_id, content)


@router.patch("/projects/{project_id}/tasks/{task_id}/checklist/{item_id}/toggle", response_model=ChecklistItemRead,
              tags=["Task Components"])
async def toggle_checklist_item(
        project_id: UUID,
        task_id: UUID,
        item_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_task_minimum_role(ParticipantRole.worker))
):
    item = await crud.get_checklist_item(db, item_id)
    if not item or item.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist item not found")
    return await crud.toggle_checklist_item(db, item_id, current_user.id)


@router.delete("/projects/{project_id}/tasks/{task_id}/checklist/{item_id}", status_code=status.HTTP_204_NO_CONTENT,
               tags=["Task Components"])
async def delete_checklist_item(
        project_id: UUID,
        task_id: UUID,
        item_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    item = await crud.get_checklist_item(db, item_id)
    if not item or item.task_id != task_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Checklist item not found")
    await crud.delete_checklist_item(db, item_id)
    return None


# ==============================================================================
# TASK PARTICIPANTS (Участники задачи)
# ==============================================================================

@router.post("/projects/{project_id}/tasks/{task_id}/members/{user_id}", response_model=TaskParticipantRead,
             tags=["Tasks"])
async def add_task_member(
        project_id: UUID,
        task_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    return await crud.add_participant_to_task(
        db, TaskParticipantCreate(task_id=task_id, user_id=user_id)
    )


@router.delete("/projects/{project_id}/tasks/{task_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT,
               tags=["Tasks"])
async def remove_task_member(
        project_id: UUID,
        task_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    member = await crud.get_task_participant_by_user_and_task(db, user_id, task_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    await crud.remove_participant_from_task(db, member.id)
    return None


@router.get("/projects/{project_id}/tasks/{task_id}/members/{user_id}", response_model=TaskParticipantRead,
            tags=["Tasks"])
async def get_task_member(
        project_id: UUID,
        task_id: UUID,
        user_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    member = await crud.get_task_participant_by_user_and_task(db, user_id, task_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return member


@router.get("/projects/{project_id}/tasks/{task_id}/members", response_model=List[TaskParticipantRead], tags=["Tasks"])
async def list_task_members(
        project_id: UUID,
        task_id: UUID,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.developer))
):
    task = await crud.get_task(db, task_id)
    if not task:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Task not found")
    return await crud.get_task_participants(db, task_id)


@router.patch("/projects/{project_id}/tasks/{task_id}/members/{user_id}", response_model=TaskParticipantRead,
              tags=["Tasks"])
async def update_task_member(
        project_id: UUID,
        task_id: UUID,
        user_id: UUID,
        schema: TaskParticipantUpdate,
        db: AsyncSession = Depends(get_session),
        current_user: CurrentUserResponse = Depends(get_current_user),
        _: None = Depends(require_project_minimum_role(ProjectRole.scrum_master))
):
    member = await crud.get_task_participant_by_user_and_task(db, user_id, task_id)
    if not member:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Member not found")
    return await crud.update_task_participant(db, member.id, schema)
