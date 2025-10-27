"""API routers package."""

from .auth import router as auth_router
from .quotes import router as quotes_router
from .policies import router as policies_router
from .claims import router as claims_router
from .trips import router as trips_router
from .rag import router as rag_router
from .handoff import router as handoff_router
from .voice import router as voice_router
from .chat import router as chat_router

__all__ = [
    "auth_router",
    "quotes_router",
    "policies_router",
    "claims_router",
    "trips_router",
    "rag_router",
    "handoff_router",
    "voice_router",
    "chat_router",
]
