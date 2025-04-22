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
    
    async def get_response(self, query: str, use_llm: bool = True, skip_retrieval: bool = False) -> Dict[str, Any]:
        sources = []
        
        # Only perform retrieval if not skipping
        if not skip_retrieval:
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
                        "chunk_id": metadata.get("chunk_id", i),
                        "relevance": 1 - distance  # Convert distance to relevance score
                    })
        else:
            context = ""
        
        # If no context found and retrieval was attempted
        if not context and not skip_retrieval:
            return {
                "answer": "I couldn't find any relevant information in the documents to answer your question.",
                "sources": []
            }
        
        # If not using LLM, just return the retrieved documents
        if not use_llm:
            # Format documents as readable answer
            doc_answer = "Here are the most relevant documents for your query:\n\n"
            for i, source in enumerate(sources):
                doc_answer += f"Document {i+1}: {source['document_name']}\n"
                # Get the actual text content
                doc_content = results["documents"][0][i]
                # Truncate if too long for display
                if len(doc_content) > 500:
                    doc_content = doc_content[:500] + "..."
                doc_answer += f"Content: {doc_content}\n\n"
            
            return {
                "answer": doc_answer if sources else "No relevant documents found.",
                "sources": sources
            }
            
        # If using LLM, prepare the prompt
        system_prompt = settings.system_prompt or """
        You are a helpful assistant that answers questions based on the provided documents.
        If the documents contain the information, use it to provide accurate answers.
        If the information is not in the documents but you know the answer, you can provide it.
        If you're unsure, indicate that you don't have enough information.
        Always be truthful, helpful, and concise.
        """
        
        # Prepare the prompt for the LLM with system prompt
        if context:
            prompt = f"""
            {system_prompt}
            
            Answer the following question. Use the provided context if relevant.
            
            Context:
            {context}
            
            Question: {query}
            
            Answer:
            """
        else:
            prompt = f"""
            {system_prompt}
            
            Answer the following question based on your knowledge. If you don't know, say so.
            
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