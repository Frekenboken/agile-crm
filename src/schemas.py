from datetime import datetime, date
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr

# Импортируем твои Enum из файла моделей
from src.models import (
    TaskType, TaskStatus, TaskPriority,
    OrganisationRole, ProjectRole, ParticipantRole
)

# --- USER ---

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    avatar_url: Optional[str] = None

class UserCreate(UserBase):
    password: str # Принимаем "чистый" пароль для хэширования

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    avatar_url: Optional[str] = None


# --- ORGANISATION ---

class OrganisationBase(BaseModel):
    name: str

class OrganisationCreate(OrganisationBase):
    pass

class OrganisationRead(OrganisationBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    created_at: datetime

class OrganisationUpdate(OrganisationBase):
    pass


# --- ORGANISATION MEMBER ---

class OrganisationMemberBase(BaseModel):
    role: OrganisationRole = OrganisationRole.member

class OrganisationMemberCreate(OrganisationMemberBase):
    organisation_id: UUID
    user_id: UUID

class OrganisationMemberRead(OrganisationMemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organisation_id: UUID
    user_id: UUID
    joined_at: datetime

class OrganisationMemberUpdate(BaseModel):
    role: OrganisationRole


# --- PROJECT ---

class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectCreate(ProjectBase):
    organisation_id: UUID

class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    organisation_id: UUID
    created_at: datetime

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# --- PROJECT MEMBER ---

class ProjectMemberBase(BaseModel):
    role: ProjectRole = ProjectRole.developer

class ProjectMemberCreate(ProjectMemberBase):
    project_id: UUID
    user_id: UUID

class ProjectMemberRead(ProjectMemberBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    user_id: UUID
    joined_at: datetime

class ProjectMemberUpdate(BaseModel):
    role: ProjectRole


# --- SPRINT ---

class SprintBase(BaseModel):
    name: str
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: bool = False
    is_completed: bool = False

class SprintCreate(SprintBase):
    project_id: UUID

class SprintRead(SprintBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    created_at: datetime

class SprintUpdate(BaseModel):
    name: Optional[str] = None
    goal: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_active: Optional[bool] = None
    is_completed: Optional[bool] = None


# --- TASK ---

class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    external_url: Optional[str] = None
    type: TaskType = TaskType.task
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    story_points: Optional[int] = None
    order_index: int = 0

class TaskCreate(TaskBase):
    project_id: UUID
    sprint_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    reporter_id: Optional[UUID] = None

class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    project_id: UUID
    sprint_id: Optional[UUID] = None
    parent_task_id: Optional[UUID] = None
    reporter_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    external_url: Optional[str] = None
    type: Optional[TaskType] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    story_points: Optional[int] = None
    order_index: Optional[int] = None
    sprint_id: Optional[UUID] = None


# --- TASK COMMENT ---

class TaskCommentBase(BaseModel):
    content: str

class TaskCommentCreate(TaskCommentBase):
    task_id: UUID
    author_id: UUID

class TaskCommentRead(TaskCommentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    author_id: UUID
    created_at: datetime
    updated_at: datetime

class TaskCommentUpdate(TaskCommentBase):
    pass


# --- CHECKLIST ITEM ---

class ChecklistItemBase(BaseModel):
    content: str
    is_completed: bool = False

class ChecklistItemCreate(ChecklistItemBase):
    task_id: UUID
    created_by: Optional[UUID] = None

class ChecklistItemRead(ChecklistItemBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    completed_by: Optional[UUID] = None
    completed_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime


# --- TASK PARTICIPANT ---

class TaskParticipantBase(BaseModel):
    role: ParticipantRole = ParticipantRole.worker

class TaskParticipantCreate(TaskParticipantBase):
    task_id: UUID
    user_id: UUID

class TaskParticipantRead(TaskParticipantBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    task_id: UUID
    user_id: UUID
    joined_at: datetime

class TaskParticipantUpdate(TaskParticipantBase):
    role: ParticipantRole