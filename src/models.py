from sqlalchemy import Column, Integer, Float, String, ForeignKey, Boolean, Enum as SQLEnum, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs

from datetime import datetime, UTC

from enum import Enum


class Base(AsyncAttrs, DeclarativeBase):
    pass


class UserRole(str, Enum):
    USER = 'user'
    PRODUCT_OWNER = 'product_owner'
    DEVELOPER = 'developer'
    SCRUM_MASTER = 'scrum_master'


class TaskStatus(str, Enum):
    BACKLOG = 'backlog'
    SPRINT = 'sprint'
    IN_PROGRESS = 'in_progress'
    DONE = 'done'


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)

    project_memberships = relationship("ProjectMember", back_populates="user", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String, unique=True, nullable=False)  # Ключ задачи (например, "PROJ-123")
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.BACKLOG)

    # Связи
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    project = relationship("Project", back_populates="tasks")

    sprint_id = Column(Integer, ForeignKey("sprints.id", ondelete="SET NULL"), nullable=True)
    sprint = relationship("Sprint", back_populates="tasks")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    key = Column(String, unique=True, nullable=False)
    description = Column(Text, nullable=True)

    # Связи
    sprints = relationship("Sprint", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    members = relationship("ProjectMember", back_populates="project", cascade="all, delete-orphan")

class Sprint(Base):
    __tablename__ = "sprints"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    goal = Column(Text, nullable=True)  # Цель спринта
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=False)
    created_date = Column(DateTime, default=lambda: datetime.now(UTC))

    # Связи
    project = relationship("Project", back_populates="sprints")
    tasks = relationship("Task", back_populates="sprint")


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.DEVELOPER)
    joined_date = Column(DateTime, default=lambda: datetime.now(UTC))

    # Связи
    project = relationship("Project", back_populates="members")
    user = relationship("User", back_populates="project_memberships")