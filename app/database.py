import weaviate
from app.config import settings
import asyncio
import logging

logger = logging.getLogger(__name__)

# Global client
client = None

async def get_client():
    global client
    if client is None:
        client = weaviate.Client(url=settings.weaviate_url)
    return client

async def init_db():
    client = await get_client()
    
    # Check if schema exists, if not create it
    try:
        schema = client.schema.get()
        class_names = [c['class'] for c in schema['classes']] if 'classes' in schema else []
        
        if settings.collection_name not in class_names:
            logger.info(f"Creating schema for {settings.collection_name}")
            
            class_obj = {
                "class": settings.collection_name,
                "vectorizer": "none",  # We'll provide our own vectors
                "properties": [
                    {
                        "name": "content",
                        "dataType": ["text"],
                    },
                    {
                        "name": "document_id",
                        "dataType": ["string"],
                        "indexFilterable": True,
                    },
                    {
                        "name": "document_name",
                        "dataType": ["string"],
                        "indexFilterable": True,
                    },
                    {
                        "name": "chunk_id",
                        "dataType": ["int"],
                        "indexFilterable": True,
                    },
                    {
                        "name": "source",
                        "dataType": ["string"],
                        "indexFilterable": True,
                    },
                ]
            }
            
            client.schema.create_class(class_obj)
            logger.info(f"Schema created for {settings.collection_name}")
        else:
            logger.info(f"Schema already exists for {settings.collection_name}")
            
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise e