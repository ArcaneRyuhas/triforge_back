import logging
from typing import Tuple
from src.services.chain_factory import chain_factory

logger = logging.getLogger(__name__)

class ValidationService:
    """Service for validating various types of input using AI chains"""
    
    def __init__(self):
        self.chain_factory = chain_factory
    
    async def validate_requirement(self, requirement: str, user_id: str) -> str:
        """
        Validate if a requirement is well-formed and suitable for Jira story generation.
        
        Args:
            requirement: The requirement text to validate
            user_id: User ID for chain creation
            
        Returns:
            str: "true" if valid, otherwise returns error message explaining why it's invalid
        """
        try:
            if not requirement or not requirement.strip():
                return "Requirement cannot be empty"
            
            if len(requirement.strip()) < 10:
                return "Requirement is too short. Please provide more details."
            
            if len(requirement) > 5000:
                return "Requirement is too long. Please keep it under 5000 characters."
            
            validation_chain = self.chain_factory.create_validation_requirements_chain(user_id)
            validation_result = validation_chain.predict(requirement=requirement.strip())
            
            if validation_result == "true":
                logger.info(f"Requirement validation passed for user {user_id}")
            else:
                logger.warning(f"Requirement validation failed for user {user_id}: {validation_result}")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Error validating requirement for user {user_id}: {str(e)}")
            return f"Validation service error: {str(e)}"
    
    async def validate_modification_prompt(self, modification_prompt: str) -> Tuple[bool, str]:
        """
        Validate modification prompts for clarity and actionability.
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        if not modification_prompt or not modification_prompt.strip():
            return False, "Modification prompt cannot be empty"
        
        if len(modification_prompt.strip()) < 5:
            return False, "Modification prompt is too short. Please be more specific."
        
        return True, "Modification prompt is valid"
    
    async def validate_diagram_type(self, diagram_type: str) -> Tuple[bool, str]:
        """
        Validate diagram type against supported types.
        
        Returns:
            Tuple[bool, str]: (is_valid, message)
        """
        supported_types = [
            "flowchart", "flow", "sequence", "class", "er", 
            "entity-relationship", "state", "gantt", "user journey", "journey"
        ]
        
        if not diagram_type:
            return False, "Diagram type is required"
        
        if diagram_type.lower() not in supported_types:
            return False, f"Unsupported diagram type. Supported types: {', '.join(supported_types)}"
        
        return True, "Diagram type is valid"

validation_service = ValidationService()