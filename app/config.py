import os
from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    # ChromaDB
    chroma_persist_directory: str = os.getenv("CHROMA_PERSIST_DIRECTORY", "chroma_db")
    
    # LLM
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "phi3:3.8b")
    system_prompt: Optional[str] = os.getenv("SYSTEM_PROMPT", None)

    # Google Drive
    google_credentials_file: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials/credentials.json")
    google_token_file: str = os.getenv("GOOGLE_TOKEN_FILE", "credentials/token.json")

    # Vector store
    collection_name: str = "document_chunks"

    # Embedding model and service
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Chunk settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

settings = Settings()