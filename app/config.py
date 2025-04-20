import os
from pydantic import BaseModel
from typing import Optional

class Settings(BaseModel):
    # Database
    weaviate_url: str = os.getenv("WEAVIATE_URL", "http://weaviate:8080")
    weaviate_host: str = os.getenv("WEAVIATE_HOST", "weaviate")
    weaviate_port: int = int(os.getenv("WEAVIATE_PORT", "8080").strip().strip('"'))
    weaviate_grpc_port: int = int(os.getenv("WEAVIATE_GRPC_PORT", "50051").strip().strip('"'))

    # LLM
    ollama_base_url: str = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "phi3:3.8b")

    # Google Drive
    google_credentials_file: str = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials/credentials.json")
    google_token_file: str = os.getenv("GOOGLE_TOKEN_FILE", "credentials/token.json")

    # Vector store
    collection_name: str = "DocumentChunks"

    # Embedding model
    embedding_model: str = "all-MiniLM-L6-v2"

    # Chunk settings
    chunk_size: int = 1000
    chunk_overlap: int = 200

settings = Settings()
