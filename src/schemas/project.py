from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class ProjectBase(BaseModel):
    name: str
    key: str
    description: str | None = None


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ProjectUpdate(BaseModel):
    name: str | None = None
    key: str | None = None
    description: str | None = None