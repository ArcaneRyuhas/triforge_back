from pydantic import BaseModel, Field
from typing import Optional
from uuid import uuid4

class BaseRequest(BaseModel):
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))

class Message(BaseRequest):
    content: str = Field(..., min_length=1)
    agent_type: Optional[str] = Field(default="general", pattern="^(general|documentation|diagram|code)$")
    diagram_format: Optional[str] = None
    programming_language: Optional[str] = None

class DocumentationRequest(BaseRequest):
    requirement: str = Field(..., min_length=1)
    document_format: str = Field(default="Jira Stories")
    agent_type: Optional[str] = Field(default="documentation")

class ModifyJiraStoriesRequest(BaseRequest):
    modification_prompt: str = Field(..., min_length=1)
    original_stories: Optional[str] = None
    agent_type: Optional[str] = Field(default="documentation")

class DiagramGenerationRequest(BaseRequest):
    diagram_format: str = Field(default="Mermaid.js")
    jira_stories: Optional[str] = None
    diagram_type: Optional[str] = Field(..., description="Type of diagram (flowchart, sequence, class, etc.)")
    agent_type: Optional[str] = Field(default="diagram")

class ModifyDiagramRequest(BaseRequest):
    modification_prompt: str = Field(..., min_length=1)
    original_diagram_code: Optional[str] = None
    agent_type: Optional[str] = Field(default="diagram")

class CodeGenerationRequest(BaseRequest):
    programming_language: str = Field(default="Python")
    diagram_code: Optional[str] = None
    jira_stories: Optional[str] = None
    agent_type: Optional[str] = Field(default="code")

class ModifyCodeRequest(BaseRequest):
    modification_prompt: str = Field(..., min_length=1)
    original_code: Optional[str] = None
    agent_type: Optional[str] = Field(default="code")
    
class JiraUploadRequest(BaseRequest):
    """Request to upload Jira stories to Atlassian"""
    email: str = Field(..., description="Jira account email")
    api_token: str = Field(..., description="Jira API token")
    domain: str = Field(..., description="Atlassian domain (e.g., mycompany.atlassian.net)")
    project_key: str = Field(..., description="Jira project key (e.g., PROJ, DEV)")
    stories_markdown: Optional[str] = Field(None, description="Markdown stories to upload (if not provided, will get from memory)")

class JiraValidateRequest(BaseRequest):
    """Request to validate Jira connection and project"""
    email: str = Field(..., description="Jira account email")
    api_token: str = Field(..., description="Jira API token") 
    domain: str = Field(..., description="Atlassian domain")
    project_key: Optional[str] = Field(None, description="Project key to validate (optional)")