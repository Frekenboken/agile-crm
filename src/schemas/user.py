from pydantic import BaseModel, ConfigDict

from src.models import UserRole


class UserBase(BaseModel):
    email: str


class UserCreate(UserBase):
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole


class UserUpdate(UserBase):
    email: str | None = None
    # password: str | None = None
    role: UserRole | None = None
