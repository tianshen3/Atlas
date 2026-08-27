from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])

# first endpoint of synchronous chat response
@router.post("/ask", response_model = ChatResponse, status_code = status.HTTP_200_OK)
async def ask_question(
    request: ChatRequest, 
    chat_serivce: ChatService = Depends(ChatService),
) -> ChatResponse:
    response = await chat_serivce.generate_chat_response(request)

    return response

