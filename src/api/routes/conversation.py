from fastapi import APIRouter, HTTPException
from src.models.requests import Message
from src.models.responses import ConversationResponse
from src.services.chain_factory import chain_factory  # Direct import
from src.services.memory_service import memory_service  # Direct import
from src.core.exceptions import AIServiceException

router = APIRouter(prefix="/conversation", tags=["conversation"])

@router.post("/", response_model=ConversationResponse)
async def handle_conversation(message: Message):
    """Handle a conversational message from the user."""
    try:
        chain = chain_factory.create_conversation_chain(message.user_id)
        response = chain.predict(input=message.content)
        
        return ConversationResponse(
            user_id=message.user_id,
            response=response
        )
    except Exception as e:
        raise AIServiceException(f"Error in conversation: {str(e)}")