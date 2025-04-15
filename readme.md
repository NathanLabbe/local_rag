# Document RAG Chat System

A lightweight document chat system with RAG (Retrieval-Augmented Generation) architecture that runs entirely on your laptop with minimal GPU requirements.

## Features

- 💬 Chat interface to ask questions about your documents
- 📄 Document ingestion from local files or Google Drive
- 🔍 Semantic search across your document collection
- 🤖 Powered by a lightweight local LLM (through Ollama)
- 🔄 RAG architecture for accurate, contextual responses
- 🐳 Docker deployment for easy setup and portability

## System Architecture

This system consists of:

1. **FastAPI Backend**: Handles API requests, document processing, and chat interactions
2. **Weaviate Vector Database**: Stores document embeddings for efficient retrieval
3. **Ollama Integration**: Connects to a locally run LLM for generating responses
4. **Google Drive Integration**: Allows importing documents directly from Google Drive
5. **Web Interface**: User-friendly interface for document management and chatting

## Requirements

- Docker and Docker Compose
- Ollama (for running the LLM locally)
- Google Cloud Platform project with Google Drive API enabled (for Google Drive integration)

## Setup Instructions

### 1. Install Ollama and Download a Model

Ollama allows you to run large language models locally.

```bash
# Install Ollama (instructions at https://ollama.ai/)
# Then download a lightweight model
ollama pull llama3   # or another model like phi-2
```

### 2. Set Up Google Drive API (Optional, only if you want to import from Google Drive)

1. Create a project in [Google Cloud Console](https://console.cloud.google.com/)
2. Enable the Google Drive API
3. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download the credentials JSON file
4. Create a `credentials` directory in your project folder:
   ```bash
   mkdir -p credentials
   ```
5. Save the downloaded credentials file as `credentials/credentials.json`

### 3. Project Structure

Create the project structure as shown below:

```
project/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   └── documents.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── chat_service.py
│   │   ├── document_service.py
│   │   ├── embeddings_service.py
│   │   └── google_drive_service.py
│   └── static/
│       ├── css/
│       │   └── style.css
│       └── js/
│           └── main.js
└── templates/
    ├── base.html
    └── index.html
```

**Note**: The empty `__init__.py` files are needed to mark directories as Python packages.

### 4. Start the System

```bash
# Navigate to your project directory
cd project

# Start Docker containers
docker-compose up -d
```

The system will be available at http://localhost:8000

## Using the System

### Managing Documents

1. **Upload Documents**:
   - Use the file upload button in the sidebar to upload text files directly
   - Supported formats: `.txt`, `.pdf`, `.doc`, `.docx`

2. **Import from Google Drive** (if configured):
   - Click the "Import from Google Drive" button
   - Optionally enter a specific folder ID or leave empty to scan your entire Drive
   - Click "Import"
   - The first time you do this, you'll need to authorize the application

3. **View and Delete Documents**:
   - Your uploaded documents appear in the "Uploaded Documents" section
   - Click "Delete" next to a document to remove it from the system

### Chatting with Documents

1. Type your query in the chat input field at the bottom of the chat area
2. Press Enter or click "Send"
3. The system will:
   - Identify the most relevant document chunks for your query
   - Send those chunks as context to the LLM
   - Generate a response based on the document content
4. The response will include source references showing which document chunks were used

### Example Questions

- "What are the main points in the document about climate change?"
- "Can you summarize the key findings from the research paper?"
- "What did the quarterly report say about revenue growth?"
- "Find information about project timelines in my documents"

## Customization

### Changing the LLM Model

Edit the `settings.ollama_model` in `app/config.py` to use a different Ollama model:

```python
ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3")  # Change to "phi-2", "mistral", etc.
```

### Adjusting Document Chunking

For longer or shorter document chunks, modify the chunk settings in `app/config.py`:

```python
chunk_size: int = 1000  # Increase/decrease as needed
chunk_overlap: int = 200  # Adjust for more/less context overlap
```

### Using Different Embedding Model

The system uses `all-MiniLM-L6-v2` by default. For different embedding models, update the Docker Compose file to use a different transformers image, and update the embedding model in `app/config.py`.

## Troubleshooting

**Q: The system doesn't find relevant information in my documents.**  
A: Try adjusting the chunk size to be smaller for more precise retrieval.

**Q: Ollama connection fails.**  
A: Make sure Ollama is running on your host machine and the model is downloaded.

**Q: Google Drive integration doesn't work.**  
A: Verify your Google credentials and make sure the credentials file is correctly placed in the credentials directory.

## Technical Details

- **Vector Embeddings**: Document chunks are converted to embeddings using the all-MiniLM-L6-v2 model
- **RAG Architecture**: Combines retrieval from vector database with generation from LLM
- **Docker Deployment**: Makes setup easy across different environments

## Security Notes

- This system is designed for local development and personal use
- The Google Drive integration uses OAuth 2.0 for authentication
- No document data is sent to external services (all processing happens locally)