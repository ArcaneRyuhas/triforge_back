from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import uuid4

class Project(BaseModel):
    """Project model with memory and artifact relationships"""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    user_id: str = Field(...)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)
    
    # Project settings
    settings: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ProjectCreateRequest(BaseModel):
    """Request to create a new project"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(default_factory=list)
    settings: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ProjectUpdateRequest(BaseModel):
    """Request to update an existing project"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class ProjectResponse(BaseModel):
    """Response containing project information"""
    id: str
    name: str
    description: Optional[str]
    user_id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    tags: List[str]
    settings: Dict[str, Any]
    
    # Additional statistics
    conversation_count: Optional[int] = 0
    last_activity: Optional[datetime] = None

class ProjectListResponse(BaseModel):
    """Response for listing projects"""
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int