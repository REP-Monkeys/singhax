"""Hotel model for storing hotel booking data."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Integer, Numeric, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Hotel(Base):
    """Hotel model for hotel bookings."""

    __tablename__ = "hotels"

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
    
    # Hotel Details
    hotel_name = Column(String, nullable=True)
    hotel_chain = Column(String, nullable=True)
    star_rating = Column(Integer, nullable=True)
    
    # Location
    address_street = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_country = Column(String, nullable=True)
    address_postal_code = Column(String, nullable=True)
    address_full = Column(String, nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # Booking Dates
    check_in_date = Column(Date, nullable=True)
    check_in_time = Column(String, nullable=True)
    check_out_date = Column(Date, nullable=True)
    check_out_time = Column(String, nullable=True)
    nights_count = Column(Integer, nullable=True)
    
    # Room Details
    room_type = Column(String, nullable=True)
    number_of_rooms = Column(Integer, nullable=True)
    occupancy = Column(Integer, nullable=True)
    smoking_preference = Column(String, nullable=True)
    
    # Investment Value
    total_cost_amount = Column(Numeric(10, 2), nullable=True)
    total_cost_currency = Column(String(3), nullable=True)
    per_night_cost_amount = Column(Numeric(10, 2), nullable=True)
    per_night_cost_currency = Column(String(3), nullable=True)
    deposit_paid_amount = Column(Numeric(10, 2), nullable=True)
    deposit_paid_currency = Column(String(3), nullable=True)
    is_refundable = Column(Boolean, nullable=True)
    cancellation_policy = Column(Text, nullable=True)
    
    # Booking Reference
    confirmation_number = Column(String, nullable=True)
    booking_id = Column(String, nullable=True)
    
    # Guests (JSONB)
    guests = Column(JSONB, nullable=True)
    
    # Full extracted data
    extracted_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="hotels")

    def __repr__(self):
        return f"<Hotel(id={self.id}, name={self.hotel_name}, check_in={self.check_in_date})>"

