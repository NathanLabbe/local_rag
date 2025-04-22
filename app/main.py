from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from pathlib import Path

from app.routes import chat, documents, settings
from app.database import init_db

# Define lifespan first
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("Initializing database...")
    try:
        await init_db()
        print("Database initialized successfully!")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise e
    yield
    # Shutdown logic (if any)

# Create FastAPI app with lifespan
app = FastAPI(title="Document RAG Chat", lifespan=lifespan)

# Mount static files
static_path = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include routers
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(settings.router)  # Added settings router

@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)