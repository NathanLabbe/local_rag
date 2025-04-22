# Document RAG Chat System

A lightweight document chat system with RAG (Retrieval-Augmented Generation) architecture that runs on your laptop with minimal hardware requirements.

## What is RAG?

RAG (Retrieval-Augmented Generation) is a method that enhances language models by retrieving relevant information from a database before generating responses. This allows the model to provide more accurate and contextual answers based on your documents.

## Features

- 💬 Simple chat interface to ask questions about your documents
- 📄 Document upload from local files (.txt, .pdf)
- 📁 Import documents from Google Drive (optional)
- 🔍 Semantic search across your document collection
- 🤖 Powered by a lightweight local LLM through Ollama
- 🐳 Docker deployment for easy setup

## How It Works

1. **Upload Documents**: Add your documents to the system through file upload or Google Drive
2. **Ask Questions**: Type your question in the chat interface
3. **Get Answers**: The system retrieves relevant information from your documents and generates answers

The system provides two main modes:
- **Retrieval + Generation**: Finds relevant document chunks and uses them to inform the LLM's response (RAG)
- **Generation Only**: Uses only the LLM to answer without looking up documents (when you uncheck "Use document retrieval")

## Setup Instructions

### 1. Install Ollama and Download a Model

```bash
# Install Ollama from https://ollama.ai/
# Then download a lightweight model
ollama pull phi3:3.8b   # or another model like llama3
```

### 2. Set Up Google Drive API (Optional)

1. Create a project in Google Cloud Console
2. Enable the Google Drive API
3. Create OAuth 2.0 credentials (Desktop app)
4. Download and save as `credentials/credentials.json`

### 3. Start the System

```bash
# Navigate to your project directory
docker-compose up -d
```

Access the system at http://localhost:8000

## Using the System

### Document Management

- **Upload**: Use the file upload button to add text or PDF files
- **Import from Drive**: Click "Import from Google Drive" (if configured)
- **Delete**: Remove documents you no longer need

### Chat Settings

- **Use LLM for responses**: Enable/disable using the language model
- **Use document retrieval**: Control whether to look up information from your documents

### Examples

- "What are the key points in my project proposal?"
- "Summarize the financial data from last quarter"
- "What were the conclusions of the research paper?"

## Customization

Edit `app/config.py` to change:
- The Ollama model (e.g., phi3:3.8b, llama3)
- Document chunking settings
- System prompt for the LLM

## Technical Details

- **Backend**: FastAPI with Python
- **Vector Database**: ChromaDB for embedding storage
- **Embeddings**: sentence-transformers for converting text to vectors
- **LLM**: Ollama for local language model inference