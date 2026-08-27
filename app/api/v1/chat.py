from fastapi import APIRouter, Depends, status
from fastapi.responses import StreamingResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])

# first endpoint of synchronous chat response
@router.post("/ask", response_model = ChatResponse, status_code = status.HTTP_200_OK)
async def ask_question(
    request: ChatRequest, 
    chat_service: ChatService = Depends(ChatService),
) -> ChatResponse:
    response = await chat_service.generate_chat_response(request)

    return response


# second endpoint of streaming responses
@router.post("/completions", status_code = status.HTTP_200_OK)
async def stream_chat_completions (
    request: ChatRequest, 
    chat_service: ChatService = Depends(ChatService),
) -> StreamingResponse:
    event_generator = chat_service.generate_chat_response_stream(request)
    return StreamingResponse(
        event_generator,
        media_type = "text/event-stream",
        headers = {
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
    