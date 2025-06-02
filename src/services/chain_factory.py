from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from typing import Dict
from src.services.ai_service import ai_service
from src.services.memory_service import memory_service
from src.utils.prompts import PROMPT_TEMPLATES

class ChainFactory:
    
    @staticmethod
    def create_documentation_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for generating Jira stories."""
        llm = ai_service.create_llm(temperature=0.4, max_tokens=400)
        
        prompt = PromptTemplate(
            input_variables=["requirement", "chat_history"],
            template=PROMPT_TEMPLATES["jira_generation"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_jira_modification_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for modifying existing Jira stories."""
        llm = ai_service.create_llm(temperature=0.1, max_tokens=400)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["jira_modification"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_diagram_generation_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for generating diagrams."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=300)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["diagram_generation"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_diagram_modification_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for modifying diagrams."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=300)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["diagram_modification"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_code_generation_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for generating code."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=300)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["code_generation"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_code_modification_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for modifying code."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=300)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["code_modification"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_conversation_chain(user_id: str) -> LLMChain:
        """Create a general conversation chain."""
        llm = ai_service.create_llm(temperature=0.2, max_tokens=100)
        
        prompt = PromptTemplate(
            input_variables=["input", "chat_history"],
            template=PROMPT_TEMPLATES["conversation"]
        )
        
        memory = memory_service.get_or_create_memory(user_id)
        return LLMChain(llm=llm, prompt=prompt, memory=memory, verbose=False)
    
    @staticmethod
    def create_validation_requirements_chain(user_id: str) -> LLMChain:
        """Create a specialized chain for validating requirements."""
        llm = ai_service.create_llm(temperature=0.0, max_tokens=300)
        
        prompt = PromptTemplate(
            input_variables=["requirement"],
            template=PROMPT_TEMPLATES["validation_requirements"]
        )
        
        return LLMChain(llm=llm, prompt=prompt, verbose=False)

chain_factory = ChainFactory()