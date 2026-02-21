
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import os

from app.config import settings
from app.database import init_db
from app.api import auth, documents, chat, flashcards, websocket





app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION, 
    description="AI-powered study assistant with RAG and Pinecone",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",")] if settings.ALLOWED_ORIGINS else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.options("/{rest_of_path:path}")
async def preflight_handler(request: Request, rest_of_path: str):
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )


@app.on_event("startup")
def on_startup():
    """Initialize required directories and validate config."""
    print("🚀 Starting up StudyAI API...")

    init_db()
    print("✅ Database tables ready")

    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    print(f"✅ Uploads directory ready: {settings.UPLOAD_DIRECTORY}")

    if not settings.PINECONE_API_KEY:
        print("WARNING: PINECONE_API_KEY not set!")
    else:
        print(f"Pinecone configured: {settings.PINECONE_INDEX_NAME}")

    print("Application startup complete!")


app.include_router(auth.router, prefix=settings.API_V1_PREFIX, tags=["Authentication"])
app.include_router(documents.router, prefix=settings.API_V1_PREFIX, tags=["Documents"])
app.include_router(chat.router, prefix=settings.API_V1_PREFIX, tags=["Chat & RAG"])
app.include_router(flashcards.router, prefix=settings.API_V1_PREFIX)
app.include_router(websocket.router, prefix=settings.API_V1_PREFIX, tags=["WebSocket"])  


@app.get("/", tags=["Root"])
def root():
    """Welcome endpoint with API information."""
    return {
        "message": "Welcome to StudyAI API!",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "status": "healthy",
        "vector_db": "Pinecone",
        "features": [
            "PDF upload and processing",
            "AI-powered Q&A with RAG",
            "Flashcard generation",
            "Spaced repetition learning",
            "Pinecone vector search"
        ]
    }

@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint for monitoring and CI/CD."""
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "database": "connected",
        "vector_db": "pinecone",
        "message": "StudyAI API is running!"
    }