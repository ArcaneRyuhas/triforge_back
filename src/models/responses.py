from pydantic import BaseModel

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