from langchain.memory import ConversationSummaryBufferMemory
from typing import Dict, Tuple, Optional
from src.core.config import settings
from src.services.ai_service import ai_service
from src.database.models.conversation_memory import ConversationMemoryModel
from src.database.session import SessionLocal  # Importar SessionLocal directamente
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class ProjectMemoryService:
    """Service for managing project-scoped conversation memory with summarization"""
    
    def __init__(self):
        self.active_memories: Dict[Tuple[str, str], ConversationSummaryBufferMemory] = {}
        self.max_token_limit = getattr(settings, 'memory_max_tokens', 2000)
    
    def get_or_create_memory(self, user_id: str, project_id: str) -> ConversationSummaryBufferMemory:
        """Get or create project-scoped memory with summary buffer"""
        memory_key = (user_id, project_id)
        
        if memory_key not in self.active_memories:
            # Create new memory with summary buffer
            llm = ai_service.create_llm(temperature=0.1, max_tokens=150)
            
            memory = ConversationSummaryBufferMemory(
                llm=llm,
                max_token_limit=self.max_token_limit,
                return_messages=True,
                memory_key="chat_history"
            )
            
            # Load existing conversation history from database
            self._load_memory_from_database(memory, user_id, project_id)
            
            self.active_memories[memory_key] = memory
            
            logger.info(f"Created new project memory for user {user_id}, project {project_id}")
        
        return self.active_memories[memory_key]
    
    def save_memory_to_database(self, user_id: str, project_id: str):
        """Persist memory to database"""
        try:
            memory_key = (user_id, project_id)
            if memory_key not in self.active_memories:
                return
            
            memory = self.active_memories[memory_key]
            
            # Get summary and recent messages
            summary = getattr(memory, 'moving_summary_buffer', '')
            recent_messages = []
            
            # Serialize recent messages
            for msg in memory.chat_memory.messages[-10:]:  # Last 10 messages
                recent_messages.append({
                    'type': msg.type,
                    'content': msg.content,
                    'timestamp': getattr(msg, 'timestamp', None)
                })
            
            # Create database session
            db = SessionLocal()
            try:
                memory_record = db.query(ConversationMemoryModel).filter_by(
                    user_id=user_id, 
                    project_id=project_id
                ).first()
                
                if memory_record:
                    memory_record.summary = summary
                    memory_record.recent_messages = recent_messages
                    memory_record.token_count = getattr(memory, 'token_count', 0)
                else:
                    memory_record = ConversationMemoryModel(
                        user_id=user_id,
                        project_id=project_id,
                        summary=summary,
                        recent_messages=recent_messages,
                        token_count=getattr(memory, 'token_count', 0)
                    )
                    db.add(memory_record)
                
                db.commit()
                logger.info(f"Saved memory to database for user {user_id}, project {project_id}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error saving memory to database: {str(e)}")
    
    def _load_memory_from_database(self, memory: ConversationSummaryBufferMemory, user_id: str, project_id: str):
        """Load existing memory from database"""
        try:
            # Create database session
            db = SessionLocal()
            try:
                memory_record = db.query(ConversationMemoryModel).filter_by(
                    user_id=user_id,
                    project_id=project_id
                ).first()
                
                if memory_record:
                    # Restore summary
                    if memory_record.summary:
                        memory.moving_summary_buffer = memory_record.summary
                    
                    # Restore recent messages
                    if memory_record.recent_messages:
                        from langchain.schema import HumanMessage, AIMessage
                        
                        for msg_data in memory_record.recent_messages:
                            if msg_data['type'] == 'human':
                                message = HumanMessage(content=msg_data['content'])
                            else:
                                message = AIMessage(content=msg_data['content'])
                            
                            memory.chat_memory.add_message(message)
                    
                    logger.info(f"Loaded memory from database for user {user_id}, project {project_id}")
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error loading memory from database: {str(e)}")
    
    def clear_memory(self, user_id: str, project_id: str = None) -> bool:
        """Clear memory for specific project or all user projects"""
        try:
            if project_id:
                # Clear specific project memory
                memory_key = (user_id, project_id)
                if memory_key in self.active_memories:
                    del self.active_memories[memory_key]
                
                # Clear from database
                db = SessionLocal()
                try:
                    db.query(ConversationMemoryModel).filter_by(
                        user_id=user_id,
                        project_id=project_id
                    ).delete()
                    db.commit()
                finally:
                    db.close()
                
                logger.info(f"Cleared memory for user {user_id}, project {project_id}")
                return True
            else:
                # Clear all user memories
                keys_to_remove = [key for key in self.active_memories.keys() if key[0] == user_id]
                for key in keys_to_remove:
                    del self.active_memories[key]
                
                # Clear from database
                db = SessionLocal()
                try:
                    db.query(ConversationMemoryModel).filter_by(user_id=user_id).delete()
                    db.commit()
                finally:
                    db.close()
                
                logger.info(f"Cleared all memories for user {user_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error clearing memory: {str(e)}")
            return False
    
    def get_memory_summary(self, user_id: str, project_id: str) -> Dict[str, any]:
        """Get memory summary and statistics"""
        try:
            memory = self.get_or_create_memory(user_id, project_id)
            
            return {
                "user_id": user_id,
                "project_id": project_id,
                "message_count": len(memory.chat_memory.messages),
                "token_count": getattr(memory, 'token_count', 0),
                "has_summary": bool(getattr(memory, 'moving_summary_buffer', '')),
                "summary_preview": getattr(memory, 'moving_summary_buffer', '')[:200] + "..." if getattr(memory, 'moving_summary_buffer', '') else ""
            }
        except Exception as e:
            logger.error(f"Error getting memory summary: {str(e)}")
            return {
                "user_id": user_id,
                "project_id": project_id,
                "message_count": 0,
                "token_count": 0,
                "has_summary": False,
                "summary_preview": "",
                "error": str(e)
            }

# Global instance
project_memory_service = ProjectMemoryService()