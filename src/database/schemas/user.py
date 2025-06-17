from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    user_id: UUID
    password: str           

class UserRead(UserBase):
    user_id: UUID

    class Config:
        orm_mode = True
