from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.database.base import Base

class JiraCredential(Base):
    __tablename__ = "jira_credentials"

    credential_id = Column(UUID(as_uuid=True), primary_key=True, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"), nullable=False)
    domain = Column(String(255), nullable=False)
    api_token = Column(String(255), nullable=False) # TODO: No debe ser texto plano, pero con OAuth no importa
    email = Column(String(255), nullable=False)

    user = relationship("User", back_populates="jira_credentials")
