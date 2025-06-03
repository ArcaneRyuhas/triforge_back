from pydantic import BaseModel
from typing import List, Dict, Optional  

class ConversationResponse(BaseModel):
    user_id: str
    response: str

class JiraStoriesResponse(BaseModel):
    user_id: str
    jira_stories: str
    is_valid: bool

class HealthResponse(BaseModel):
    status: str
    message: str
    version: str
    
class JiraValidationResponse(BaseModel):
    """Response for Jira validation"""
    user_id: str
    is_valid: bool
    message: str
    project_validated: Optional[bool] = None

class JiraUploadResponse(BaseModel):
    """Response for Jira upload operation"""
    user_id: str
    success: bool
    message: str
    created_issues: List[Dict[str, str]]
    failed_issues: List[Dict[str, str]]
    total_stories: int
    successful_uploads: int