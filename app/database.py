import weaviate
from weaviate.connect import ConnectionParams, ProtocolParams
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Global client
client = None

async def get_client():
    global client
    if client is None:
        client = weaviate.connect_to_custom(
            http_host=f"{settings.weaviate_host}",
            http_port=f"{settings.weaviate_port}",
            http_secure=False,
            grpc_host=f"{settings.weaviate_host}:{settings.weaviate_grpc_port}",
            grpc_port=f"{settings.weaviate_grpc_port}",
            grpc_secure=False,
            skip_init_checks=True
        ),
    return client

async def init_db():
    try:
        client = await get_client()

        # Check if schema exists, if not create it
        collections = client.collections.list_all()
        collection_names = [c.name for c in collections]

        if settings.collection_name not in collection_names:
            logger.info(f"Creating schema for {settings.collection_name}")

            # Create collection using v4 API
            collection = client.collections.create(
                name=settings.collection_name,
                vectorizer_config=weaviate.classes.config.Configure.Vectorizer.text2vec_transformers(),  # Use the transformers vectorizer
                properties=[
                    weaviate.classes.config.Property(
                        name="content",
                        data_type=weaviate.classes.config.DataType.TEXT,
                    ),
                    weaviate.classes.config.Property(
                        name="document_id",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        indexing=weaviate.classes.config.Configure.Property.Indexing(
                            filterable=True
                        ),
                    ),
                    weaviate.classes.config.Property(
                        name="document_name",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        indexing=weaviate.classes.config.Configure.Property.Indexing(
                            filterable=True
                        ),
                    ),
                    weaviate.classes.config.Property(
                        name="chunk_id",
                        data_type=weaviate.classes.config.DataType.INT,
                        indexing=weaviate.classes.config.Configure.Property.Indexing(
                            filterable=True
                        ),
                    ),
                    weaviate.classes.config.Property(
                        name="source",
                        data_type=weaviate.classes.config.DataType.TEXT,
                        indexing=weaviate.classes.config.Configure.Property.Indexing(
                            filterable=True
                        ),
                    ),
                ]
            )
            logger.info(f"Schema created for {settings.collection_name}")
        else:
            logger.info(f"Schema already exists for {settings.collection_name}")

    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise e

# Explicitly export the init_db function
__all__ = ['get_client', 'init_db']
