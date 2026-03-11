from pydantic import BaseModel, ConfigDict
from datetime import datetime
from src.models import TaskStatus


class TaskBase(BaseModel):
    name: str
    description: str | None = None
    status: TaskStatus = TaskStatus.BACKLOG
    level: int = 0
    project_id: int
    sprint_id: int | None = None


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_date: datetime


class TaskUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    status: TaskStatus | None = None
    level: int | None = None
    project_id: int | None = None
    sprint_id: int | None = None