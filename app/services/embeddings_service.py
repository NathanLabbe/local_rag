import logging
from typing import List, Dict, Any, Optional
from langchain_community.embeddings import HuggingFaceEmbeddings
from app.config import settings

logger = logging.getLogger(__name__)

# Global embedding service
_embedding_service = None

class EmbeddingService:
    def __init__(self):
        # Initialize the embedding model
        self.model = HuggingFaceEmbeddings(model_name=f"sentence-transformers/{settings.embedding_model}")
    
    async def get_embeddings(self, text: str) -> List[float]:
        """Get embeddings for a text string"""
        try:
            # HuggingFaceEmbeddings returns list of list, we need the first item
            embeddings = self.model.embed_documents([text])
            return embeddings[0]
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            raise

async def get_embedding_service():
    """Get or create the embedding service"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service