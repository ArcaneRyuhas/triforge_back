from pydantic import BaseModel, Field
from typing import Optional, Literal
from uuid import uuid4

class UnifiedRequest(BaseModel):
    user_id: Optional[str] = Field(default_factory=lambda: str(uuid4()))
    message: str = Field(..., min_length=1, description="User's message or request")
    # Optional hints if frontend wants to force a specific intent
    intent_hint: Optional[Literal["conversation", "documentation", "diagram", "code"]] = None

class IntentDetectionResult(BaseModel):
    intent: Literal["conversation", "documentation", "diagram", "code", "modify_documentation", "modify_diagram", "modify_code"]
    confidence: float
    extracted_params: dict  # Intent-specific parameters