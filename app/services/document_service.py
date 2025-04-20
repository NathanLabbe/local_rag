import uuid
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from chromadb.errors import InvalidCollectionException
import fitz 
from app.config import settings
from app.models import DocumentResponse, DocumentCreate
from app.database import get_client
from app.services.embeddings_service import get_embedding_service, EmbeddingService

logger = logging.getLogger(__name__)

class DocumentService:
    def __init__(self, chroma_client, embedding_service: EmbeddingService):
        self.client = chroma_client
        self.embedding_service = embedding_service
        self.collection_name = settings.collection_name
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except InvalidCollectionException:
            self.collection = self.client.create_collection(name=self.collection_name)
        
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
        
        # Create embeddings and metadata for each chunk
        chunk_ids = []
        embeddings = []
        metadatas = []
        documents = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_{i}"
            chunk_ids.append(chunk_id)
            
            # Get embedding
            embedding = await self.embedding_service.get_embeddings(chunk)
            embeddings.append(embedding)
            
            # Create metadata
            metadata = {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_id": i,
                "source": source,
                "created_at": datetime.now().isoformat()
            }
            metadatas.append(metadata)
            
            # Add the document text
            documents.append(chunk)
        
        # Add all chunks to the collection at once
        self.collection.add(
            ids=chunk_ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents
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
        # Query all items in the collection
        result = self.collection.get()
        
        # Group by document_id to get unique documents
        document_map = {}
        
        if result and result['metadatas']:
            for metadata in result['metadatas']:
                doc_id = metadata.get('document_id')
                if doc_id and doc_id not in document_map:
                    document_map[doc_id] = {
                        'document_name': metadata.get('document_name', 'Unknown'),
                        'source': metadata.get('source', 'Unknown'),
                        'chunks': 1
                    }
                elif doc_id:
                    document_map[doc_id]['chunks'] += 1
        
        # Convert to DocumentResponse objects
        documents = []
        for doc_id, doc_info in document_map.items():
            documents.append(
                DocumentResponse(
                    document_id=doc_id,
                    document_name=doc_info['document_name'],
                    source=doc_info['source'],
                    chunk_count=doc_info['chunks'],
                    created_at=datetime.now()  # We don't have creation time stored
                )
            )
            
        return documents
    
    async def delete_document(self, document_id: str) -> bool:
        try:
            # Get all items that match this document_id
            result = self.collection.get(
                where={"document_id": document_id}
            )
            
            # If we found items, delete them by ID
            if result and result['ids']:
                self.collection.delete(ids=result['ids'])
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {str(e)}")
            return False
    
    async def process_uploaded_file(
        self, file_path: str, document_name: str, source: str
    ) -> DocumentResponse:
        """Process an uploaded file (txt or pdf)"""
        # Detect file extension
        if document_name.lower().endswith(".pdf"):
            text = self._extract_text_from_pdf(file_path)
        elif document_name.lower().endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        else:
            raise ValueError("Unsupported file type. Only .txt and .pdf are supported.")
        
        return await self.process_document(text, document_name, source)
    
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF"""
        doc = fitz.open(file_path)
        text = ""
        for page in doc:
            text += page.get_text()
        return text

async def get_document_service():
    client = await get_client()
    embedding_service = await get_embedding_service()
    return DocumentService(client, embedding_service)