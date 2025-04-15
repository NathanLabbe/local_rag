from typing import List, Dict, Any
import httpx
from langchain_weaviate import WeaviateVectorStore
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.messages import AIMessage, HumanMessage
import json

from app.config import settings
from app.database import get_client
from app.models import ChatMessage, ChatResponse
from app.services.embeddings_service import get_embedding_service, EmbeddingService

class ChatService:
    def __init__(self, weaviate_client, embedding_service: EmbeddingService):
        self.client = weaviate_client
        self.embedding_service = embedding_service
        self.vector_store = WeaviateVectorStore(
            client=weaviate_client,
            index_name=settings.collection_name,
            text_key="content",
            embedding=embedding_service.get_langchain_embeddings(),
            attributes=["document_id", "document_name", "chunk_id", "source"]
        )
    
    async def process_query(self, query: str, chat_history: List[ChatMessage] = None) -> ChatResponse:
        if chat_history is None:
            chat_history = []
            
        # Convert history to LangChain format
        lc_history = []
        for msg in chat_history:
            if msg.role == "user":
                lc_history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_history.append(AIMessage(content=msg.content))
                
        # Get relevant documents
        embedding = await self.embedding_service.get_embeddings(query)
        search_results = self.vector_store.similarity_search_by_vector_with_relevance_scores(
            embedding, k=5, score_threshold=0.7
        )
        
        # Extract relevant context
        contexts = []
        source_documents = []
        for doc, score in search_results:
            contexts.append(doc.page_content)
            source_documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": score
            })
            
        context_str = "\n\n".join(contexts)
        
        # Use Ollama for generating response
        prompt_template = """
        Answer the question based on the following context. If the context doesn't contain relevant information to answer the question, say so and don't make up an answer.

        Context:
        {context}

        Question: {question}
        
        Answer:
        """
        
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        # Call Ollama API directly
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.ollama_base_url}/api/generate",
                json={
                    "model": settings.ollama_model,
                    "prompt": prompt.format(context=context_str, question=query),
                    "stream": False
                }
            )
            
            if response.status_code != 200:
                raise Exception(f"Error from Ollama API: {response.text}")
                
            result = response.json()
            answer = result.get("response", "")
            
        return ChatResponse(
            answer=answer,
            source_documents=source_documents
        )

async def get_chat_service():
    client = await get_client()
    embedding_service = await get_embedding_service()
    return ChatService(client, embedding_service)