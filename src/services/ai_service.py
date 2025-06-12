import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings
from src.core.exceptions import AIServiceException
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self._configure_gemini()
    
    def _configure_gemini(self):
        """Configure Gemini AI with API key"""
        try:
            genai.configure(api_key=settings.genai_api_key)
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {str(e)}")
            raise AIServiceException(f"Failed to configure Gemini: {str(e)}")
    
    def create_llm(
        self, 
        temperature: float = None, 
        max_tokens: int = None,
        model: str = None
    ) -> ChatGoogleGenerativeAI:
        try:
            llm = ChatGoogleGenerativeAI(
                model=model or settings.default_model,
                temperature=temperature or settings.default_temperature,
                top_p=0.95,
                top_k=40,
                max_output_tokens=max_tokens or settings.max_output_tokens,
                google_api_key=settings.genai_api_key,
            )
            logger.info(f"Created LLM with mode")
            return llm
        except Exception as e:
            logger.error(f"Failed to create LLM: {str(e)}")
            raise AIServiceException(f"Failed to create LLM: {str(e)}")

# Global instance
ai_service = AIService()