from fastapi import APIRouter, Depends, HTTPException
from app.models import ChatRequest, ChatResponse
from app.services.chat_service import get_chat_service, ChatService

router = APIRouter(prefix="/api/chat", tags=["chat"])

@router.post("/", response_model=ChatResponse)
async def process_chat(
    chat_request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    try:
        response = await chat_service.process_query(
            query=chat_request.query,
            chat_history=chat_request.history
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))