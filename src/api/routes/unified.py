from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from src.models.unified_requests import UnifiedRequest
from src.models.responses import ConversationResponse, JiraStoriesResponse, ProjectCodeResponse
from src.services.intent_detection_service import intent_detection_service
from src.services.chain_factory import chain_factory
from src.services.memory_service import memory_service
from src.api.auth_dependencies import get_current_user
from src.core.exceptions import AIServiceException
from src.utils.logger import logging
import json

# Import existing request models to reuse
from src.models.requests import (
    DocumentationRequest, DiagramGenerationRequest,
    ProjectCodeGenerationRequest, ModifyJiraStoriesRequest,
    ModifyDiagramRequest
)

# Import existing route handlers
from src.api.routes.documentation import generate_jira_stories, modify_jira_stories
from src.api.routes.diagram import generate_diagram, modify_diagram
from src.api.routes.code import generate_project_code
from src.api.routes.conversation import handle_conversation

router = APIRouter(prefix="/chat", tags=["unified"])
logger = logging.getLogger(__name__)

@router.post("/", response_model=ConversationResponse)
async def unified_chat_endpoint(request: UnifiedRequest, current_user: Dict[str, Any] = Depends(get_current_user)):
    """
    Unified endpoint that detects intent and routes to appropriate handler
    """
    try:
        # Detect intent
        intent_result = await intent_detection_service.detect_intent(
            request.user_id,
            request.message,
            request.intent_hint
        )
        
        logger.info(f"Detected intent: {intent_result.intent} with confidence: {intent_result.confidence}")
        
        # Route based on intent
        if intent_result.intent == "documentation":
            # Convert to DocumentationRequest
            doc_request = DocumentationRequest(
                user_id=request.user_id,
                requirement=request.message
            )
            jira_response = await generate_jira_stories(doc_request)
            
            # Convert JiraStoriesResponse to ConversationResponse
            if jira_response.is_valid:
                return ConversationResponse(
                    user_id=request.user_id,
                    response=jira_response.jira_stories
                )
            else:
                # Handle validation errors
                return ConversationResponse(
                    user_id=request.user_id,
                    response=jira_response.jira_stories  # This contains the error message
                )
            
        elif intent_result.intent == "modify_documentation":
            modify_request = ModifyJiraStoriesRequest(
                user_id=request.user_id,
                modification_prompt=request.message
            )
            return await modify_jira_stories(modify_request)
            
        elif intent_result.intent == "diagram":
            # Extract diagram type from params or message
            diagram_type = intent_result.extracted_params.get("diagram_type", "flowchart")
            
            diagram_request = DiagramGenerationRequest(
                user_id=request.user_id,
                diagram_type=diagram_type
            )
            return await generate_diagram(diagram_request)
            
        elif intent_result.intent == "modify_diagram":
            modify_request = ModifyDiagramRequest(
                user_id=request.user_id,
                modification_prompt=request.message
            )
            return await modify_diagram(modify_request)
            
        elif intent_result.intent == "code":
            code_request = ProjectCodeGenerationRequest(
                user_id=request.user_id,
                prompt=request.message
            )
            code_response = await generate_project_code(code_request)
            
            # Convert ProjectCodeResponse to ConversationResponse
            response_text = f"""Successfully generated project!

**Project ID:** {code_response.project_id}
**Technologies:** {', '.join(code_response.technologies)}
**Files Generated:** {len(code_response.files)}

{code_response.message}

You can download the project using the project ID: {code_response.project_id}
"""
            return ConversationResponse(
                user_id=request.user_id,
                response=response_text
            )
            
        elif intent_result.intent == "conversation":
            # Default conversation handling
            chain = chain_factory.create_conversation_chain(request.user_id)
            response = chain.predict(input=request.message)
            
            return ConversationResponse(
                user_id=request.user_id,
                response=response
            )
        
        else:
            # Handle uncertain intent
            if intent_result.confidence < 0.5:
                clarification = (
                    "I'm not sure what you'd like me to help with. "
                    "You can ask me to:\n"
                    "- Generate Jira stories from requirements\n"
                    "- Create diagrams (flowchart, sequence, etc.)\n"
                    "- Build complete project code\n"
                    "- Modify any existing content\n\n"
                    "What would you like to do?"
                )
                return ConversationResponse(
                    user_id=request.user_id,
                    response=clarification
                )
            else:
                # Handle unrecognized but confident intent
                return ConversationResponse(
                    user_id=request.user_id,
                    response=f"I detected the intent '{intent_result.intent}' but I'm not sure how to handle it. Please try rephrasing your request."
                )
            
    except Exception as e:
        logger.error(f"Error in unified endpoint: {str(e)}")
        raise AIServiceException(f"Error processing request: {str(e)}")