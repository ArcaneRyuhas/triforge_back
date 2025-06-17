from sqlalchemy.orm import Session
from src.database.models.jira_credential import JiraCredential
from uuid import uuid4

def create_jira_credential(db: Session, domain: str, api_token: str, email: str, user_id):
    credential = JiraCredential(
        credential_id=uuid4(),
        domain=domain,
        api_token=api_token,
        email=email,
        user_id=user_id
    )
    db.add(credential)
    db.commit()
    db.refresh(credential)
    return credential

def get_jira_credentials_for_user(db: Session, user_id):
    return db.query(JiraCredential).filter(JiraCredential.user_id == user_id).all()
