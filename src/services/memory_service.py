from langchain.memory import ConversationBufferWindowMemory
from typing import Dict
from src.core.config import settings

class MemoryService:
    def __init__(self):
        self.shared_memories: Dict[str, ConversationBufferWindowMemory] = {}
    
    def get_or_create_memory(self, user_id: str, k: int = None) -> ConversationBufferWindowMemory:
        """Get or create a shared memory instance for a user"""
        if k is None:
            k = settings.memory_window_size
            
        if user_id not in self.shared_memories:
            self.shared_memories[user_id] = ConversationBufferWindowMemory(
                k=k, 
                return_messages=True, 
                memory_key="chat_history"
            )
        return self.shared_memories[user_id]
    
    def clear_memory(self, user_id: str) -> bool:
        """Clear memory for a specific user"""
        if user_id in self.shared_memories:
            del self.shared_memories[user_id]
            return True
        return False
    
    def get_last_ai_message(self, user_id: str, pattern: str = None) -> str:
        """Get the last AI message, optionally matching a pattern"""
        if user_id not in self.shared_memories:
            return None
            
        memory = self.shared_memories[user_id]
        memory_messages = memory.chat_memory.messages
        
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                if pattern is None:
                    return msg.content
                # Add pattern matching logic here if needed
                return msg.content
        return None

# Global instance
memory_service = MemoryService()