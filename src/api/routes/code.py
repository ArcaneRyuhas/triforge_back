from fastapi import APIRouter, HTTPException
from src.models.requests import CodeGenerationRequest, ModifyCodeRequest
from src.models.responses import ConversationResponse
from src.services.chain_factory import chain_factory 
from src.services.memory_service import memory_service 
from src.utils.helpers import ResponseCleaner, ContentFinder
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging

router = APIRouter(prefix="/code", tags=["code"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=ConversationResponse)
async def generate_code(request: CodeGenerationRequest):
    """Generate code based on the latest diagram or Jira stories in memory."""
    try:
        if not request.programming_language:
            raise ValidationException("Programming language is required for code generation.")
        
        code_chain = chain_factory.create_code_generation_chain(request.user_id)
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        
        # Determine content source
        content_for_llm = ""
        source_type = "requirements"
        
        if request.diagram_code:
            content_for_llm = f"Diagram:\n{request.diagram_code}"
            source_type = "diagram"
        elif request.jira_stories:
            content_for_llm = f"Jira Stories:\n{request.jira_stories}"
            source_type = "jira stories"
        else:
            # Find content in memory
            memory_messages = shared_memory.chat_memory.messages
            
            # Prioritize diagram over Jira stories
            diagram_code = ContentFinder.find_diagram_in_memory(memory_messages)
            jira_stories = ContentFinder.find_jira_stories_in_memory(memory_messages)
            
            if diagram_code:
                content_for_llm = f"Diagram:\n{diagram_code}"
                source_type = "diagram"
            elif jira_stories:
                content_for_llm = f"Jira Stories:\n{jira_stories}"
                source_type = "jira stories"
            else:
                raise ValidationException("No diagram or Jira stories provided or found in conversation history. Cannot generate code.")
        
        # Add to memory
        shared_memory.save_context(
            {"input": f"Generate {request.programming_language} code based on {source_type}"},
            {"output": "Processing code generation request..."}
        )
        
        # Combine programming language with content
        full_input = f"Programming Language: {request.programming_language}\n{content_for_llm}"
        
        response = code_chain.run(input=full_input)
        clean_response = ResponseCleaner.clean_code_response(response, request.programming_language)
        
        # Save to memory
        shared_memory.save_context(
            {"input": f"Generated {request.programming_language} code"},
            {"output": clean_response}
        )
        
        return ConversationResponse(user_id=request.user_id, response=clean_response)
    except Exception as e:
        logger.error(f"Error generating code: {str(e)}")
        raise AIServiceException(f"Error generating code: {str(e)}")

@router.post("/modify", response_model=ConversationResponse)
async def modify_code(request: ModifyCodeRequest):
    """Modify existing code based on a modification prompt."""
    try:
        modification_chain = chain_factory.create_code_modification_chain(request.user_id)
        
        # Get original code from request or memory
        original_code = request.original_code
        if not original_code:
            shared_memory = memory_service.get_or_create_memory(request.user_id)
            memory_messages = shared_memory.chat_memory.messages
            original_code = ContentFinder.find_code_in_memory(memory_messages)
            
        if not original_code:
            raise ValidationException("No original code provided or found in conversation history. Please generate code first or provide the code.")
        
        # Combine inputs
        combined_input = f"""Existing Code:
{original_code}

Modification Request:
"{request.modification_prompt}"
"""
        
        # Process modification
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        shared_memory.save_context(
            {"input": f"Request to modify code: {request.modification_prompt}"}, 
            {"output": "Processing code modification request..."}
        )
        
        response = modification_chain.run(input=combined_input)
        clean_response = ResponseCleaner.clean_code_response(response)
        
        # Save to memory
        shared_memory.save_context(
            {"input": "Please update the code"}, 
            {"output": clean_response}
        )
        
        return ConversationResponse(user_id=request.user_id, response=clean_response)
    except Exception as e:
        logger.error(f"Error modifying code: {str(e)}")
        raise AIServiceException(f"Error modifying code: {str(e)}")