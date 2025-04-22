from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# ========== DOCUMENT MODELS ==========

class DocumentBase(BaseModel):
    document_id: str
    document_name: str
    source: str

class DocumentCreate(DocumentBase):
    content: str

class DocumentResponse(DocumentBase):
    chunk_count: int
    created_at: datetime

# ========== CHAT MODELS ==========

class ChatMessage(BaseModel):
    role: str = Field(..., description="The role of the message sender (user or assistant)")
    content: str = Field(..., description="The message content")

class ChatRequest(BaseModel):
    query: str = Field(..., description="The user's question")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation history")
    use_llm: bool = Field(default=True, description="Whether to use LLM to generate a final answer or just retrieve documents")

class ChatResponse(BaseModel):
    answer: str = Field(..., description="The assistant's generated response")
    source_documents: List[Dict[str, Any]] = Field(default=[], description="Relevant documents retrieved as context")

# ========== DRIVE INGESTION MODEL ==========

class DriveIngestionRequest(BaseModel):
    folder_id: Optional[str] = Field(default=None, description="Optional Google Drive folder ID to ingest")
