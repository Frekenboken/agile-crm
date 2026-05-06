import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Integer, Boolean, DateTime, Date,
    ForeignKey, Enum, UniqueConstraint, Index, func
)
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import UUID  # Для SQLite будет работать как тип через расширение

class Base(AsyncAttrs, DeclarativeBase):
    pass


# --- ENUMS ---

class TaskType(enum.Enum):
    epic = "epic"
    story = "story"
    task = "task"
    bug = "bug"


class TaskStatus(enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class TaskPriority(enum.Enum):
    highest = "highest"
    high = "high"
    medium = "medium"
    low = "low"
    lowest = "lowest"

# Роли
class OrganisationRole(enum.Enum):
    owner = "owner"
    admin = "admin"
    member = "member"


class ProjectRole(enum.Enum):
    scrum_master = "scrum_master"
    product_owner = "product_owner"
    developer = "developer"

class ParticipantRole(enum.Enum):
    worker = "worker"
    reviewer = "reviewer"
    tester = "tester"

# --- ТАБЛИЦЫ ---

class Organisation(Base):
    __tablename__ = 'organisation'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class User(Base):
    __tablename__ = 'user'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True)
    hashed_password = Column(String(255))
    first_name = Column(String(255), nullable=False)
    last_name = Column(String(255), nullable=False)
    avatar_url = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Project(Base):
    __tablename__ = 'project'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organisation_id = Column(String(36), ForeignKey('organisation.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('organisation_id', 'name', name='uq_project_org_name'),
    )


class OrganisationMember(Base):
    __tablename__ = 'organisation_member'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organisation_id = Column(String(36), ForeignKey('organisation.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(36), ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum(OrganisationRole), nullable=False, default=OrganisationRole.member)
    joined_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('organisation_id', 'user_id', name='uq_org_member'),
    )


class ProjectMember(Base):
    __tablename__ = 'project_member'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(36), ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    role = Column(Enum(ProjectRole), nullable=False, default=ProjectRole.developer)
    joined_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('project_id', 'user_id', name='uq_project_member'),
    )


class Sprint(Base):
    __tablename__ = 'sprint'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    name = Column(String(255), nullable=False)
    goal = Column(Text)
    start_date = Column(Date)
    end_date = Column(Date)
    is_active = Column(Boolean, nullable=False, default=False)
    is_completed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_sprint_active', 'project_id', 'is_active'),
    )


class Task(Base):
    __tablename__ = 'task'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String(36), ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    sprint_id = Column(String(36), ForeignKey('sprint.id', ondelete='SET NULL'))
    parent_task_id = Column(String(36), ForeignKey('task.id', ondelete='CASCADE'))

    type = Column(Enum(TaskType), nullable=False, default=TaskType.task)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    external_url = Column(Text)

    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.todo)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.medium)
    story_points = Column(Integer)
    order_index = Column(Integer, nullable=False, default=0)

    reporter_id = Column(String(36), ForeignKey('user.id', ondelete='SET NULL'))

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_task_project', 'project_id'),
        Index('idx_task_sprint', 'sprint_id'),
        Index('idx_task_parent', 'parent_task_id'),
        Index('idx_task_reporter', 'reporter_id'),
        Index('idx_task_ordering', 'project_id', 'sprint_id', 'order_index'),
    )


class TaskComment(Base):
    __tablename__ = 'task_comment'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(String(36), ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index('idx_comment_task', 'task_id'),
    )


class ChecklistItem(Base):
    __tablename__ = 'checklist_item'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    content = Column(String(500), nullable=False)
    is_completed = Column(Boolean, nullable=False, default=False)
    completed_by = Column(String(36), ForeignKey('user.id', ondelete='SET NULL'))
    completed_at = Column(DateTime)
    created_by = Column(String(36), ForeignKey('user.id', ondelete='SET NULL'))
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index('idx_checklist_task', 'task_id'),
    )


class TaskParticipant(Base):
    __tablename__ = 'task_participant'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(String(36), ForeignKey('user.id'), nullable=False)
    role = Column(Enum(ParticipantRole), nullable=False, default=ParticipantRole.worker)
    joined_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint('task_id', 'user_id', name='uq_task_participant'),
        Index('idx_participant_user', 'user_id'),
    )