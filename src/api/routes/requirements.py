from fastapi import APIRouter, HTTPException
from src.models.requests import RequirementsRefinementRequest
from src.models.responses import RequirementsRefinementResponse
from src.services.chain_factory import chain_factory
from src.services.memory_service import memory_service
from src.core.exceptions import AIServiceException, ValidationException
from src.utils.logger import logging

router = APIRouter(prefix="/requirements", tags=["requirements"])
logger = logging.getLogger(__name__)

@router.post("/refine", response_model=RequirementsRefinementResponse)
async def refine_requirements(request: RequirementsRefinementRequest):
    """Transform a poorly written document into well-structured requirements."""
    try:
        # Validate input
        if not request.raw_document or len(request.raw_document.strip()) < 10:
            raise ValidationException("Document is too short or empty. Please provide more content.")
        
        if len(request.raw_document) > 10000:
            raise ValidationException("Document is too long. Please keep it under 10000 characters.")
        
        # Create requirements refinement chain
        refinement_chain = chain_factory.create_requirements_refinement_chain(request.user_id)
        
        # Get memory for context
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        
        # Save input to memory
        shared_memory.save_context(
            {"input": f"Raw document to refine: {request.raw_document[:100]}..."}, 
            {"output": "Processing document refinement..."}
        )
        
        # Combine the input into a single string
        combined_input = f"""Raw Document:
{request.raw_document}

Output Format: {request.output_format or 'structured_requirements'}

Target Audience: {request.target_audience or 'development_team'}

Include Acceptance Criteria: {request.include_acceptance_criteria}"""
        
        # Process the document - using 'input' as the key
        response = refinement_chain.run(input=combined_input)
        
        # Save result to memory
        shared_memory.save_context(
            {"input": "Refine document into requirements"}, 
            {"output": response}
        )
        
        logger.info(f"Successfully refined requirements for user {request.user_id}")
        
        return RequirementsRefinementResponse(
            user_id=request.user_id,
            refined_requirements=response.strip(),
        )
        
    except ValidationException:
        raise
    except Exception as e:
        logger.error(f"Error refining requirements: {str(e)}")
        raise AIServiceException(f"Error refining requirements: {str(e)}")

@router.post("/analyze", response_model=RequirementsRefinementResponse)
async def analyze_requirements(request: RequirementsRefinementRequest):
    """Analyze a document and extract key requirements without full refinement."""
    try:
        analysis_chain = chain_factory.create_requirements_analysis_chain(request.user_id)
        
        shared_memory = memory_service.get_or_create_memory(request.user_id)
        
        # Process using 'input' as the key
        response = analysis_chain.run(input=request.raw_document)
        
        shared_memory.save_context(
            {"input": "Analyze document for requirements"}, 
            {"output": response}
        )
        
        return RequirementsRefinementResponse(
            user_id=request.user_id,
            refined_requirements=response.strip(),
        )
        
    except Exception as e:
        logger.error(f"Error analyzing requirements: {str(e)}")
        raise AIServiceException(f"Error analyzing requirements: {str(e)}")