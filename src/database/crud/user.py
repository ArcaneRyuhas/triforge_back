from sqlalchemy.orm import Session
from database.models.user import User

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def create_user(db: Session, username: str, email: str, full_name: str = None):
    db_user = User(username=username, email=email, full_name=full_name)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
