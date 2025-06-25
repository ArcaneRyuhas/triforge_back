from typing import Dict, List
from src.services.chain_factory import chain_factory
from src.services.memory_service import memory_service
from src.models.unified_requests import IntentDetectionResult
from src.utils.helpers import ContentFinder
import json
import logging

logger = logging.getLogger(__name__)

class IntentDetectionService:
    """Service for detecting user intent from messages and conversation history"""
    
    def __init__(self):
        self.intent_patterns = {
            "documentation": ["jira", "story", "stories", "requirement", "user story", "acceptance criteria"],
            "diagram": ["diagram", "flowchart", "sequence", "mermaid", "visualize", "chart", "flow"],
            "code": ["code", "implement", "build", "create app", "develop", "project", "full stack"],
            "modify": ["modify", "update", "change", "edit", "add to", "improve", "fix"]
        }
    
    async def detect_intent(self, user_id: str, message: str, hint: str = None) -> IntentDetectionResult:
        """Detect user intent using LLM and conversation context"""
        
        # If hint is provided and strong, use it
        if hint:
            logger.info(f"Using intent hint: {hint}")
            return IntentDetectionResult(
                intent=hint,
                confidence=1.0,
                extracted_params={}
            )
        
        # Get conversation history
        shared_memory = memory_service.get_or_create_memory(user_id)
        memory_messages = shared_memory.chat_memory.messages
        
        # Check for modification intent first
        is_modification = any(word in message.lower() for word in ["modify", "update", "change", "edit"])
        
        # Build context for intent detection
        context = self._build_context(memory_messages, is_modification)
        
        # Use intent detection chain
        intent_chain = chain_factory.create_intent_detection_chain(user_id)
        
        intent_prompt = f"""
        Analyze this message and conversation context to determine the user's intent.
        
        Message: "{message}"
        
        Context:
        {context}
        """
        
        try:
            response = intent_chain.predict(input=intent_prompt)
            
            # Import the JSON cleaner
            from src.utils.helpers import JSONResponseCleaner
            clean_response = JSONResponseCleaner.clean_json_response(response)
            result = json.loads(clean_response)
            
            logger.info(f"Intent detection result: {result}")
            
            return IntentDetectionResult(
                intent=result["intent"],
                confidence=float(result["confidence"]),
                extracted_params=result.get("extracted_params", {})
            )
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}, falling back to pattern matching")
            # Fallback to pattern matching
            return self._fallback_intent_detection(message, memory_messages)
    
    def _build_context(self, memory_messages, is_modification: bool) -> str:
        """Build context string from conversation history"""
        context_parts = []
        
        # Check what's in memory
        has_jira = ContentFinder.find_jira_stories_in_memory(memory_messages) is not None
        has_diagram = ContentFinder.find_diagram_in_memory(memory_messages) is not None
        has_code = ContentFinder.find_code_in_memory(memory_messages) is not None
        
        context_parts.append(f"Has Jira stories: {has_jira}")
        context_parts.append(f"Has diagram: {has_diagram}")
        context_parts.append(f"Has code: {has_code}")
        context_parts.append(f"Is modification request: {is_modification}")
        
        # Add last few messages
        recent_messages = []
        for msg in memory_messages[-4:]:  # Last 4 messages
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                recent_messages.append(f"[{msg.type}]: {msg.content[:100]}...")
        
        if recent_messages:
            context_parts.append("Recent conversation:")
            context_parts.extend(recent_messages)
        
        return "\n".join(context_parts)
    
    def _fallback_intent_detection(self, message: str, memory_messages) -> IntentDetectionResult:
        """Fallback pattern-based intent detection"""
        message_lower = message.lower()
        
        # Check for modifications
        if any(word in message_lower for word in ["modify", "update", "change"]):
            if ContentFinder.find_diagram_in_memory(memory_messages):
                return IntentDetectionResult(intent="modify_diagram", confidence=0.7, extracted_params={})
            elif ContentFinder.find_code_in_memory(memory_messages):
                return IntentDetectionResult(intent="modify_code", confidence=0.7, extracted_params={})
            elif ContentFinder.find_jira_stories_in_memory(memory_messages):
                return IntentDetectionResult(intent="modify_documentation", confidence=0.7, extracted_params={})
        
        # Check patterns
        for intent, patterns in self.intent_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return IntentDetectionResult(intent=intent, confidence=0.6, extracted_params={})
        
        # Default to conversation
        return IntentDetectionResult(intent="conversation", confidence=0.5, extracted_params={})
    
intent_detection_service = IntentDetectionService()