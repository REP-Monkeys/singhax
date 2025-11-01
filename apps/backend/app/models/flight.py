"""Flight model for storing flight confirmation data."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class Flight(Base):
    """Flight model for flight confirmations."""

    __tablename__ = "flights"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String, nullable=True, index=True)
    
    # Metadata
    source_filename = Column(String, nullable=True)
    extracted_at = Column(DateTime(timezone=True), server_default=func.now())
    json_file_path = Column(String, nullable=True)
    
    # File Storage
    file_path = Column(String, nullable=True)  # Path to stored document file on filesystem
    file_size = Column(Integer, nullable=True)  # File size in bytes
    file_content_type = Column(String, nullable=True)  # MIME type (e.g., "application/pdf")
    original_filename = Column(String, nullable=True)  # Original uploaded filename
    
    # Trip Type
    trip_type = Column(String, nullable=True)  # "one_way" or "return"
    
    # Airline Information (backward compatibility - uses outbound airline)
    airline_name = Column(String, nullable=True)
    airline_code = Column(String, nullable=True)
    
    # Outbound Airline Information
    outbound_airline_name = Column(String, nullable=True)
    outbound_airline_code = Column(String, nullable=True)
    
    # Inbound Airline Information (nullable for one-way trips)
    inbound_airline_name = Column(String, nullable=True)
    inbound_airline_code = Column(String, nullable=True)
    
    # Flight Details
    departure_date = Column(Date, nullable=True)
    departure_time = Column(String, nullable=True)
    departure_airport_code = Column(String, nullable=True)
    departure_airport_name = Column(String, nullable=True)
    
    return_date = Column(Date, nullable=True)
    return_time = Column(String, nullable=True)
    return_airport_code = Column(String, nullable=True)
    return_airport_name = Column(String, nullable=True)
    
    flight_number_outbound = Column(String, nullable=True)
    flight_number_inbound = Column(String, nullable=True)
    
    # Destination
    destination_country = Column(String, nullable=True)
    destination_city = Column(String, nullable=True)
    destination_airport_code = Column(String, nullable=True)
    
    # Booking Reference
    pnr = Column(String, nullable=True)
    booking_number = Column(String, nullable=True)
    
    # Trip Information
    trip_duration_days = Column(Integer, nullable=True)
    total_cost_amount = Column(Numeric(10, 2), nullable=True)
    total_cost_currency = Column(String(3), nullable=True)
    
    # Travelers (JSONB)
    travelers = Column(JSONB, nullable=True)
    
    # Full extracted data
    extracted_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="flights")

    def __repr__(self):
        return f"<Flight(id={self.id}, airline={self.airline_name}, departure={self.departure_date})>"

