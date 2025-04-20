import logging
import httpx
from typing import List, Dict, Any, Optional
from chromadb.errors import InvalidCollectionException
from app.config import settings
from app.database import get_client
from app.services.embeddings_service import get_embedding_service

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self, chroma_client, embedding_service):
        self.client = chroma_client
        self.embedding_service = embedding_service
        self.collection_name = settings.collection_name
        
        # Get or create the collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
        except InvalidCollectionException:
            self.collection = self.client.create_collection(name=self.collection_name)
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Alias for get_response to maintain compatibility with existing code"""
        return await self.get_response(query)
    
    async def get_response(self, query: str) -> Dict[str, Any]:
        # Get query embedding
        query_embedding = await self.embedding_service.get_embeddings(query)
        
        # Query the collection for similar chunks
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=5,  # Get top 5 most relevant chunks
            include=["documents", "metadatas", "distances"]
        )
        
        # Process the results to extract context and sources
        context = ""
        sources = []
        
        if results and results["documents"] and len(results["documents"]) > 0:
            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0], results["metadatas"][0], results["distances"][0]
            )):
                # Add document to context
                context += f"\nChunk {i+1}:\n{doc}\n"
                
                # Add source info
                sources.append({
                    "document_name": metadata.get("document_name", "Unknown"),
                    "source": metadata.get("source", "Unknown"),
                    "relevance": 1 - distance  # Convert distance to relevance score
                })
        
        # If no context found
        if not context:
            return {
                "answer": "I couldn't find any relevant information in the documents to answer your question.",
                "sources": []
            }
            
        # Prepare the prompt for the LLM
        prompt = f"""
        Answer the following question based only on the provided context. If the context doesn't contain relevant information to answer the question, say so.
        
        Context:
        {context}
        
        Question: {query}
        
        Answer:
        """
            
        # Send to Ollama for response generation
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=240.0  # Increased timeout for LLM processing
                )
                
                if response.status_code == 200:
                    answer = response.json().get("response", "")
                    
                    # Add sources to the answer
                    if sources:
                        source_text = "\n\nSources:\n"
                        for src in sources:
                            source_text += f"- {src['document_name']} (Relevance: {src['relevance']:.2f})\n"
                        answer += source_text

                    return {
                        "answer": answer,
                        "sources": sources
                    }
                else:
                    logger.error(f"Error from Ollama API: {response.status_code}, {response.text}")
                    return {
                        "answer": "Sorry, there was an error generating a response.",
                        "sources": sources
                    }
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return {
                "answer": f"Error: {str(e)}",
                "sources": sources
            }

async def get_chat_service():
    client = await get_client()
    embedding_service = await get_embedding_service()
    return ChatService(client, embedding_service)