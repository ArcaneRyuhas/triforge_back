from fastapi import APIRouter, HTTPException
from src.models.requests import DocumentationRequest, ModifyJiraStoriesRequest
from src.models.responses import JiraStoriesResponse, ConversationResponse
from src.services.chain_factory import chain_factory
from src.services.memory_service import memory_service  
from src.core.exceptions import AIServiceException, MemoryNotFoundException
from src.utils.logger import logging
from src.services.validation_service import validation_service

router = APIRouter(prefix="/documentation", tags=["documentation"])
logger = logging.getLogger(__name__)

async def ensure_requirements_valid (requirement: str):
    """Ensure the requirement is valid and not empty."""
    

@router.post("/generate", response_model=JiraStoriesResponse)
async def generate_jira_stories(request: DocumentationRequest):
    """Generate Jira user stories using the documentation agent."""
    try:
        requirements_are_valid = await validation_service.validate_requirement(request.requirement, request.user_id)

        if requirements_are_valid != "true":
            return JiraStoriesResponse(
            user_id=request.user_id,
            jira_stories=requirements_are_valid.strip(),
            is_valid=False
            )

        jira_chain = chain_factory.create_documentation_chain(request.user_id)
        shared_memory = memory_service.get_or_create_memory(request.user_id)

        shared_memory.save_context(
            {"input": f"Requirement: {request.requirement}"}, 
            {"output": "I'll generate Jira stories for this requirement."}
        )
        
        jira_stories = jira_chain.predict(
            requirement=request.requirement,
            chat_history=shared_memory.load_memory_variables({})["chat_history"]
        )
        
        # Save to memory
        shared_memory.save_context(
            {"input": "Please generate Jira stories"}, 
            {"output": jira_stories}
        )
        
        return JiraStoriesResponse(
            user_id=request.user_id,
            jira_stories=jira_stories.strip(),
            is_valid=True
        )
    except Exception as e:
        logger.error(f"Jira stories generation error: {str(e)}")
        raise AIServiceException(f"Jira stories generation error: {str(e)}")

@router.post("/modify", response_model=ConversationResponse)
async def modify_jira_stories(request: ModifyJiraStoriesRequest):
    """Modify existing Jira stories based on a modification prompt."""
    try:
        modification_chain = chain_factory.create_jira_modification_chain(request.user_id)
        
        # Get original stories from request or memory
        original_stories = request.original_stories
        if not original_stories:
            original_stories = memory_service.get_last_ai_message(request.user_id)
            
        if not original_stories:
            raise MemoryNotFoundException(request.user_id)
        
        # Combine inputs
        combined_input = f"""Original Jira Stories:
{original_stories}

Additional Requirements/Feedback:
"{request.modification_prompt}"
"""
        
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        shared_memory.save_context(
            {"input": f"Request to modify Jira stories: {request.modification_prompt}"}, 
            {"output": "Processing modification request..."}
        )
        
        response = modification_chain.run(input=combined_input)
        
        # Save to memory
        shared_memory.save_context(
            {"input": "Please update the Jira stories"}, 
            {"output": response}
        )
        
        return ConversationResponse(user_id=request.user_id, response=response)
    except Exception as e:
        logger.error(f"Error modifying Jira stories: {str(e)}")
        raise AIServiceException(f"Error modifying Jira stories: {str(e)}")