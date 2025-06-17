from sqlalchemy.orm import Session
from src.database.models.project import Project
from uuid import uuid4

def create_project(db: Session, title: str, user_id):
    project = Project(project_id=uuid4(), title=title, user_id=user_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

def get_projects_by_user(db: Session, user_id):
    return db.query(Project).filter(Project.user_id == user_id).all()
