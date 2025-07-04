from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from src.services.project_memory_service import project_memory_service
from src.services.chain_factory import chain_factory
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class BaseAIService(ABC):
    """Abstract base class for AI services with project-scoped memory"""
    
    def __init__(self):
        self.project_memory_service = project_memory_service
        self.chain_factory = chain_factory
    
    @abstractmethod
    async def process_request(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process AI request with project context"""
        pass
    
    def get_project_memory(self, user_id: str, project_id: str):
        """Get or create project-scoped memory"""
        return self.project_memory_service.get_or_create_memory(user_id, project_id)
    
    def save_to_memory(self, user_id: str, project_id: str, input_msg: str, output_msg: str):
        """Save interaction to project memory"""
        memory = self.get_project_memory(user_id, project_id)
        memory.save_context({"input": input_msg}, {"output": output_msg})
        
    def log_service_action(self, action: str, user_id: str, project_id: str, details: str = ""):
        """Log service actions with context"""
        logger.info(f"[{self.__class__.__name__}] {action} - User: {user_id}, Project: {project_id}, {details}")