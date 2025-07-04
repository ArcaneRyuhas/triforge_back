from typing import Dict, Any
from src.ai_services.base_ai_service import BaseAIService
from src.core.exceptions import AIServiceException
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class ConversationService(BaseAIService):
    """Service for handling general conversation and Q&A"""
    
    async def process_request(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process general conversation requests"""
        try:
            message = request_data.get("message", "")
            
            if not message.strip():
                return {
                    "response": "I'm here to help! You can ask me to create Jira stories, generate diagrams, build code, or just have a conversation.",
                    "success": True
                }
            
            # Get project memory for context
            memory = self.get_project_memory(user_id, project_id)
            
            # Create conversation chain with project context
            conversation_chain = self.chain_factory.create_conversation_chain(user_id, project_id)
            
            # Generate response
            response = conversation_chain.predict(input=message)
            
            # Save to memory
            self.save_to_memory(user_id, project_id, message, response)
            
            self.log_service_action("conversation", user_id, project_id, f"Message length: {len(message)}")
            
            return {
                "response": response,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error in conversation service: {str(e)}")
            raise AIServiceException(f"Error in conversation: {str(e)}")