from uuid import UUID
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.auth.hashing import get_password_hash

# Импорт моделей и схем (поправь пути под свою структуру проекта)
from src.models import (
    Organisation, User, Project, OrganisationMember, ProjectMember,
    Sprint, Task, TaskComment, ChecklistItem, TaskParticipant, TaskStatus
)
from src.schemas import (
    OrganisationCreate, OrganisationUpdate,
    UserCreate, UserUpdate,
    ProjectCreate, ProjectUpdate,
    OrganisationMemberCreate, OrganisationMemberUpdate,
    ProjectMemberCreate, ProjectMemberUpdate,
    SprintCreate, SprintUpdate,
    TaskCreate, TaskUpdate,
    TaskCommentCreate,
    ChecklistItemCreate,
    TaskParticipantCreate, TaskParticipantUpdate, TaskCommentUpdate
)


# ==============================================================================
# 1. USER CRUD
# ==============================================================================

async def get_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == str(user_id)))
    return result.scalars().first()


async def get_all_users(db: AsyncSession) -> List[User]:
    result = await db.execute(select(User))
    return list(result.scalars().all())


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()


async def create_user(db: AsyncSession, schema: UserCreate) -> User:
    db_obj = User(
        email=schema.email,
        first_name=schema.first_name,
        last_name=schema.last_name,
        avatar_url=schema.avatar_url,
        hashed_password=get_password_hash(schema.password)
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_user(db: AsyncSession, user_id: UUID, schema: UserUpdate) -> Optional[User]:
    db_obj = await get_user(db, user_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_user(db: AsyncSession, user_id: UUID) -> bool:
    db_obj = await get_user(db, user_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 2. ORGANISATION CRUD
# ==============================================================================

async def get_organisation(db: AsyncSession, organisation_id: UUID) -> Optional[Organisation]:
    result = await db.execute(select(Organisation).where(Organisation.id == str(organisation_id)))
    return result.scalars().first()


async def get_all_organisations(db: AsyncSession) -> List[Organisation]:
    result = await db.execute(select(Organisation))
    return result.scalars().all()


async def create_organisation(db: AsyncSession, schema: OrganisationCreate) -> Organisation:
    db_obj = Organisation(name=schema.name)
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_organisation(db: AsyncSession, organisation_id: UUID, schema: OrganisationUpdate) -> Optional[
    Organisation]:
    db_obj = await get_organisation(db, organisation_id)
    if not db_obj:
        return None
    db_obj.name = schema.name
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_organisation(db: AsyncSession, organisation_id: UUID) -> bool:
    db_obj = await get_organisation(db, organisation_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 3. ORGANISATION MEMBER CRUD
# ==============================================================================

async def get_organisation_member_by_user_and_org(
        db: AsyncSession,
        user_id: UUID,
        organisation_id: UUID
) -> Optional[OrganisationMember]:
    result = await db.execute(
        select(OrganisationMember).where(
            OrganisationMember.user_id == str(user_id),
            OrganisationMember.organisation_id == str(organisation_id)
        )
    )
    return result.scalars().first()


async def get_organisation_member(db: AsyncSession, member_id: UUID) -> Optional[OrganisationMember]:
    result = await db.execute(select(OrganisationMember).where(OrganisationMember.id == str(member_id)))
    return result.scalars().first()


async def get_organisation_members(db: AsyncSession, organisation_id: UUID) -> List[OrganisationMember]:
    result = await db.execute(
        select(OrganisationMember).where(OrganisationMember.organisation_id == str(organisation_id)))
    return list(result.scalars().all())


async def add_user_to_organisation(db: AsyncSession, schema: OrganisationMemberCreate) -> OrganisationMember:
    db_obj = OrganisationMember(
        organisation_id=str(schema.organisation_id),
        user_id=str(schema.user_id),
        role=schema.role
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_organisation_member(db: AsyncSession, member_id: UUID, schema: OrganisationMemberUpdate) -> Optional[
    OrganisationMember]:
    db_obj = await get_organisation_member(db, member_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_organisation_member(db: AsyncSession, member_id: UUID) -> bool:
    db_obj = await get_organisation_member(db, member_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 4. PROJECT CRUD
# ==============================================================================

async def get_project(db: AsyncSession, project_id: UUID) -> Optional[Project]:
    result = await db.execute(select(Project).where(Project.id == str(project_id)))
    return result.scalars().first()


async def get_projects_by_organisation(db: AsyncSession, organisation_id: UUID) -> List[Project]:
    result = await db.execute(select(Project).where(Project.organisation_id == str(organisation_id)))
    return list(result.scalars().all())


async def create_project(db: AsyncSession, schema: ProjectCreate) -> Project:
    db_obj = Project(
        organisation_id=str(schema.organisation_id),
        name=schema.name,
        description=schema.description
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_project(db: AsyncSession, project_id: UUID, schema: ProjectUpdate) -> Optional[Project]:
    db_obj = await get_project(db, project_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_project(db: AsyncSession, project_id: UUID) -> bool:
    db_obj = await get_project(db, project_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 5. PROJECT MEMBER CRUD
# ==============================================================================

async def get_project_member_by_user_and_project(
        db: AsyncSession,
        user_id: UUID,
        project_id: UUID
) -> Optional[ProjectMember]:
    result = await db.execute(
        select(ProjectMember).where(
            ProjectMember.user_id == str(user_id),
            ProjectMember.project_id == str(project_id)
        )
    )
    return result.scalars().first()


async def get_project_member(db: AsyncSession, member_id: UUID) -> Optional[ProjectMember]:
    result = await db.execute(select(ProjectMember).where(ProjectMember.id == str(member_id)))
    return result.scalars().first()


async def get_project_members(db: AsyncSession, project_id: UUID) -> List[ProjectMember]:
    result = await db.execute(select(ProjectMember).where(ProjectMember.project_id == str(project_id)))
    return list(result.scalars().all())


async def add_user_to_project(db: AsyncSession, schema: ProjectMemberCreate) -> ProjectMember:
    db_obj = ProjectMember(
        project_id=str(schema.project_id),
        user_id=str(schema.user_id),
        role=schema.role
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_project_member(db: AsyncSession, member_id: UUID, schema: ProjectMemberUpdate) -> Optional[
    ProjectMember]:
    db_obj = await get_project_member(db, member_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def remove_user_from_project(db: AsyncSession, member_id: UUID) -> bool:
    db_obj = await get_project_member(db, member_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 6. SPRINT CRUD
# ==============================================================================

async def get_sprint(db: AsyncSession, sprint_id: UUID) -> Optional[Sprint]:
    result = await db.execute(select(Sprint).where(Sprint.id == str(sprint_id)))
    return result.scalars().first()


async def get_sprints_by_project(db: AsyncSession, project_id: UUID) -> List[Sprint]:
    result = await db.execute(select(Sprint).where(Sprint.project_id == str(project_id)))
    return list(result.scalars().all())


async def create_sprint(db: AsyncSession, schema: SprintCreate) -> Sprint:
    db_obj = Sprint(
        project_id=str(schema.project_id),
        name=schema.name,
        goal=schema.goal,
        start_date=schema.start_date,
        end_date=schema.end_date,
        is_active=schema.is_active,
        is_completed=schema.is_completed
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def update_sprint(db: AsyncSession, sprint_id: UUID, schema: SprintUpdate) -> Optional[Sprint]:
    db_obj = await get_sprint(db, sprint_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_sprint(db: AsyncSession, sprint_id: UUID) -> bool:
    db_obj = await get_sprint(db, sprint_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


async def start_sprint(db: AsyncSession, sprint_id: UUID) -> Optional[Sprint]:
    db_obj = await get_sprint(db, sprint_id)
    if not db_obj:
        return None

    result = await db.execute(
        select(Sprint).where(
            Sprint.project_id == db_obj.project_id,
            Sprint.is_active == True,
            Sprint.id != sprint_id
        )
    )
    active_sprint = result.scalars().first()
    if active_sprint:
        raise ValueError(
            f"Project already has an active sprint: '{active_sprint.name}'. "
            f"Complete it before starting a new one."
        )

    db_obj.is_active = True
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def complete_sprint(db: AsyncSession, sprint_id: UUID) -> Optional[Sprint]:
    db_obj = await get_sprint(db, sprint_id)
    if not db_obj:
        return None

    db_obj.is_active = False
    db_obj.is_completed = True

    # Отвязываем все задачи от спринта
    result = await db.execute(
        select(Task).where(Task.sprint_id == str(sprint_id))
    )
    tasks = result.scalars().all()
    for task in tasks:
        task.sprint_id = None

    await db.commit()
    await db.refresh(db_obj)
    return db_obj

# ==============================================================================
# 7. TASK CRUD
# ==============================================================================

async def get_task(db: AsyncSession, task_id: UUID) -> Optional[Task]:
    result = await db.execute(select(Task).where(Task.id == str(task_id)))
    return result.scalars().first()


async def get_tasks_by_project(db: AsyncSession, project_id: UUID) -> List[Task]:
    result = await db.execute(select(Task).where(Task.project_id == str(project_id)))
    return list(result.scalars().all())


async def get_tasks_by_sprint(db: AsyncSession, sprint_id: UUID) -> List[Task]:
    result = await db.execute(select(Task).where(Task.sprint_id == str(sprint_id)))
    return list(result.scalars().all())


async def create_task(db: AsyncSession, schema: TaskCreate) -> Task:
    db_obj = Task(
        project_id=str(schema.project_id),
        sprint_id=str(schema.sprint_id) if schema.sprint_id else None,
        parent_task_id=str(schema.parent_task_id) if schema.parent_task_id else None,
        reporter_id=str(schema.reporter_id) if schema.reporter_id else None,
        title=schema.title,
        description=schema.description,
        external_url=schema.external_url,
        type=schema.type,
        status=schema.status,
        priority=schema.priority,
        story_points=schema.story_points,
        order_index=schema.order_index
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


# В crud.py, перед функциями

ALLOWED_STATUS_TRANSITIONS = {
    TaskStatus.todo: [TaskStatus.in_progress],
    TaskStatus.in_progress: [TaskStatus.review, TaskStatus.todo],
    TaskStatus.review: [TaskStatus.testing, TaskStatus.in_progress],
    TaskStatus.testing: [TaskStatus.done, TaskStatus.in_progress],
    TaskStatus.done: [],  # из done нельзя перейти никуда
}


async def update_task(db: AsyncSession, task_id: UUID, schema: TaskUpdate) -> Optional[Task]:
    db_obj = await get_task(db, task_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)

    # Проверка перехода статуса
    if 'status' in update_data:
        new_status = update_data['status']
        allowed = ALLOWED_STATUS_TRANSITIONS.get(db_obj.status, [])
        if new_status not in allowed:
            raise ValueError(
                f"Transition from '{db_obj.status.value}' to '{new_status.value}' is not allowed"
            )

    for key, value in update_data.items():
        if key in ['sprint_id', 'parent_task_id'] and value is not None:
            setattr(db_obj, key, str(value))
        else:
            setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_task(db: AsyncSession, task_id: UUID) -> bool:
    db_obj = await get_task(db, task_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 8. TASK COMMENT CRUD
# ==============================================================================

async def get_comment(db: AsyncSession, comment_id: UUID) -> Optional[TaskComment]:
    result = await db.execute(select(TaskComment).where(TaskComment.id == str(comment_id)))
    return result.scalars().first()


async def get_comments_by_task(db: AsyncSession, task_id: UUID) -> List[TaskComment]:
    result = await db.execute(select(TaskComment).where(TaskComment.task_id == str(task_id)))
    return list(result.scalars().all())


async def create_comment(db: AsyncSession, schema: TaskCommentCreate) -> TaskComment:
    db_obj = TaskComment(
        task_id=str(schema.task_id),
        author_id=str(schema.author_id),
        content=schema.content
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_comment(db: AsyncSession, comment_id: UUID) -> bool:
    db_obj = await get_comment(db, comment_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


async def update_comment(db: AsyncSession, comment_id: UUID, schema: TaskCommentUpdate) -> Optional[TaskComment]:
    db_obj = await get_comment(db, comment_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


# ==============================================================================
# 9. CHECKLIST ITEM CRUD
# ==============================================================================

async def get_checklist_item(db: AsyncSession, item_id: UUID) -> Optional[ChecklistItem]:
    result = await db.execute(select(ChecklistItem).where(ChecklistItem.id == str(item_id)))
    return result.scalars().first()


async def get_checklist_by_task(db: AsyncSession, task_id: UUID) -> List[ChecklistItem]:
    result = await db.execute(select(ChecklistItem).where(ChecklistItem.task_id == str(task_id)))
    return list(result.scalars().all())


async def create_checklist_item(db: AsyncSession, schema: ChecklistItemCreate) -> ChecklistItem:
    db_obj = ChecklistItem(
        task_id=str(schema.task_id),
        content=schema.content,
        is_completed=schema.is_completed,
        created_by=str(schema.created_by) if schema.created_by else None
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def toggle_checklist_item(db: AsyncSession, item_id: UUID, completed_by_user_id: UUID) -> Optional[ChecklistItem]:
    """Специальный метод для отметки пункта чек-листа выполненным/невыполненным"""
    db_obj = await get_checklist_item(db, item_id)
    if not db_obj:
        return None

    db_obj.is_completed = not db_obj.is_completed
    if db_obj.is_completed:
        db_obj.completed_by = str(completed_by_user_id)
        db_obj.completed_at = datetime.now()
    else:
        db_obj.completed_by = None
        db_obj.completed_at = None

    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def delete_checklist_item(db: AsyncSession, item_id: UUID) -> bool:
    db_obj = await get_checklist_item(db, item_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


# ==============================================================================
# 10. TASK PARTICIPANT CRUD
# ==============================================================================

async def get_task_participant_by_user_and_task(
        db: AsyncSession,
        user_id: UUID,
        task_id: UUID
) -> Optional[TaskParticipant]:
    result = await db.execute(
        select(TaskParticipant).where(
            TaskParticipant.user_id == str(user_id),
            TaskParticipant.task_id == str(task_id)
        )
    )
    return result.scalars().first()


async def get_participant(db: AsyncSession, participant_id: UUID) -> Optional[TaskParticipant]:
    result = await db.execute(select(TaskParticipant).where(TaskParticipant.id == str(participant_id)))
    return result.scalars().first()


async def get_task_participants(db: AsyncSession, task_id: UUID) -> List[TaskParticipant]:
    result = await db.execute(select(TaskParticipant).where(TaskParticipant.task_id == str(task_id)))
    return list(result.scalars().all())


async def add_participant_to_task(db: AsyncSession, schema: TaskParticipantCreate) -> TaskParticipant:
    db_obj = TaskParticipant(
        task_id=str(schema.task_id),
        user_id=str(schema.user_id),
        role=schema.role
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj


async def remove_participant_from_task(db: AsyncSession, participant_id: UUID) -> bool:
    db_obj = await get_participant(db, participant_id)
    if not db_obj:
        return False
    await db.delete(db_obj)
    await db.commit()
    return True


async def update_task_participant(db: AsyncSession, participant_id: UUID, schema: TaskParticipantUpdate) -> Optional[
    TaskParticipant]:
    db_obj = await get_participant(db, participant_id)
    if not db_obj:
        return None

    update_data = schema.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_obj, key, value)

    await db.commit()
    await db.refresh(db_obj)
    return db_obj
