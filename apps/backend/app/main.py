"""Main FastAPI application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db, create_tables
from app.routers import (
    auth_router,
    quotes_router,
    policies_router,
    claims_router,
    trips_router,
    rag_router,
    handoff_router,
    voice_router,
    chat_router
)

# Create FastAPI app
app = FastAPI(
    title=settings.project_name,
    description=settings.description,
    version=settings.version,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router, prefix=settings.api_v1_prefix)
app.include_router(quotes_router, prefix=settings.api_v1_prefix)
app.include_router(policies_router, prefix=settings.api_v1_prefix)
app.include_router(claims_router, prefix=settings.api_v1_prefix)
app.include_router(trips_router, prefix=settings.api_v1_prefix)
app.include_router(rag_router, prefix=settings.api_v1_prefix)
app.include_router(handoff_router, prefix=settings.api_v1_prefix)
app.include_router(voice_router, prefix=settings.api_v1_prefix)
app.include_router(chat_router, prefix=settings.api_v1_prefix)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    # Try to create database tables (graceful failure)
    try:
        create_tables()
        print("✓ Database tables initialized")
    except Exception as e:
        print(f"⚠️  Database connection failed (will retry on first request): {str(e)[:100]}")
        print("   Server will continue - chat will work without persistence")
    
    # TODO: Initialize other services (embeddings, etc.)
    print(f"🚀 {settings.project_name} v{settings.version} started")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.project_name}",
        "version": settings.version,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.version}
