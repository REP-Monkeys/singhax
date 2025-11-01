"""Database models package."""

# Import all models to ensure they are registered with SQLAlchemy
from .user import User
from .traveler import Traveler
from .trip import Trip
from .quote import Quote
from .policy import Policy
from .claim import Claim
from .chat_history import ChatHistory
from .audit_log import AuditLog
from .rag_document import RagDocument
from .payment import Payment
from .flight import Flight
from .hotel import Hotel
from .visa import Visa
from .itinerary import Itinerary

__all__ = [
    "User",
    "Traveler", 
    "Trip",
    "Quote",
    "Policy",
    "Claim",
    "ChatHistory",
    "AuditLog",
    "RagDocument",
    "Payment",
    "Flight",
    "Hotel",
    "Visa",
    "Itinerary",
]
