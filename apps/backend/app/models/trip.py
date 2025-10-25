"""Trip model."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime
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
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    destinations = Column(ARRAY(String), nullable=False)  # List of country/city codes
    flight_refs = Column(JSONB, default=list)  # Flight booking references
    accommodation_refs = Column(JSONB, default=list)  # Hotel/booking references
    total_cost = Column(String, nullable=True)  # Trip cost estimate
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="trips")
    quotes = relationship("Quote", back_populates="trip")
    
    def __repr__(self):
        return f"<Trip(id={self.id}, destinations={self.destinations}, start={self.start_date})>"
