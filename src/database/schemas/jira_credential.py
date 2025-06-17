from pydantic import BaseModel, EmailStr
from uuid import UUID

class JiraCredentialBase(BaseModel):
    domain: str
    api_token: str
    email: EmailStr

class JiraCredentialCreate(JiraCredentialBase):
    user_id: UUID

class JiraCredentialRead(JiraCredentialBase):
    credential_id: UUID
    user_id: UUID

    class Config:
        orm_mode = True
