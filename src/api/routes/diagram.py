from fastapi import APIRouter, HTTPException
from src.models.requests import DiagramGenerationRequest, ModifyDiagramRequest
from src.models.responses import ConversationResponse
from src.services.chain_factory import chain_factory  # Direct import
from src.services.memory_service import memory_service  # Direct import
from src.utils.helpers import ResponseCleaner, ContentFinder
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging

router = APIRouter(prefix="/diagram", tags=["diagram"])
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=ConversationResponse)
async def generate_diagram(request: DiagramGenerationRequest):
    """Generate a diagram based on Jira stories and diagram type."""
    try:
        # Validate diagram type
        if not request.diagram_type:
            raise ValidationException("Diagram type (e.g., 'flowchart', 'sequence', 'class') is required.")
        
        diagram_chain = chain_factory.create_diagram_generation_chain(request.user_id)
        
        # Get Jira stories from request or memory
        jira_stories = request.jira_stories
        if not jira_stories:
            shared_memory = memory_service.get_or_create_memory(request.user_id)
            memory_messages = shared_memory.chat_memory.messages
            jira_stories = ContentFinder.find_jira_stories_in_memory(memory_messages)
            
        if not jira_stories:
            raise ValidationException("No Jira stories provided or found in conversation history. Please generate stories first or provide them.")
        
        # Map diagram types
        diagram_type_mapping = {
            "flow": "flowchart",
            "flowchart": "flowchart",
            "sequence": "sequence", 
            "class": "class",
            "er": "entity-relationship",
            "entity relationship": "entity-relationship",
            "state": "state",
            "gantt": "gantt",
            "user journey": "user journey",
            "journey": "user journey"
        }
        
        normalized_diagram_type = diagram_type_mapping.get(
            request.diagram_type.lower(), 
            request.diagram_type.lower()
        )
        
        # Combine inputs
        combined_input = f"""Jira User Stories:
{jira_stories}

Diagram Type: {normalized_diagram_type}
"""
        
        # Add to memory and process
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        shared_memory.save_context(
            {"input": f"Generate a {normalized_diagram_type} diagram for these Jira stories"}, 
            {"output": "Processing diagram generation request..."}
        )
        
        response = diagram_chain.run(input=combined_input)
        clean_response = ResponseCleaner.clean_mermaid_response(response)
        
        # Save to memory
        shared_memory.save_context(
            {"input": f"Generate a {normalized_diagram_type} diagram"}, 
            {"output": clean_response}
        )
        
        return ConversationResponse(user_id=request.user_id, response=clean_response)
    except Exception as e:
        logger.error(f"Error generating diagram: {str(e)}")
        raise AIServiceException(f"Error generating diagram: {str(e)}")

@router.post("/modify", response_model=ConversationResponse)
async def modify_diagram(request: ModifyDiagramRequest):
    """Modify an existing Mermaid.js diagram based on a modification prompt."""
    try:
        modification_chain = chain_factory.create_diagram_modification_chain(request.user_id)
        
        # Get original diagram from request or memory
        original_diagram_code = request.original_diagram_code
        if not original_diagram_code:
            shared_memory = memory_service.get_or_create_memory(request.user_id)
            memory_messages = shared_memory.chat_memory.messages
            original_diagram_code = ContentFinder.find_diagram_in_memory(memory_messages)
            
        if not original_diagram_code:
            raise ValidationException("No original diagram code provided or found in conversation history. Please generate a diagram first or provide the code.")
        
        # Combine inputs
        combined_input = f"""Existing Mermaid.js Diagram:
{original_diagram_code}

Modification Request:
"{request.modification_prompt}"
"""
        
        # Process modification
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        shared_memory.save_context(
            {"input": f"Request to modify diagram: {request.modification_prompt}"}, 
            {"output": "Processing diagram modification request..."}
        )
        
        response = modification_chain.run(input=combined_input)
        clean_response = ResponseCleaner.clean_mermaid_response(response)
        
        # Save to memory
        shared_memory.save_context(
            {"input": "Please update the diagram"}, 
            {"output": clean_response}
        )
        
        return ConversationResponse(user_id=request.user_id, response=clean_response)
    except Exception as e:
        logger.error(f"Error modifying diagram: {str(e)}")
        raise AIServiceException(f"Error modifying diagram: {str(e)}")