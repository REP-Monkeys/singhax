"""Visa model for storing visa application data."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Integer, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Visa(Base):
    """Visa model for visa applications."""

    __tablename__ = "visas"

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
    
    # Visa Details
    visa_type = Column(String, nullable=True)  # Tourist, Business, etc.
    destination_country = Column(String, nullable=True)
    entry_type = Column(String, nullable=True)  # Single, Multiple
    validity_start_date = Column(Date, nullable=True)
    validity_end_date = Column(Date, nullable=True)
    
    # Applicant Information
    applicant_first_name = Column(String, nullable=True)
    applicant_last_name = Column(String, nullable=True)
    applicant_full_name = Column(String, nullable=True)
    applicant_date_of_birth = Column(Date, nullable=True)
    applicant_age = Column(Integer, nullable=True)
    applicant_passport_number = Column(String, nullable=True)
    applicant_nationality = Column(String, nullable=True)
    
    # Trip Purpose
    trip_purpose_primary = Column(String, nullable=True)
    trip_purpose_detailed = Column(Text, nullable=True)
    is_business = Column(Boolean, nullable=True)
    is_medical_treatment = Column(Boolean, nullable=True)
    
    # Planned Trip
    intended_arrival_date = Column(Date, nullable=True)
    intended_departure_date = Column(Date, nullable=True)
    duration_days = Column(Integer, nullable=True)
    destination_cities = Column(JSONB, nullable=True)  # Array of city names
    
    # Accommodation Info
    has_hotel_booking = Column(Boolean, nullable=True)
    hotel_name = Column(String, nullable=True)
    hotel_address = Column(String, nullable=True)
    
    # Financial Support
    has_sufficient_funds = Column(Boolean, nullable=True)
    estimated_trip_cost_amount = Column(Numeric(10, 2), nullable=True)
    estimated_trip_cost_currency = Column(String(3), nullable=True)
    
    # Travel History
    has_previous_travel = Column(Boolean, nullable=True)
    previous_destinations = Column(JSONB, nullable=True)  # Array of destination names
    
    # Full extracted data
    extracted_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="visas")

    def __repr__(self):
        return f"<Visa(id={self.id}, type={self.visa_type}, destination={self.destination_country})>"

