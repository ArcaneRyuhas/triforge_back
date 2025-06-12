from pydantic import BaseModel
from typing import List, Dict, Optional, Any  

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
    
    # Add these new models to src/models/responses.py

class ProjectFile(BaseModel):
    """Represents a file in a generated project"""
    path: str
    content: str
    language: str

class ProjectCodeResponse(BaseModel):
    """Response for project code generation"""
    user_id: str
    project_id: str
    technologies: List[str]
    files: List[ProjectFile]
    project_structure: Dict[str, Any]
    readme_content: str
    message: str

class ProjectStructureResponse(BaseModel):
    """Response for project structure"""
    user_id: str
    project_id: str
    structure: Dict[str, Any]
    total_files: int

class DownloadResponse(BaseModel):
    """Response for download request"""
    user_id: str
    project_id: str
    download_url: str
    filename: str
    size_bytes: int