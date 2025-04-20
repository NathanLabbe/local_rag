import chromadb
import os
import logging
from chromadb.config import Settings as ChromaSettings
from app.config import settings

logger = logging.getLogger(__name__)

# Global client for ChromaDB
_client = None

async def init_db():
    """Initialize the ChromaDB client and create the collection if needed"""
    global _client
    
    try:
        # Create the directory for ChromaDB persistence if it doesn't exist
        os.makedirs(settings.chroma_persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        _client = chromadb.PersistentClient(path=settings.chroma_persist_directory)
        
        # Create the collection - this will either create a new one or get an existing one
        try:
            # Try to get the collection first
            collection = _client.get_collection(name=settings.collection_name)
            logger.info(f"Using existing collection: {settings.collection_name}")
        except Exception:
            # If it doesn't exist, create it
            collection = _client.create_collection(name=settings.collection_name)
            logger.info(f"Created new collection: {settings.collection_name}")
            
        logger.info("ChromaDB initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {str(e)}")
        raise

async def get_client():
    """Return the ChromaDB client instance"""
    global _client
    if _client is None:
        await init_db()
    return _client