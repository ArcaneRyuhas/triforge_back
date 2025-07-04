from typing import Dict, Any
from src.ai_services.base_ai_service import BaseAIService
from src.ai_services.requirements_service import RequirementsService
from src.core.exceptions import ValidationException, AIServiceException
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class DocumentationService(BaseAIService):
    """Service for generating and modifying Jira stories and documentation"""
    
    def __init__(self):
        super().__init__()
        self.requirements_service = RequirementsService()
    
    async def process_request(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process documentation requests"""
        action = request_data.get("action", "generate")
        
        if action == "generate":
            return await self.generate_jira_stories(user_id, project_id, request_data)
        elif action == "modify":
            return await self.modify_jira_stories(user_id, project_id, request_data)
        else:
            raise ValidationException(f"Unknown documentation action: {action}")
    
    async def generate_jira_stories(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Jira user stories from requirements"""
        try:
            requirement = request_data.get("requirement", "")
            
            # Validate requirement using requirements service
            validation_result = await self.requirements_service.validate_requirement(
                user_id, project_id, {"requirement": requirement}
            )
            
            if not validation_result["is_valid"]:
                return {
                    "jira_stories": validation_result["message"],
                    "is_valid": False,
                    "success": False
                }
            
            # Get project memory for context
            memory = self.get_project_memory(user_id, project_id)
            
            # Create documentation chain
            jira_chain = self.chain_factory.create_documentation_chain(user_id, project_id)
            
            # Generate stories
            jira_stories = jira_chain.predict(
                requirement=requirement,
                chat_history=memory.load_memory_variables({})["chat_history"]
            )
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Generate Jira stories for: {requirement[:100]}...", 
                jira_stories
            )
            
            self.log_service_action("generate_jira_stories", user_id, project_id)
            
            return {
                "jira_stories": jira_stories.strip(),
                "is_valid": True,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating Jira stories: {str(e)}")
            raise AIServiceException(f"Error generating Jira stories: {str(e)}")
    
    async def modify_jira_stories(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Modify existing Jira stories based on feedback"""
        try:
            modification_prompt = request_data.get("modification_prompt", "")
            original_stories = request_data.get("original_stories")
            
            if not modification_prompt:
                raise ValidationException("Modification prompt is required")
            
            # Get original stories from memory if not provided
            if not original_stories:
                memory = self.get_project_memory(user_id, project_id)
                # Find last Jira stories in memory
                for msg in reversed(memory.chat_memory.messages):
                    if hasattr(msg, 'type') and msg.type == 'ai':
                        if "## As a" in msg.content or "story points" in msg.content.lower():
                            original_stories = msg.content
                            break
            
            if not original_stories:
                raise ValidationException("No original stories found. Please generate stories first.")
            
            # Create modification chain
            modification_chain = self.chain_factory.create_jira_modification_chain(user_id, project_id)
            
            # Prepare input
            combined_input = f"""Original Jira Stories:
{original_stories}

Additional Requirements/Feedback:
"{modification_prompt}"
"""
            
            # Process modification
            response = modification_chain.run(input=combined_input)
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Modify Jira stories: {modification_prompt}", 
                response
            )
            
            self.log_service_action("modify_jira_stories", user_id, project_id)
            
            return {
                "response": response,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error modifying Jira stories: {str(e)}")
            raise AIServiceException(f"Error modifying Jira stories: {str(e)}")