from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from src.models.unified_requests import UnifiedRequest, ProjectUnifiedRequest
from src.models.responses import ConversationResponse
from src.api.auth_dependencies import get_current_user
from src.services.intent_detection_service import intent_detection_service
from src.ai_services.conversation_service import ConversationService
from src.ai_services.documentation_service import DocumentationService
from src.ai_services.diagram_service import DiagramService
from src.ai_services.requirements_service import RequirementsService
from src.ai_services.code_service import CodeService
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging

router = APIRouter(prefix="/chat", tags=["unified"])
logger = logging.getLogger(__name__)

# Initialize AI services
conversation_service = ConversationService()
documentation_service = DocumentationService()
diagram_service = DiagramService()
requirements_service = RequirementsService()
code_service = CodeService()

@router.post("/", response_model=ConversationResponse)
async def unified_chat_endpoint(
    request: ProjectUnifiedRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Unified endpoint that detects intent and routes to appropriate AI service
    with project-scoped memory management
    """
    try:
        user_id = current_user["user_id"]
        project_id = request.project_id or "default"
        
        # Detect intent
        intent_result = await intent_detection_service.detect_intent(
            user_id,
            project_id,
            request.message,
            request.intent_hint
        )
        
        logger.info(f"Detected intent: {intent_result.intent} with confidence: {intent_result.confidence}")
        
        # Prepare request data
        request_data = {
            "message": request.message,
            "intent": intent_result.intent,
            "extracted_params": intent_result.extracted_params,
            "confidence": intent_result.confidence
        }
        
        # Route to appropriate service
        if intent_result.intent == "requirements":
            request_data.update({
                "action": "validate",
                "requirement": request.message
            })
            result = await requirements_service.process_request(user_id, project_id, request_data)
            
            # If validation passes, generate documentation
            if result.get("is_valid", False):
                doc_request_data = {
                    "action": "generate",
                    "requirement": request.message
                }
                doc_result = await documentation_service.process_request(user_id, project_id, doc_request_data)
                return ConversationResponse(
                    user_id=user_id,
                    response=doc_result["jira_stories"]
                )
            else:
                return ConversationResponse(
                    user_id=user_id,
                    response=result["message"]
                )
        
        elif intent_result.intent == "documentation":
            request_data.update({
                "action": "generate",
                "requirement": request.message
            })
            result = await documentation_service.process_request(user_id, project_id, request_data)
            return ConversationResponse(
                user_id=user_id,
                response=result["jira_stories"]
            )
        
        elif intent_result.intent == "modify_documentation":
            request_data.update({
                "action": "modify",
                "modification_prompt": request.message
            })
            result = await documentation_service.process_request(user_id, project_id, request_data)
            return ConversationResponse(
                user_id=user_id,
                response=result["response"]
            )
        
        elif intent_result.intent == "diagram":
            diagram_type = intent_result.extracted_params.get("diagram_type", "flowchart")
            request_data.update({
                "action": "generate",
                "diagram_type": diagram_type
            })
            result = await diagram_service.process_request(user_id, project_id, request_data)
            return ConversationResponse(
                user_id=user_id,
                response=result["diagram_code"]
            )
        
        elif intent_result.intent == "modify_diagram":
            request_data.update({
                "action": "modify",
                "modification_prompt": request.message
            })
            result = await diagram_service.process_request(user_id, project_id, request_data)
            return ConversationResponse(
                user_id=user_id,
                response=result["diagram_code"]
            )
        
        elif intent_result.intent == "code":
            request_data.update({
                "action": "generate",
                "prompt": request.message
            })
            result = await code_service.process_request(user_id, project_id, request_data)
            
            # Format response for conversation
            response_text = f"""Successfully generated project!

**Project ID:** {result['project_id']}
**Technologies:** {', '.join(result['technologies'])}
**Files Generated:** {len(result['files'])}

{result['message']}

You can download the project using: /code/download-project with project ID: {result['project_id']}
"""
            return ConversationResponse(
                user_id=user_id,
                response=response_text
            )
        
        else:
            # Default to conversation service
            result = await conversation_service.process_request(user_id, project_id, request_data)
            return ConversationResponse(
                user_id=user_id,
                response=result["response"]
            )
            
    except Exception as e:
        logger.error(f"Error in unified endpoint: {str(e)}")
        raise AIServiceException(f"Error processing request: {str(e)}")

@router.post("/project/{project_id}", response_model=ConversationResponse)
async def project_chat_endpoint(
    project_id: str,
    request: UnifiedRequest, 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Project-specific chat endpoint for explicit project context
    """
    # Create project-scoped request
    project_request = ProjectUnifiedRequest(
        message=request.message,
        intent_hint=request.intent_hint,
        project_id=project_id
    )
    
    return await unified_chat_endpoint(project_request, current_user)

@router.get("/project/{project_id}/memory/summary")
async def get_project_memory_summary(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Get memory summary for a specific project"""
    from src.services.project_memory_service import project_memory_service
    
    user_id = current_user["user_id"]
    summary = project_memory_service.get_memory_summary(user_id, project_id)
    
    return summary

@router.delete("/project/{project_id}/memory")
async def clear_project_memory(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Clear memory for a specific project"""
    from src.services.project_memory_service import project_memory_service
    
    user_id = current_user["user_id"]
    success = project_memory_service.clear_memory(user_id, project_id)
    
    if success:
        return {"message": f"Memory cleared for project {project_id}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to clear memory")