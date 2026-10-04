from pydantic import BaseModel
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: str | None = None

class UserCreate(UserBase):
    github_id: int
    github_token: str

class UserUpdate(BaseModel):
    email: str | None = None

class User(UserBase):
    id: int
    github_id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes: True
