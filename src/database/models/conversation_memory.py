from sqlalchemy import Column, String, Text, Integer, DateTime, JSON
from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Index, func
from src.database.base import Base

class ConversationMemoryModel(Base):
    """Database model for storing project-scoped conversation memory"""
    __tablename__ = "conversation_memories"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)
    project_id = Column(String(36), nullable=False, index=True)
    
    # Memory content
    summary = Column(Text, nullable=True)  # Conversation summary from ConversationSummaryBufferMemory
    recent_messages = Column(JSON, nullable=True)  # Recent messages as JSON
    token_count = Column(Integer, default=0)  # Token count for memory management
    
    # Metadata
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Composite index for efficient queries
    __table_args__ = (
        Index('ix_user_project', 'user_id', 'project_id'),
    )