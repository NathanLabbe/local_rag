from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from app.services.chat_service import get_chat_service, ChatService

router = APIRouter(
    prefix="/api/chat",
    tags=["chat"],
)

class ChatRequest(BaseModel):
    query: str
    history: Optional[List[Dict[str, Any]]] = []

class ChatResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []

@router.post("/", response_model=ChatResponse)
async def process_chat(
    chat_request: ChatRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """Process a chat message and return a response"""
    try:
        # Use get_response instead of process_query
        result = await chat_service.get_response(chat_request.query)
        return ChatResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))