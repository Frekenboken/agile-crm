from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.models import UserRole


class ProjectMemberBase(BaseModel):
    project_id: int
    user_id: int
    role: UserRole = UserRole.DEVELOPER


class ProjectMemberCreate(ProjectMemberBase):
    pass


class ProjectMemberRead(ProjectMemberBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    joined_date: datetime


class ProjectMemberUpdate(BaseModel):
    role: UserRole | None = None