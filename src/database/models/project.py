from sqlalchemy import Column, String, Text, Boolean, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from src.database.base import Base

class ProjectModel(Base):
    """Database model for projects"""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(String(36), nullable=False, index=True)
    
    # Project metadata
    settings = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_activity = Column(DateTime, default=func.now())
    
    # Relationships
    # conversations = relationship("ConversationMemoryModel", backref="project")