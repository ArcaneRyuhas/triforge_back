import json
from uuid import uuid4
from typing import Dict, Any, List
from src.ai_services.base_ai_service import BaseAIService
from src.services.project_generation_service import project_generation_service
from src.core.exceptions import ValidationException, AIServiceException
from src.utils.helpers import ContextGatherer
from src.utils.logger import logging

logger = logging.getLogger(__name__)

class CodeService(BaseAIService):
    """Service for code generation and project creation"""
    
    async def process_request(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process code generation requests"""
        action = request_data.get("action", "generate")
        
        if action == "generate":
            return await self.generate_project_code(user_id, project_id, request_data)
        else:
            raise ValidationException(f"Unknown code action: {action}")
    
    async def generate_project_code(self, user_id: str, project_id: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a complete project with multiple technologies"""
        try:
            prompt = request_data.get("prompt", "")
            
            if not prompt.strip():
                raise ValidationException("Project prompt is required")
            
            generation_project_id = str(uuid4())
            
            # Get context from project memory
            memory = self.get_project_memory(user_id, project_id)
            memory_messages = memory.chat_memory.messages
            
            # Use ContextGatherer to collect and format context
            context_data = ContextGatherer.gather_project_context(memory_messages)
            context = ContextGatherer.format_context_for_llm(context_data)
            
            self.log_service_action("generate_project_start", user_id, project_id, f"Prompt: {prompt[:100]}...")
            
            # Step 1: Detect technologies
            technology_chain = self.chain_factory.create_technology_detection_chain(user_id, project_id)
            
            tech_response = technology_chain.predict(
                prompt=prompt,
                context=context
            )
            
            logger.info(f"Technology detection response: {tech_response}")
            
            # Parse technologies
            technologies = project_generation_service.parse_technologies(tech_response)
            
            if not technologies:
                raise ValidationException("No technologies could be detected from your prompt. Please be more specific.")
            
            logger.info(f"Detected {len(technologies)} technologies: {[tech.name for tech in technologies]}")
            
            # Step 2: Generate project code
            project_chain = self.chain_factory.create_project_code_generation_chain(user_id, project_id)
            
            technologies_str = json.dumps([
                {"name": tech.name, "category": tech.category, "version": tech.version}
                for tech in technologies
            ], indent=2)
            
            full_input = f"""
                Technologies to use:
                {technologies_str}

                User Requirements:
                {prompt}

                Context from Project Memory:
                {context}
                """

            # Add memory context if available
            if memory.chat_memory.messages:
                chat_history = memory.load_memory_variables({})["chat_history"]
                full_input += f"\n\nChat History:\n{chat_history}"

            code_response = project_chain.invoke(full_input)
            
            logger.info(f"Project code generation completed, response length: {len(str(code_response))}")
            
            # Handle different response formats
            if isinstance(code_response, dict) and 'text' in code_response:
                actual_response = code_response['text']
            else:
                actual_response = str(code_response)
            
            # Parse project files
            project_files = project_generation_service.parse_project_files(actual_response)
            
            if not project_files:
                raise ValidationException("No project files could be generated. Please try again with a different prompt.")
            
            logger.info(f"Generated {len(project_files)} project files")
            
            # Store the project
            project_structure = project_generation_service.store_project(
                generation_project_id, technologies, project_files
            )
            
            # Generate README content
            readme_content = project_generation_service._generate_readme(project_structure)
            
            # Save to memory
            self.save_to_memory(
                user_id, 
                project_id, 
                f"Generate project with technologies: {', '.join([tech.name for tech in technologies])}", 
                f"Generated complete project with {len(project_files)} files"
            )
            
            self.log_service_action("generate_project_complete", user_id, project_id, f"Generated {len(project_files)} files")
            
            return {
                "project_id": generation_project_id,
                "technologies": [tech.name for tech in technologies],
                "files": [{"path": f.path, "content": f.content, "language": f.language} for f in project_files],
                "project_structure": project_structure.root_structure,
                "readme_content": readme_content,
                "message": f"Successfully generated project with {len(project_files)} files using {', '.join([tech.name for tech in technologies])}",
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error generating project code: {str(e)}")
            raise AIServiceException(f"Error generating project code: {str(e)}")