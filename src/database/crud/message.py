from sqlalchemy.orm import Session
from src.database.models.message import Message
from uuid import uuid4
from datetime import datetime

def create_message(db: Session, text: str, project_id):
    message = Message(
        message_id=uuid4(),
        text=text,
        project_id=project_id,
        created_at=datetime.utcnow()
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_messages_by_project(db: Session, project_id):
    return db.query(Message).filter(Message.project_id == project_id).order_by(Message.created_at).all()
