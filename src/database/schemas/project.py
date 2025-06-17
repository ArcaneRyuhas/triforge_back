from pydantic import BaseModel
from uuid import UUID

class ProjectBase(BaseModel):
    title: str

class ProjectCreate(ProjectBase):
    user_id: UUID

class ProjectRead(ProjectBase):
    project_id: UUID
    user_id: UUID

    class Config:
        orm_mode = True
