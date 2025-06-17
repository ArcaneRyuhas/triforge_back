from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from src.database.session import get_db
from src.database.schemas import user as user_schema
from src.database.schemas import project as project_schema
from src.database.schemas import message as message_schema
from src.database.schemas import jira_credential as jira_schema

from src.database.crud import user as user_crud
from src.database.crud import project as project_crud
from src.database.crud import message as message_crud
from src.database.crud import jira_credential as jira_crud

router = APIRouter(prefix="/db", tags=["Database"])

# --- USER ---
@router.post("/users/", response_model=user_schema.UserRead)
def create_user(user: user_schema.UserBase, db: Session = Depends(get_db)):
    db_user = user_crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return user_crud.create_user(db, **user.dict())

@router.get("/users/{user_id}", response_model=user_schema.UserRead)
def read_user(user_id: UUID, db: Session = Depends(get_db)):
    return user_crud.get_user(db, user_id)


# --- PROJECT ---
@router.post("/projects/", response_model=project_schema.ProjectRead)
def create_project(project: project_schema.ProjectCreate, db: Session = Depends(get_db)):
    return project_crud.create_project(db, title=project.title, user_id=project.user_id)

@router.get("/projects/user/{user_id}", response_model=list[project_schema.ProjectRead])
def get_projects_by_user(user_id: UUID, db: Session = Depends(get_db)):
    return project_crud.get_projects_by_user(db, user_id)


# --- MESSAGE ---
@router.post("/messages/", response_model=message_schema.MessageRead)
def create_message(message: message_schema.MessageCreate, db: Session = Depends(get_db)):
    return message_crud.create_message(db, message.text, message.project_id)

@router.get("/messages/project/{project_id}", response_model=list[message_schema.MessageRead])
def get_messages_for_project(project_id: UUID, db: Session = Depends(get_db)):
    return message_crud.get_messages_by_project(db, project_id)


# --- JIRA ---
@router.post("/jira/", response_model=jira_schema.JiraCredentialRead)
def create_jira_credential(jira: jira_schema.JiraCredentialCreate, db: Session = Depends(get_db)):
    return jira_crud.create_jira_credential(db, **jira.dict())

@router.get("/jira/user/{user_id}", response_model=list[jira_schema.JiraCredentialRead])
def get_jira_credentials(user_id: UUID, db: Session = Depends(get_db)):
    return jira_crud.get_jira_credentials_for_user(db, user_id)
