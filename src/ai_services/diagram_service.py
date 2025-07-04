from typing import Dict, Any
from src.ai_services.base_ai_service import BaseAIService
from src.core.exceptions import ValidationException, AIServiceException
from src.utils.helpers import ResponseCleaner, ContentFinder
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class DiagramService(BaseAIService):
    """Service for generating and modifying diagrams"""
    
    async def process_request(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process diagram requests"""
        action = request_data.get("action", "generate")
        
        if action == "generate":
            return await self.generate_diagram(user_id, project_id, request_data)
        elif action == "modify":
            return await self.modify_diagram(user_id, project_id, request_data)
        else:
            raise ValidationException(f"Unknown diagram action: {action}")
    
    async def generate_diagram(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a new diagram based on requirements or context"""
        try:
            diagram_type = request_data.get("diagram_type", "flowchart")
            
            # Validate diagram type
            valid_types = ["flowchart", "flow", "sequence", "class", "er", "entity-relationship", 
                          "state", "gantt", "user journey", "journey"]
            
            if diagram_type.lower() not in valid_types:
                raise ValidationException(f"Unsupported diagram type. Supported: {', '.join(valid_types)}")
            
            # Get project memory for context
            memory = self.get_project_memory(user_id, project_id)
            memory_messages = memory.chat_memory.messages
            
            # Look for Jira stories in memory
            jira_stories = ContentFinder.find_jira_stories_in_memory(memory_messages)
            
            if not jira_stories:
                raise ValidationException("No Jira stories found in project context. Please generate stories first.")
            
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
                diagram_type.lower(), 
                diagram_type.lower()
            )
            
            # Create diagram generation chain
            diagram_chain = self.chain_factory.create_diagram_generation_chain(user_id, project_id)
            
            # Prepare input
            combined_input = f"""Jira User Stories:
{jira_stories}

Diagram Type: {normalized_diagram_type}
"""
            
            # Generate diagram
            response = diagram_chain.run(input=combined_input)
            clean_response = ResponseCleaner.clean_mermaid_response(response)
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Generate {normalized_diagram_type} diagram", 
                clean_response
            )
            
            self.log_service_action("generate_diagram", user_id, project_id, f"Type: {normalized_diagram_type}")
            
            return {
                "diagram_code": clean_response,
                "diagram_type": normalized_diagram_type,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            raise AIServiceException(f"Error generating diagram: {str(e)}")
    
    async def modify_diagram(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Modify an existing diagram"""
        try:
            modification_prompt = request_data.get("modification_prompt", "")
            original_diagram_code = request_data.get("original_diagram_code")
            
            if not modification_prompt:
                raise ValidationException("Modification prompt is required")
            
            # Get original diagram from memory if not provided
            if not original_diagram_code:
                memory = self.get_project_memory(user_id, project_id)
                memory_messages = memory.chat_memory.messages
                original_diagram_code = ContentFinder.find_diagram_in_memory(memory_messages)
            
            if not original_diagram_code:
                raise ValidationException("No original diagram found in project context. Please generate a diagram first.")
            
            # Create modification chain
            modification_chain = self.chain_factory.create_diagram_modification_chain(user_id, project_id)
            
            # Prepare input
            combined_input = f"""Existing Mermaid.js Diagram:
{original_diagram_code}

Modification Request:
"{modification_prompt}"
"""
            
            # Process modification
            response = modification_chain.run(input=combined_input)
            clean_response = ResponseCleaner.clean_mermaid_response(response)
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Modify diagram: {modification_prompt}", 
                clean_response
            )
            
            self.log_service_action("modify_diagram", user_id, project_id)
            
            return {
                "diagram_code": clean_response,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error modifying diagram: {str(e)}")
            raise AIServiceException(f"Error modifying diagram: {str(e)}")