from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class DocumentBase(BaseModel):
    document_id: str
    document_name: str
    source: str

class DocumentCreate(DocumentBase):
    content: str
    
class DocumentResponse(DocumentBase):
    chunk_count: int
    created_at: datetime
    
class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., description="The message content")
    
class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's question")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous messages")
    
class ChatResponse(BaseModel):
    answer: str = Field(..., description="The assistant's response")
    source_documents: List[Dict[str, Any]] = Field(default=[], description="Source documents used for response")
    
class DriveIngestionRequest(BaseModel):
    folder_id: Optional[str] = Field(default=None, description="Optional Google Drive folder ID to ingest")