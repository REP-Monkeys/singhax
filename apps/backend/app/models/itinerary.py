"""Itinerary model for storing itinerary data."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Itinerary(Base):
    """Itinerary model for travel itineraries."""

    __tablename__ = "itineraries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, nullable=True, index=True)
    
    # Metadata
    source_filename = Column(String, nullable=True)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    json_file_path = Column(String, nullable=True)
    
    # File Storage
    file_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=True)
    file_content_type = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)
    
    # Trip Overview
    trip_title = Column(String, nullable=True)
    duration_days = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    
    # Destinations (stored as JSONB array)
    destinations = Column(JSONB, nullable=True)  # Array of destination objects
    
    # Activities (stored as JSONB array)
    activities = Column(JSONB, nullable=True)  # Array of activity objects
    
    # Adventure Sports Detection
    has_adventure_sports = Column(Boolean, nullable=True)
    adventure_sports_activities = Column(JSONB, nullable=True)  # Array of adventure sport objects
    
    # Risk Factors
    has_extreme_sports = Column(Boolean, nullable=True)
    has_water_sports = Column(Boolean, nullable=True)
    has_winter_sports = Column(Boolean, nullable=True)
    has_high_altitude_activities = Column(Boolean, nullable=True)
    has_motorized_sports = Column(Boolean, nullable=True)
    is_group_travel = Column(Boolean, nullable=True)
    has_remote_locations = Column(Boolean, nullable=True)
    has_political_risk_destinations = Column(Boolean, nullable=True)
    
    # Trip Characteristics
    is_group_tour = Column(Boolean, nullable=True)
    is_solo_travel = Column(Boolean, nullable=True)
    group_size = Column(Integer, nullable=True)
    includes_children = Column(Boolean, nullable=True)
    includes_seniors = Column(Boolean, nullable=True)  # 70+
    
    # Trip Structure
    trip_type = Column(String, nullable=True)  # single_return, multi_city, annual
    number_of_destinations = Column(Integer, nullable=True)
    requires_internal_travel = Column(Boolean, nullable=True)
    internal_transport = Column(JSONB, nullable=True)  # Array of transport methods
    
    # Travelers (stored as JSONB)
    travelers = Column(JSONB, nullable=True)  # Array of traveler objects
    
    # Full extracted data
    extracted_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="itineraries")

    def __repr__(self):
        return f"<Itinerary(id={self.id}, title={self.trip_title}, start_date={self.start_date})>"

