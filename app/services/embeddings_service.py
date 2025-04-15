import httpx
import numpy as np
from typing import List, Union
from langchain.embeddings.base import Embeddings

from app.config import settings

class CustomEmbeddings(Embeddings):
    def __init__(self, embedding_service):
        self.embedding_service = embedding_service
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self.embedding_service.get_embeddings_sync(text) for text in texts]
        
    def embed_query(self, text: str) -> List[float]:
        return self.embedding_service.get_embeddings_sync(text)

class EmbeddingService:
    def __init__(self):
        # Using the transformers container for embeddings
        self.transformers_url = "http://transformers:8080"
        self._embeddings_cache = {}
        self._langchain_embeddings = None
        
    async def get_embeddings(self, text: str) -> List[float]:
        # Simple cache to avoid re-computing embeddings for the same text
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.transformers_url}/vectors",
                json={"text": text}
            )
            
            if response.status_code != 200:
                raise Exception(f"Error getting embeddings: {response.text}")
                
            result = response.json()
            vector = result.get("vector", [])
            
            # Cache the result
            self._embeddings_cache[text] = vector
            return vector
    
    def get_embeddings_sync(self, text: str) -> List[float]:
        """Synchronous version for LangChain compatibility"""
        import asyncio
        return asyncio.run(self.get_embeddings(text))
    
    def get_langchain_embeddings(self) -> Embeddings:
        if self._langchain_embeddings is None:
            self._langchain_embeddings = CustomEmbeddings(self)
        return self._langchain_embeddings

_embedding_service = None

async def get_embedding_service():
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service