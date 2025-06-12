import re
from typing import Optional, List, Dict

class ResponseCleaner:
    @staticmethod
    def clean_mermaid_response(response: str) -> str:
        """Clean Mermaid.js response by removing markdown blocks and prefixes"""
        clean_response = response.strip()
        
        # Remove markdown code block syntax if present
        if clean_response.startswith("```mermaid"):
            clean_response = clean_response[len("```mermaid"):].strip()
        if clean_response.startswith("```"):
            clean_response = clean_response[3:].strip()
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3].strip()
            
        # Remove common prefixes
        prefixes_to_remove = [
            "Here's a Mermaid.js diagram:",
            "Here is the Mermaid.js diagram:",
            "Here's the diagram:",
            "Mermaid.js code:",
            "Diagram:"
        ]
        
        for prefix in prefixes_to_remove:
            if clean_response.startswith(prefix):
                clean_response = clean_response[len(prefix):].strip()
        
        return clean_response
    
    @staticmethod
    def clean_code_response(response: str, language: str = None) -> str:
        """Clean code response by removing markdown blocks and prefixes"""
        clean_response = response.strip()
        
        # Remove markdown code block syntax
        lines = clean_response.split('\n')
        if len(lines) > 1 and lines[0].strip().startswith("```") and lines[-1].strip() == "```":
            clean_response = "\n".join(lines[1:-1]).strip()
        elif clean_response.startswith("```"):
            clean_response = clean_response[3:].strip()
        
        # Remove common prefixes
        prefixes_to_remove = [
            f"Here's the {language} code:" if language else "Here's the code:",
            f"Here is the {language} code:" if language else "Here is the code:",
            "Generated Code:",
            "Code:"
        ]
        
        for prefix in prefixes_to_remove:
            if clean_response.startswith(prefix):
                clean_response = clean_response[len(prefix):].strip()
        
        return clean_response

class ContentFinder:
    @staticmethod
    def find_jira_stories_in_memory(memory_messages) -> Optional[str]:
        """Find Jira stories in memory messages"""
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                if re.search(r"##\s*As a\s*", msg.content) or "story points" in msg.content.lower():
                    return msg.content
        return None
    
    @staticmethod
    def find_diagram_in_memory(memory_messages) -> Optional[str]:
        """Find Mermaid diagram in memory messages"""
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                content = msg.content.strip()
                if content.startswith(("graph", "sequenceDiagram", "classDiagram", "erDiagram", "stateDiagram", "gantt", "journey")):
                    return content
        return None
    
    @staticmethod
    def find_code_in_memory(memory_messages) -> Optional[str]:
        """Find code in memory messages"""
        code_patterns = [
            r'def\s+\w+\s*\(',  # Python functions
            r'class\s+\w+',     # Class definitions
            r'import\s+\w+',    # Import statements
            r'from\s+\w+\s+import',  # From imports
            r'function\s+\w+\s*\(',  # JavaScript functions
            r'public\s+class\s+\w+',  # Java classes
            r'public\s+static\s+void\s+main',  # Java main
            r'#include\s*<',     # C/C++ includes
            r'int\s+main\s*\(',  # C/C++ main
            r'console\.log\s*\(',  # JavaScript console.log
            r'System\.out\.println',  # Java print
            r'print\s*\(',       # Python print
        ]
        
        for msg in reversed(memory_messages):
            if hasattr(msg, 'type') and msg.type == 'ai':
                content = msg.content.strip()
                if any(re.search(pattern, content, re.IGNORECASE | re.MULTILINE) for pattern in code_patterns):
                    return content
        return None

class JSONResponseCleaner:
    """Helper class to clean and parse JSON responses from LLMs"""
    
    @staticmethod
    def clean_json_response(response: str) -> str:
        """Clean JSON response by removing markdown blocks and common prefixes"""
        clean_response = response.strip()
        
        # Remove markdown code block syntax if present
        if clean_response.startswith("```json"):
            clean_response = clean_response[len("```json"):].strip()
        elif clean_response.startswith("```"):
            clean_response = clean_response[3:].strip()
        
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3].strip()
        
        # Remove common prefixes that LLMs might add
        prefixes_to_remove = [
            "Here's the JSON:",
            "Here is the JSON:",
            "JSON response:",
            "Response:",
            "Output:"
        ]
        
        for prefix in prefixes_to_remove:
            if clean_response.startswith(prefix):
                clean_response = clean_response[len(prefix):].strip()
        
        return clean_response
    
    @staticmethod
    def safe_json_parse(response: str, fallback_data: dict = None):
        """Safely parse JSON with fallback"""
        try:
            cleaned = JSONResponseCleaner.clean_json_response(response)
            return json.loads(cleaned)
        except json.JSONDecodeError:
            if fallback_data:
                return fallback_data
            raise

class ContextGatherer:
    """Helper class to gather and format context from memory for AI chains"""
    
    @staticmethod
    def gather_project_context(memory_messages) -> Dict[str, str]:
        """Gather all relevant context for project generation"""
        context = {
            "requirements": None,
            "diagrams": None,
            "code": None,
            "conversations": []
        }
        
        # Find Jira stories/requirements
        context["requirements"] = ContentFinder.find_jira_stories_in_memory(memory_messages)
        
        # Find diagrams
        context["diagrams"] = ContentFinder.find_diagram_in_memory(memory_messages)
        
        # Find existing code
        context["code"] = ContentFinder.find_code_in_memory(memory_messages)
        
        # Gather recent conversations for additional context
        conversation_count = 0
        for msg in reversed(memory_messages):
            if conversation_count >= 5:  # Limit to last 5 conversations
                break
            
            if hasattr(msg, 'type') and hasattr(msg, 'content'):
                context["conversations"].append({
                    "type": msg.type,
                    "content": msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                })
                conversation_count += 1
        
        return context
    
    @staticmethod
    def format_context_for_llm(context: Dict[str, str]) -> str:
        """Format context dictionary into a readable string for LLM"""
        formatted_parts = []
        
        if context.get("requirements"):
            formatted_parts.append(f"=== REQUIREMENTS/USER STORIES ===\n{context['requirements']}")
        
        if context.get("diagrams"):
            formatted_parts.append(f"=== SYSTEM DIAGRAM ===\n{context['diagrams']}")
        
        if context.get("code"):
            formatted_parts.append(f"=== EXISTING CODE ===\n{context['code']}")
        
        if context.get("conversations"):
            conv_text = "\n".join([
                f"[{conv['type'].upper()}]: {conv['content']}" 
                for conv in context["conversations"]
            ])
            formatted_parts.append(f"=== RECENT CONVERSATION ===\n{conv_text}")
        
        if not formatted_parts:
            return "No previous context available."
        
        return "\n\n".join(formatted_parts)