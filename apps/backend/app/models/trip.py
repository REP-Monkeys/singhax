"""Trip model."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Trip(Base):
    """Trip model for travel itineraries."""

    __tablename__ = "trips"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    session_id = Column(String, nullable=True, unique=True, index=True)  # Link to chat session
    status = Column(String, default="draft")  # draft, ongoing, completed, past
    start_date = Column(Date, nullable=True)  # Made nullable for draft trips
    end_date = Column(Date, nullable=True)  # Made nullable for draft trips
    destinations = Column(ARRAY(String), default=list)  # List of country/city codes
    travelers_count = Column(Integer, default=1)  # Number of travelers
    flight_refs = Column(JSONB, default=list)  # Flight booking references
    accommodation_refs = Column(JSONB, default=list)  # Hotel/booking references
    total_cost = Column(String, nullable=True)  # Trip cost estimate
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="trips")
    quotes = relationship("Quote", back_populates="trip")

    def __repr__(self):
        return f"<Trip(id={self.id}, destinations={self.destinations}, status={self.status})>"
