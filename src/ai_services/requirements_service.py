from typing import Dict, Any, Tuple
from src.ai_services.base_ai_service import BaseAIService
from src.core.exceptions import ValidationException, AIServiceException
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class RequirementsService(BaseAIService):
    """Service for requirements validation, refinement, and analysis"""
    
    async def process_request(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process requirements-related requests"""
        action = request_data.get("action", "validate")
        
        if action == "validate":
            return await self.validate_requirement(user_id, project_id, request_data)
        elif action == "refine":
            return await self.refine_requirements(user_id, project_id, request_data)
        elif action == "analyze":
            return await self.analyze_requirements(user_id, project_id, request_data)
        else:
            raise ValidationException(f"Unknown requirements action: {action}")
    
    async def validate_requirement(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate if a requirement is well-formed and suitable for processing"""
        requirement = request_data.get("requirement", "").strip()
        
        # Basic validation
        if not requirement:
            return {"is_valid": False, "message": "Requirement cannot be empty"}
        
        if len(requirement) < 10:
            return {"is_valid": False, "message": "Requirement is too short. Please provide more details."}
        
        if len(requirement) > 5000:
            return {"is_valid": False, "message": "Requirement is too long. Please keep it under 5000 characters."}
        
        # AI validation using chain
        try:
            validation_chain = self.chain_factory.create_validation_requirements_chain(user_id, project_id)
            validation_result = validation_chain.predict(requirement=requirement)
            
            is_valid = validation_result.strip().lower() == "true"
            
            self.log_service_action(
                "validate_requirement", 
                user_id, 
                project_id, 
                f"Result: {is_valid}"
            )
            
            return {
                "is_valid": is_valid,
                "message": "Requirement is valid and ready for processing" if is_valid else "Requirement needs improvement for better processing"
            }
            
        except Exception as e:
            logger.error(f"Error validating requirement for user {user_id}, project {project_id}: {str(e)}")
            return {"is_valid": False, "message": f"Validation service error: {str(e)}"}
    
    async def refine_requirements(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform poorly written requirements into well-structured ones"""
        try:
            raw_document = request_data.get("raw_document", "")
            output_format = request_data.get("output_format", "structured_requirements")
            include_acceptance_criteria = request_data.get("include_acceptance_criteria", True)
            target_audience = request_data.get("target_audience", "development_team")
            
            if len(raw_document.strip()) < 10:
                raise ValidationException("Document is too short. Please provide more content.")
            
            # Get project memory for context
            memory = self.get_project_memory(user_id, project_id)
            
            # Create refinement chain
            refinement_chain = self.chain_factory.create_requirements_refinement_chain(user_id, project_id)
            
            # Prepare input
            combined_input = f"""Raw Document:
{raw_document}

Output Format: {output_format}
Target Audience: {target_audience}
Include Acceptance Criteria: {include_acceptance_criteria}"""

            # Process refinement
            response = refinement_chain.run(input=combined_input)
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Refine requirements document ({len(raw_document)} chars)", 
                response
            )
            
            self.log_service_action("refine_requirements", user_id, project_id, f"Refined {len(raw_document)} chars")
            
            return {
                "refined_requirements": response.strip(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error refining requirements: {str(e)}")
            raise AIServiceException(f"Error refining requirements: {str(e)}")
    
    async def analyze_requirements(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze requirements document and extract key information"""
        try:
            document = request_data.get("document", "")
            
            # Create analysis chain
            analysis_chain = self.chain_factory.create_requirements_analysis_chain(user_id, project_id)
            
            # Process analysis
            response = analysis_chain.run(input=document)
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Analyze requirements document", 
                response
            )
            
            self.log_service_action("analyze_requirements", user_id, project_id)
            
            return {
                "analysis": response.strip(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error analyzing requirements: {str(e)}")
            raise AIServiceException(f"Error analyzing requirements: {str(e)}")