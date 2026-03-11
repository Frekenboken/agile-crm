from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class SprintBase(BaseModel):
    name: str
    goal: str | None = None
    project_id: int
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool = False


class SprintCreate(SprintBase):
    pass


class SprintRead(SprintBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_date: datetime


class SprintUpdate(BaseModel):
    name: str | None = None
    goal: str | None = None
    project_id: int | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None