import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.config import settings
from app.models import DocumentResponse, DocumentCreate
from app.database import get_client
from app.services.embeddings_service import get_embedding_service, EmbeddingService

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, weaviate_client, embedding_service: EmbeddingService):
        self.client = weaviate_client
        self.embedding_service = embedding_service
        self.collection_name = settings.collection_name
        
        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            length_function=len
        )
    
    async def process_document(
        self, content: str, document_name: str, source: str
    ) -> DocumentResponse:
        document_id = str(uuid.uuid4())
        
        # Split the document into chunks
        chunks = self.text_splitter.split_text(content)
        
        # Create embeddings for each chunk and store them
        for i, chunk in enumerate(chunks):
            embedding = await self.embedding_service.get_embeddings(chunk)
            
            # Store in Weaviate
            self.client.data_object.create(
                data_object={
                    "content": chunk,
                    "document_id": document_id,
                    "document_name": document_name,
                    "chunk_id": i,
                    "source": source
                },
                class_name=self.collection_name,
                vector=embedding
            )
            
        # Return document info
        return DocumentResponse(
            document_id=document_id,
            document_name=document_name,
            source=source,
            chunk_count=len(chunks),
            created_at=datetime.now()
        )
    
    async def list_documents(self) -> List[DocumentResponse]:
        # Query unique documents by document_id
        query = f"""
        {{
            Aggregate {{
                {self.collection_name} {{
                    groupby {{
                        path: ["document_id"]
                        fields: [
                            {{ name: "document_name", path: ["document_name"] }},
                            {{ name: "source", path: ["source"] }},
                            {{ name: "chunk_count", operator: count }}
                        ]
                    }}
                }}
            }}
        }}
        """
        
        result = self.client.query.raw(query)
        
        documents = []
        try:
            groups = result["data"]["Aggregate"][self.collection_name]
            
            for group in groups:
                groupby_values = group["groupby"]
                document_id = None
                document_name = None
                source = None
                chunk_count = 0
                
                for value in groupby_values:
                    if "path" in value and value["path"][0] == "document_id":
                        document_id = value["value"]
                    if "fields" in value:
                        for field in value["fields"]:
                            if field.get("name") == "document_name":
                                document_name = field.get("value")
                            elif field.get("name") == "source":
                                source = field.get("value")
                            elif field.get("name") == "chunk_count":
                                chunk_count = field.get("value")
                
                if document_id and document_name and source:
                    documents.append(
                        DocumentResponse(
                            document_id=document_id,
                            document_name=document_name,
                            source=source,
                            chunk_count=chunk_count,
                            created_at=datetime.now()  # We don't have creation time stored
                        )
                    )
        except Exception as e:
            logger.error(f"Error processing document list: {str(e)}")
            # Return empty list on error
            
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        try:
            # Create a batch process for deleting objects
            result = (
                self.client.batch.delete_objects()
                .with_class_name(self.collection_name)
                .with_where({
                    "path": ["document_id"],
                    "operator": "Equal",
                    "valueString": document_id
                })
                .do()
            )
            
            # Check if anything was deleted
            return result.get('results', {}).get('successful', 0) > 0
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False

async def get_document_service():
    client = await get_client()
    embedding_service = await get_embedding_service()
    return DocumentService(client, embedding_service)