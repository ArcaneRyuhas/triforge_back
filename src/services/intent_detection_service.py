from typing import Dict, List
from src.services.chain_factory import chain_factory
from src.services.project_memory_service import project_memory_service
from src.models.unified_requests import IntentDetectionResult
from src.utils.helpers import ContentFinder
import json
import logging

logger = logging.getLogger(__name__)

class IntentDetectionService:
    """Enhanced service for detecting user intent with project context and requirements classification"""
    
    def __init__(self):
        self.intent_patterns = {
            "requirements": ["requirement", "need", "should", "must", "want to build", "system should"],
            "documentation": ["jira", "story", "stories", "user story", "acceptance criteria", "epic"],
            "diagram": ["diagram", "flowchart", "sequence", "mermaid", "visualize", "chart", "flow"],
            "code": ["code", "implement", "build", "create app", "develop", "project", "full stack"],
            "modify": ["modify", "update", "change", "edit", "add to", "improve", "fix"],
            "conversation": ["what", "how", "why", "explain", "tell me", "help", "?"]
        }
    
    async def detect_intent(self, user_id: str, project_id: str, message: str, hint: str = None) -> IntentDetectionResult:
        """Detect user intent using enhanced LLM analysis with project context"""
        
        # If hint is provided and strong, use it
        if hint:
            logger.info(f"Using intent hint: {hint}")
            return IntentDetectionResult(
                intent=hint,
                confidence=1.0,
                extracted_params={}
            )
        
        # Get project conversation history
        memory = project_memory_service.get_or_create_memory(user_id, project_id)
        memory_messages = memory.chat_memory.messages
        
        # Enhanced context building for better intent detection
        context = self._build_enhanced_context(memory_messages, message)
        
        # Use enhanced intent detection chain
        intent_chain = chain_factory.create_intent_detection_chain(user_id, project_id)
        
        intent_prompt = f"""
        Analyze this message and project context to determine the user's intent.
        
        Message: "{message}"
        
        Project Context:
        {context}
        
        Pay special attention to:
        1. Whether this is a NEW requirement/need vs asking about EXISTING documentation
        2. If user is describing what they want to build (requirements) vs asking to create stories (documentation)
        3. Whether they're modifying existing content or creating new content
        4. Technical words that indicate code generation vs business requirements
        """
        
        try:
            response = intent_chain.predict(input=intent_prompt)
            
            from src.utils.helpers import JSONResponseCleaner
            clean_response = JSONResponseCleaner.clean_json_response(response)
            result = json.loads(clean_response)
            
            # Enhanced intent classification logic
            detected_intent = self._classify_intent_enhanced(result["intent"], message, context)
            
            logger.info(f"Intent detection result: {detected_intent}")
            
            return IntentDetectionResult(
                intent=detected_intent,
                confidence=float(result["confidence"]),
                extracted_params=result.get("extracted_params", {})
            )
        except Exception as e:
            logger.error(f"Intent detection failed: {str(e)}, falling back to enhanced pattern matching")
            return self._fallback_intent_detection_enhanced(message, memory_messages)
    
    def _classify_intent_enhanced(self, raw_intent: str, message: str, context: str) -> str:
        """Enhanced intent classification with requirements vs documentation distinction"""
        message_lower = message.lower()
        
        # Check for modification patterns first
        if any(word in message_lower for word in ["modify", "update", "change", "edit", "improve"]):
            if "diagram" in context.lower() or any(word in message_lower for word in ["diagram", "flowchart"]):
                return "modify_diagram"
            elif "stories" in context.lower() or "jira" in context.lower():
                return "modify_documentation"
            elif "code" in context.lower():
                return "modify_code"
        
        # Distinguish requirements from documentation
        requirement_indicators = [
            "i need", "i want", "system should", "application should", "website should",
            "need to build", "want to create", "building", "developing", "project that",
            "system that", "app that", "website that", "platform that"
        ]
        
        documentation_indicators = [
            "create stories", "generate stories", "jira stories", "user stories",
            "write stories", "make stories", "stories for", "break down into stories"
        ]
        
        # Check for requirements intent
        if any(indicator in message_lower for indicator in requirement_indicators):
            if not any(indicator in message_lower for indicator in documentation_indicators):
                return "requirements"
        
        # Check for explicit documentation request
        if any(indicator in message_lower for indicator in documentation_indicators):
            return "documentation"
        
        # Technical/code generation indicators
        code_indicators = [
            "build", "implement", "code", "develop", "create app", "full stack",
            "frontend", "backend", "database", "api", "react", "node", "python"
        ]
        
        if any(indicator in message_lower for indicator in code_indicators):
            return "code"
        
        # Diagram indicators
        diagram_indicators = [
            "diagram", "flowchart", "sequence", "chart", "visualize", "flow", "mermaid"
        ]
        
        if any(indicator in message_lower for indicator in diagram_indicators):
            return "diagram"
        
        # Default to conversation for questions and unclear intents
        return "conversation"
    
    def _build_enhanced_context(self, memory_messages, current_message: str) -> str:
        """Build enhanced context with better categorization"""
        context_parts = []
        
        # Check what's in project memory
        has_jira = ContentFinder.find_jira_stories_in_memory(memory_messages) is not None
        has_diagram = ContentFinder.find_diagram_in_memory(memory_messages) is not None
        has_code = ContentFinder.find_code_in_memory(memory_messages) is not None
        
        context_parts.append(f"Project has Jira stories: {has_jira}")
        context_parts.append(f"Project has diagrams: {has_diagram}")
        context_parts.append(f"Project has code: {has_code}")
        
        # Analyze current message characteristics
        message_lower = current_message.lower()
        is_question = current_message.strip().endswith('?') or any(
            word in message_lower for word in ['what', 'how', 'why', 'when', 'where', 'which']
        )
        is_request = any(word in message_lower for word in ['create', 'generate', 'make', 'build'])
        is_description = any(word in message_lower for word in ['need', 'want', 'should', 'require'])
        
        context_parts.append(f"Message is question: {is_question}")
        context_parts.append(f"Message is request: {is_request}")
        context_parts.append(f"Message is description: {is_description}")
        
        # Add recent conversation for context
        recent_messages = []
        for msg in memory_messages[-3:]:  # Last 3 messages for context
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                recent_messages.append(f"[{msg.type}]: {msg.content[:150]}...")
        
        if recent_messages:
            context_parts.append("Recent conversation:")
            context_parts.extend(recent_messages)
        
        return "\n".join(context_parts)
    
    def _fallback_intent_detection_enhanced(self, message: str, memory_messages) -> IntentDetectionResult:
        """Enhanced fallback pattern-based intent detection"""
        message_lower = message.lower()
        
        # Check for modifications with better context awareness
        if any(word in message_lower for word in ["modify", "update", "change", "edit"]):
            if ContentFinder.find_diagram_in_memory(memory_messages):
                return IntentDetectionResult(intent="modify_diagram", confidence=0.7, extracted_params={})
            elif ContentFinder.find_code_in_memory(memory_messages):
                return IntentDetectionResult(intent="modify_code", confidence=0.7, extracted_params={})
            elif ContentFinder.find_jira_stories_in_memory(memory_messages):
                return IntentDetectionResult(intent="modify_documentation", confidence=0.7, extracted_params={})
        
        # Enhanced pattern matching with requirements vs documentation distinction
        if any(pattern in message_lower for pattern in self.intent_patterns["requirements"]):
            if not any(pattern in message_lower for pattern in ["story", "stories", "jira"]):
                return IntentDetectionResult(intent="requirements", confidence=0.6, extracted_params={})
        
        # Check other patterns
        for intent, patterns in self.intent_patterns.items():
            if intent != "requirements" and any(pattern in message_lower for pattern in patterns):
                return IntentDetectionResult(intent=intent, confidence=0.6, extracted_params={})
        
        # Default to conversation
        return IntentDetectionResult(intent="conversation", confidence=0.5, extracted_params={})

intent_detection_service = IntentDetectionService()