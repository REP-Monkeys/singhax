"""Main FastAPI application."""

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pathlib import Path

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
    chat_router,
    payments_router
)
from app.routers.destination_images import router as destination_images_router

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
app.include_router(payments_router, prefix=settings.api_v1_prefix)
app.include_router(destination_images_router, prefix=settings.api_v1_prefix)

# Mount static files for destination images
uploads_dir = Path("apps/backend/uploads")
if uploads_dir.exists():
    app.mount(
        "/static/uploads",
        StaticFiles(directory=str(uploads_dir)),
        name="uploads"
    )


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
    
    # Debug: Print Supabase configuration status
    print(f"[CONFIG] Supabase URL configured: {settings.supabase_url is not None}")
    print(f"[CONFIG] Supabase anon key configured: {settings.supabase_anon_key is not None}")
    print(f"[CONFIG] Supabase service role key configured: {settings.supabase_service_role_key is not None}")
    print(f"[CONFIG] Supabase JWT secret configured: {settings.supabase_jwt_secret is not None}")
    if settings.supabase_service_role_key:
        print(f"[CONFIG] Service role key starts with: {settings.supabase_service_role_key[:30]}...")
    if settings.supabase_jwt_secret:
        print(f"[CONFIG] JWT secret starts with: {settings.supabase_jwt_secret[:30]}...")
    
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
