import re
from typing import Optional, List

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