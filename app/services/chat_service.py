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
    
    async def get_response(self, 
                        query: str, 
                        history: List[Dict[str, Any]] = None, 
                        use_llm: bool = True, 
                        skip_retrieval: bool = False) -> Dict[str, Any]:
        """
        Generate a response to a user query based on document retrieval and/or LLM generation.
        
        Args:
            query: The user's query string
            history: Optional chat history for context
            use_llm: Whether to use the LLM for response generation
            skip_retrieval: Whether to skip document retrieval step
            
        Returns:
            Dictionary containing the answer and source information
        """
        if history is None:
            history = []
            
        sources = []
        context = ""
        
        # Perform retrieval if not skipping
        if not skip_retrieval:
            sources, context = await self._retrieve_relevant_documents(query)
            
            # If no context found and retrieval was attempted
            if not context:
                if not use_llm:
                    return {
                        "answer": "I couldn't find any relevant information in the documents to answer your question.",
                        "sources": []
                    }
                # If using LLM, we'll continue with empty context
        
        # If not using LLM, just return the retrieved documents
        if not use_llm:
            return self._format_document_answer(sources, context)
            
        # If using LLM, get response from model
        answer = await self._get_llm_response(query, context, history)
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    async def _retrieve_relevant_documents(self, query: str) -> tuple:
        """Retrieve relevant documents from the vector store"""
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
        
        if results and results["documents"] and len(results["documents"][0]) > 0:
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
                
        return sources, context
    
    def _format_document_answer(self, sources, context) -> Dict[str, Any]:
        """Format retrieved documents as a readable answer"""
        if not sources:
            return {
                "answer": "No relevant documents found.",
                "sources": []
            }
            
        doc_answer = "Here are the most relevant documents for your query:\n\n"
        for i, source in enumerate(sources):
            doc_answer += f"Document {i+1}: {source['document_name']}\n"
            
            # Extract corresponding content
            chunk_content = context.split(f"Chunk {i+1}:\n")[1].split("\n\nChunk")[0]
            
            # Truncate if too long for display
            if len(chunk_content) > 500:
                chunk_content = chunk_content[:500] + "..."
                
            doc_answer += f"Content: {chunk_content}\n\n"
        
        return {
            "answer": doc_answer,
            "sources": sources
        }
    
    async def _get_llm_response(self, query: str, context: str, history: List[Dict[str, Any]]) -> str:
        """Get response from the LLM"""
        system_prompt = settings.system_prompt or """
        You are a helpful assistant that answers questions based on the provided documents.
        If the documents contain the information, use it to provide accurate answers.
        If the information is not in the documents but you know the answer, you can provide it.
        If you're unsure, indicate that you don't have enough information.
        Always be truthful, helpful, and concise.
        """
        
        # Format chat history for the prompt
        history_text = ""
        if history:
            history_text = "Previous conversation:\n"
            for msg in history:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                history_text += f"{role.capitalize()}: {content}\n"
            history_text += "\n"
        
        # Prepare the prompt for the LLM
        if context:
            prompt = f"""
            {system_prompt}
            
            {history_text}
            Answer the following question. Use the provided context if relevant.
            
            Context:
            {context}
            
            Question: {query}
            
            Answer:
            """
        else:
            prompt = f"""
            {system_prompt}
            
            {history_text}
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
                    return response.json().get("response", "")
                else:
                    logger.error(f"Error from Ollama API: {response.status_code}, {response.text}")
                    return "Sorry, there was an error generating a response."
        except Exception as e:
            logger.error(f"Error calling Ollama API: {str(e)}")
            return f"Error: {str(e)}"

async def get_chat_service():
    client = await get_client()
    embedding_service = await get_embedding_service()
    return ChatService(client, embedding_service)