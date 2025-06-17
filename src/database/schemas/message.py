from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class MessageBase(BaseModel):
    text: str

class MessageCreate(MessageBase):
    project_id: UUID

class MessageRead(MessageBase):
    message_id: UUID
    project_id: UUID
    created_at: datetime

    class Config:
        orm_mode = True
