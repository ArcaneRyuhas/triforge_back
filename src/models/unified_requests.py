from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import uuid4

class UnifiedRequest(BaseModel):
    """Basic unified request without project context"""
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    message: str = Field(..., min_length=1, description="User's message or request")
    intent_hint: Optional[Literal["conversation", "documentation", "diagram", "code", "requirements"]] = None

class ProjectUnifiedRequest(BaseModel):
    """Unified request with project context for scoped memory"""
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    message: str = Field(..., min_length=1, description="User's message or request")
    project_id: Optional[str] = Field(None, description="Project ID for scoped memory. Uses 'default' if not provided")
    intent_hint: Optional[Literal["conversation", "documentation", "diagram", "code", "requirements"]] = None

class IntentDetectionResult(BaseModel):
    """Enhanced intent detection result with more intents"""
    intent: Literal[
        "conversation", 
        "documentation", 
        "diagram", 
        "code", 
        "requirements",
        "modify_documentation", 
        "modify_diagram", 
        "modify_code"
    ]
    confidence: float
    extracted_params: dict
    reasoning: Optional[str] = None  # Why this intent was chosen