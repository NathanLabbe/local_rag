# Document RAG Chat System

A lightweight document chat system with RAG (Retrieval-Augmented Generation) architecture that runs locally with minimal hardware requirements. Ask questions about your documents and get contextually relevant answers.

## Key Features

- **Chat with your documents**: Ask questions in natural language about your uploaded files
- **Lightweight**: Uses efficient models that can run on consumer hardware
- **RAG Architecture**: Combines document retrieval with language model generation
- **Easy document management**: Upload text/PDF files or import from Google Drive
- **Customizable settings**: Change models, system prompts, and retrieval behavior
- **Responsive UI**: Works on desktop and mobile devices

## What is RAG?

RAG (Retrieval-Augmented Generation) enhances LLM responses by first retrieving relevant information from your documents, then using this context to generate accurate answers. This approach gives you:

- **More accurate responses**: Based on your actual documents
- **Reduced hallucinations**: Grounded in real content
- **Source attribution**: See which documents contributed to the answer
- **Lower compute requirements**: Efficient processing of large document collections

## System Requirements

- Docker or Python 3.9+
- [Ollama](https://ollama.ai/) for running local LLMs
- 8GB+ RAM recommended (depends on chosen model)
- 10GB+ disk space for document storage and embeddings

## Quick Setup

1. **Install Ollama and download a lightweight model**
   ```bash
   # Install from https://ollama.ai/
   ollama pull phi3:3.8b   # Recommended for most systems
   # Or try other models like: llama3, mistral, etc.
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   # Access at http://localhost:8000
   ```

3. **First-time setup**
   - Upload some documents to start your knowledge base
   - Configure your settings (optional)
   - Start asking questions!

## Usage Guide

### Document Management

- **Upload files**: Support for text (.txt) and PDF (.pdf) files
- **Google Drive integration**: Import documents directly from your Drive
- **Document list**: See all imported documents with chunk counts
- **Delete documents**: Remove documents you no longer need

### Chat Interface

- **Ask questions**: Type your query in the chat input
- **View sources**: See which parts of your documents were used to answer
- **Control settings**: Toggle between different modes:
  - **Full RAG** (default): Document retrieval + LLM generation
  - **Retrieval only**: Just see relevant document chunks
  - **Generation only**: Use LLM without document lookups

### Advanced Settings

- **System prompt**: Customize the behavior of the LLM
- **LLM model**: Switch between different Ollama models
- **Retrieval settings**: Control document search behavior

## How It Works

1. **Document processing**: 
   - Documents are split into chunks and embedded as vectors
   - These vectors are stored in a ChromaDB database

2. **Query processing**:
   - Your question is converted to a vector
   - Similar document chunks are retrieved
   - The LLM generates an answer using these chunks as context

3. **Response delivery**:
   - The answer is displayed along with source documents
   - Relevance scores help you understand which sources were most useful

## Technical Stack

- **Backend**: FastAPI with Python
- **Vector Database**: ChromaDB (local, no cloud dependency)
- **Embeddings**: sentence-transformers (all-MiniLM-L6-v2)
- **LLM**: Any model supported by Ollama
- **Frontend**: Simple HTML/JS with Pico CSS framework

## Customization

- Edit `.env` file or `app/config.py` to change:
  - Default LLM model
  - Embedding model
  - Chunk size and overlap
  - System prompt

## Troubleshooting

- **Model not loading**: Make sure Ollama is running and the specified model is installed
- **Slow responses**: Try a smaller model or reduce document chunk size
- **Out of memory**: Lower the model size or run on a machine with more RAM

---

Built for personal knowledge management and document exploration.