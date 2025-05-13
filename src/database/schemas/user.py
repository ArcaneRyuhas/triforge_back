from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    username: str
    email: EmailStr
    full_name: str | None = None

class UserCreate(UserBase):
    password: str           

class UserRead(UserBase):
    id: int

    class Config:
        orm_mode = True
