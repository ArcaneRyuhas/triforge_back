from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Dict
from src.services.ai_service import ai_service
from src.services.project_memory_service import project_memory_service
from src.utils.prompts import PROMPT_TEMPLATES

class ChainFactory:
    """Updated chain factory with project-scoped memory support"""
    
    @staticmethod
    def create_documentation_chain(user_id: str, project_id: str) -> LLMChain:
        """Create a specialized chain for generating Jira stories with project context."""
        llm = ai_service.create_llm(temperature=0.4, max_tokens=400)
        
        prompt = PromptTemplate(
            input_variables=["requirement", "chat_history"],
            template=PROMPT_TEMPLATES["jira_generation"]
        )
        
        memory = project_memory_service.get_or_create_memory(user_id, project_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_validation_requirements_chain(user_id: str, project_id: str) -> LLMChain:
        """Create a specialized chain for validating requirements with project context."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=300)
        
        prompt = PromptTemplate(
            input_variables=["requirement"],
            template=PROMPT_TEMPLATES["validation_requirements"]
        )
        
        # Note: Validation chains don't need memory, but we keep the signature consistent
        return LLMChain(llm=llm, prompt=prompt, verbose=False)
    
    @staticmethod
    def create_requirements_refinement_chain(user_id: str, project_id: str) -> LLMChain:
        """Create a specialized chain for refining requirements with project context."""
        llm = ai_service.create_llm(temperature=0.3, max_tokens=800)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["requirements_refinement"]
        )
        
        memory = project_memory_service.get_or_create_memory(user_id, project_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_intent_detection_chain(user_id: str, project_id: str) -> LLMChain:
        """Create a specialized chain for detecting user intent with project context."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=150)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["intent_detection"]
        )
        
        memory = project_memory_service.get_or_create_memory(user_id, project_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

    # Update all other chain creation methods to include project_id parameter
    @staticmethod
    def create_conversation_chain(user_id: str, project_id: str) -> LLMChain:
        llm = ai_service.create_llm(temperature=0.2, max_tokens=100)
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["conversation"]
        )
        memory = project_memory_service.get_or_create_memory(user_id, project_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)

chain_factory = ChainFactory()