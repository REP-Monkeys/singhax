# PDF Upload Database Storage - Implementation Proposal

## Overview

This document proposes the implementation of database storage for extracted PDF document information. Currently, PDFs are uploaded, parsed via OCR/LLM, and saved as JSON files. This proposal adds database persistence and proper document type validation.

---

## 1. Document Type Validation & Rejection

### Current Behavior
- Documents are detected via `DocumentTypeDetector`
- If type is "unknown", extraction still proceeds but with minimal data
- No explicit rejection message for irrelevant documents

### Proposed Changes

**Location:** `apps/backend/app/services/ocr/document_detector.py` and `apps/backend/app/routers/chat.py`

1. **Enhance Document Type Detection:**
   - After detection, explicitly check if type is one of: `flight_confirmation`, `hotel_booking`, `itinerary`, `visa_application`
   - If type is "unknown" or not in the allowed list, reject immediately

2. **Rejection Logic:**
   - In `upload_image` endpoint, after `json_extractor.extract()`:
     - Check if `extracted_json.get("document_type") == "unknown"`
     - If unknown, return HTTP 400 with message: "Please only upload relevant documents! Accepted types: flight confirmation, hotel booking, itinerary, or visa application."

3. **Update JSONExtractor:**
   - Modify `_create_unknown_document_json()` to include a clearer error message
   - Ensure the detector returns "unknown" for any non-matching document types

---

## 2. Database Schema Design

### Table: `flights`

Stores extracted flight confirmation data.

```sql
CREATE TABLE flights (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR,  -- Link to chat session
    
    -- Metadata
    source_filename VARCHAR,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    json_file_path VARCHAR,  -- Path to saved JSON file
    
    -- Airline Information
    airline_name VARCHAR,
    airline_code VARCHAR,
    
    -- Flight Details
    departure_date DATE,
    departure_time VARCHAR,  -- Store as string (e.g., "14:30")
    departure_airport_code VARCHAR,
    departure_airport_name VARCHAR,
    
    return_date DATE,
    return_time VARCHAR,
    return_airport_code VARCHAR,
    return_airport_name VARCHAR,
    
    flight_number_outbound VARCHAR,
    flight_number_inbound VARCHAR,
    
    -- Destination
    destination_country VARCHAR,
    destination_city VARCHAR,
    destination_airport_code VARCHAR,
    
    -- Booking Reference
    pnr VARCHAR,
    booking_number VARCHAR,
    
    -- Trip Information
    trip_duration_days INTEGER,
    total_cost_amount NUMERIC(10, 2),
    total_cost_currency VARCHAR(3),
    
    -- Travelers (stored as JSONB for multiple travelers with ticket details)
    travelers JSONB,  -- Array of traveler objects with name, ticket details, costs
    
    -- Full extracted data (for reference/backup)
    extracted_data JSONB,  -- Store complete JSON structure
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes
    CONSTRAINT flights_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_flights_user_id ON flights(user_id);
CREATE INDEX idx_flights_session_id ON flights(session_id);
CREATE INDEX idx_flights_departure_date ON flights(departure_date);
```

### Table: `hotels`

Stores extracted hotel booking data.

```sql
CREATE TABLE hotels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR,
    
    -- Metadata
    source_filename VARCHAR,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    json_file_path VARCHAR,
    
    -- Hotel Details
    hotel_name VARCHAR,
    hotel_chain VARCHAR,
    star_rating INTEGER,
    
    -- Location
    address_street VARCHAR,
    address_city VARCHAR,
    address_country VARCHAR,
    address_postal_code VARCHAR,
    address_full VARCHAR,
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    
    -- Booking Dates
    check_in_date DATE,
    check_in_time VARCHAR,
    check_out_date DATE,
    check_out_time VARCHAR,
    nights_count INTEGER,
    
    -- Room Details
    room_type VARCHAR,
    number_of_rooms INTEGER,
    occupancy INTEGER,
    smoking_preference VARCHAR,
    
    -- Investment Value
    total_cost_amount NUMERIC(10, 2),
    total_cost_currency VARCHAR(3),
    per_night_cost_amount NUMERIC(10, 2),
    per_night_cost_currency VARCHAR(3),
    deposit_paid_amount NUMERIC(10, 2),
    deposit_paid_currency VARCHAR(3),
    is_refundable BOOLEAN,
    cancellation_policy TEXT,
    
    -- Booking Reference
    confirmation_number VARCHAR,
    booking_id VARCHAR,
    
    -- Guests (stored as JSONB)
    guests JSONB,  -- Array of guest objects
    
    -- Full extracted data
    extracted_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT hotels_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_hotels_user_id ON hotels(user_id);
CREATE INDEX idx_hotels_session_id ON hotels(session_id);
CREATE INDEX idx_hotels_check_in_date ON hotels(check_in_date);
```

### Table: `visas`

Stores extracted visa application data.

```sql
CREATE TABLE visas (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR,
    
    -- Metadata
    source_filename VARCHAR,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    json_file_path VARCHAR,
    
    -- Visa Details
    visa_type VARCHAR,  -- Tourist, Business, etc.
    destination_country VARCHAR,
    entry_type VARCHAR,  -- Single, Multiple
    validity_start_date DATE,
    validity_end_date DATE,
    
    -- Applicant Information
    applicant_first_name VARCHAR,
    applicant_last_name VARCHAR,
    applicant_full_name VARCHAR,
    applicant_date_of_birth DATE,
    applicant_age INTEGER,
    applicant_passport_number VARCHAR,
    applicant_nationality VARCHAR,
    
    -- Trip Purpose
    trip_purpose_primary VARCHAR,
    trip_purpose_detailed TEXT,
    is_business BOOLEAN,
    is_medical_treatment BOOLEAN,
    
    -- Planned Trip
    intended_arrival_date DATE,
    intended_departure_date DATE,
    duration_days INTEGER,
    destination_cities JSONB,  -- Array of city names
    
    -- Accommodation Info
    has_hotel_booking BOOLEAN,
    hotel_name VARCHAR,
    hotel_address VARCHAR,
    
    -- Financial Support
    has_sufficient_funds BOOLEAN,
    estimated_trip_cost_amount NUMERIC(10, 2),
    estimated_trip_cost_currency VARCHAR(3),
    
    -- Travel History
    has_previous_travel BOOLEAN,
    previous_destinations JSONB,  -- Array of destination names
    
    -- Full extracted data
    extracted_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT visas_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_visas_user_id ON visas(user_id);
CREATE INDEX idx_visas_session_id ON visas(session_id);
CREATE INDEX idx_visas_destination_country ON visas(destination_country);
```

### Table: `itineraries`

Stores extracted itinerary data.

```sql
CREATE TABLE itineraries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_id VARCHAR,
    
    -- Metadata
    source_filename VARCHAR,
    extracted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    json_file_path VARCHAR,
    
    -- Trip Overview
    trip_title VARCHAR,
    duration_days INTEGER,
    start_date DATE,
    end_date DATE,
    
    -- Destinations (stored as JSONB array)
    destinations JSONB,  -- Array of destination objects with city, country, dates, nights
    
    -- Activities (stored as JSONB array)
    activities JSONB,  -- Array of activity objects
    
    -- Adventure Sports Detection
    has_adventure_sports BOOLEAN,
    adventure_sports_activities JSONB,  -- Array of adventure sport objects
    
    -- Risk Factors
    has_extreme_sports BOOLEAN,
    has_water_sports BOOLEAN,
    has_winter_sports BOOLEAN,
    has_high_altitude_activities BOOLEAN,
    has_motorized_sports BOOLEAN,
    is_group_travel BOOLEAN,
    has_remote_locations BOOLEAN,
    has_political_risk_destinations BOOLEAN,
    
    -- Trip Characteristics
    is_group_tour BOOLEAN,
    is_solo_travel BOOLEAN,
    group_size INTEGER,
    includes_children BOOLEAN,
    includes_seniors BOOLEAN,  -- 70+
    
    -- Trip Structure
    trip_type VARCHAR,  -- single_return, multi_city, annual
    number_of_destinations INTEGER,
    requires_internal_travel BOOLEAN,
    internal_transport JSONB,  -- Array of transport methods
    
    -- Travelers (stored as JSONB)
    travelers JSONB,  -- Array of traveler objects
    
    -- Full extracted data
    extracted_data JSONB,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT itineraries_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX idx_itineraries_user_id ON itineraries(user_id);
CREATE INDEX idx_itineraries_session_id ON itineraries(session_id);
CREATE INDEX idx_itineraries_start_date ON itineraries(start_date);
CREATE INDEX idx_itineraries_has_adventure_sports ON itineraries(has_adventure_sports);
```

---

## 3. SQLAlchemy Models

### Proposed Model Files

**Location:** `apps/backend/app/models/flight.py`

```python
"""Flight model for storing flight confirmation data."""

from sqlalchemy import Column, String, Date, ForeignKey, DateTime, Integer, Numeric, Boolean
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
    
    # Airline Information
    airline_name = Column(String, nullable=True)
    airline_code = Column(String, nullable=True)
    
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
```

**Similar models needed for:** `hotel.py`, `visa.py`, `itinerary.py`

---

## 4. Database Service Layer

### Proposed Service File

**Location:** `apps/backend/app/services/document_storage.py`

```python
"""Service for storing extracted document data in database."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from app.models.flight import Flight
from app.models.hotel import Hotel
from app.models.visa import Visa
from app.models.itinerary import Itinerary


class DocumentStorageService:
    """Service for storing extracted document data."""
    
    def store_extracted_document(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        json_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store extracted document data in appropriate table.
        
        Args:
            db: Database session
            user_id: User UUID
            session_id: Chat session ID
            extracted_json: Extracted JSON data
            json_file_path: Path to saved JSON file
            
        Returns:
            Dictionary with stored record information
        """
        document_type = extracted_json.get("document_type")
        
        if document_type == "flight_confirmation":
            return self._store_flight(db, user_id, session_id, extracted_json, json_file_path)
        elif document_type == "hotel_booking":
            return self._store_hotel(db, user_id, session_id, extracted_json, json_file_path)
        elif document_type == "visa_application":
            return self._store_visa(db, user_id, session_id, extracted_json, json_file_path)
        elif document_type == "itinerary":
            return self._store_itinerary(db, user_id, session_id, extracted_json, json_file_path)
        else:
            raise ValueError(f"Unknown document type: {document_type}")
    
    def _store_flight(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        json_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """Store flight confirmation data."""
        flight_data = extracted_json.get("flight_details", {})
        destination = extracted_json.get("destination", {})
        airline = extracted_json.get("airline", {})
        booking_ref = extracted_json.get("booking_reference", {})
        trip_value = extracted_json.get("trip_value", {})
        trip_duration = extracted_json.get("trip_duration", {})
        
        departure = flight_data.get("departure", {}) or {}
        return_flight = flight_data.get("return", {}) or {}
        flight_numbers = flight_data.get("flight_numbers", {}) or {}
        
        total_cost = trip_value.get("total_cost", {}) or {}
        
        flight = Flight(
            user_id=user_id,
            session_id=session_id,
            source_filename=extracted_json.get("source_filename"),
            json_file_path=json_file_path,
            
            airline_name=airline.get("name"),
            airline_code=airline.get("code"),
            
            departure_date=self._parse_date(departure.get("date")),
            departure_time=departure.get("time"),
            departure_airport_code=departure.get("airport_code"),
            departure_airport_name=departure.get("airport_name"),
            
            return_date=self._parse_date(return_flight.get("date")),
            return_time=return_flight.get("time"),
            return_airport_code=return_flight.get("airport_code"),
            return_airport_name=return_flight.get("airport_name"),
            
            flight_number_outbound=flight_numbers.get("outbound"),
            flight_number_inbound=flight_numbers.get("inbound"),
            
            destination_country=destination.get("country"),
            destination_city=destination.get("city"),
            destination_airport_code=destination.get("airport_code"),
            
            pnr=booking_ref.get("pnr"),
            booking_number=booking_ref.get("booking_number"),
            
            trip_duration_days=trip_duration.get("days"),
            total_cost_amount=self._parse_numeric(total_cost.get("amount")),
            total_cost_currency=total_cost.get("currency"),
            
            travelers=extracted_json.get("travelers"),
            extracted_data=extracted_json
        )
        
        db.add(flight)
        db.commit()
        db.refresh(flight)
        
        return {"id": str(flight.id), "type": "flight", "stored_at": flight.created_at.isoformat()}
    
    def _store_hotel(self, db, user_id, session_id, extracted_json, json_file_path):
        """Store hotel booking data."""
        # Similar implementation...
        pass
    
    def _store_visa(self, db, user_id, session_id, extracted_json, json_file_path):
        """Store visa application data."""
        # Similar implementation...
        pass
    
    def _store_itinerary(self, db, user_id, session_id, extracted_json, json_file_path):
        """Store itinerary data."""
        # Similar implementation...
        pass
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except:
            return None
    
    def _parse_numeric(self, value: Any) -> Optional[float]:
        """Parse numeric value."""
        if value is None:
            return None
        try:
            return float(value)
        except:
            return None
```

---

## 5. Required Changes to Existing Code

### 5.1 Update Upload Endpoint

**File:** `apps/backend/app/routers/chat.py`

**Changes:**
1. After JSON extraction, check if `document_type == "unknown"`
2. If unknown, reject with HTTP 400
3. If valid, call `DocumentStorageService.store_extracted_document()`
4. Return success response with database record ID

**Pseudo-code:**
```python
# After json_extractor.extract()
extracted_json = json_extractor.extract(...)

# Check document type
if extracted_json.get("document_type") == "unknown":
    raise HTTPException(
        status_code=400,
        detail="Please only upload relevant documents! Accepted types: flight confirmation, hotel booking, itinerary, or visa application."
    )

# Store in database
storage_service = DocumentStorageService()
storage_result = storage_service.store_extracted_document(
    db=db,
    user_id=current_user.id,
    session_id=session_id,
    extracted_json=extracted_json,
    json_file_path=extracted_json.get("json_file_path")
)
```

### 5.2 Update User Model

**File:** `apps/backend/app/models/user.py`

**Add relationships:**
```python
flights = relationship("Flight", back_populates="user", cascade="all, delete-orphan")
hotels = relationship("Hotel", back_populates="user", cascade="all, delete-orphan")
visas = relationship("Visa", back_populates="user", cascade="all, delete-orphan")
itineraries = relationship("Itinerary", back_populates="user", cascade="all, delete-orphan")
```

### 5.3 Update Models __init__.py

**File:** `apps/backend/app/models/__init__.py`

**Add imports:**
```python
from .flight import Flight
from .hotel import Hotel
from .visa import Visa
from .itinerary import Itinerary

__all__ = [
    # ... existing models ...
    "Flight",
    "Hotel",
    "Visa",
    "Itinerary",
]
```

### 5.4 Create Alembic Migration

**Command:**
```bash
cd apps/backend
alembic revision --autogenerate -m "add_flight_hotel_visa_itinerary_tables"
alembic upgrade head
```

---

## 6. API Endpoints (Optional - For Future Use)

### 6.1 Get User's Documents

**Proposed endpoints:**
- `GET /api/v1/documents/flights` - Get user's flight confirmations
- `GET /api/v1/documents/hotels` - Get user's hotel bookings
- `GET /api/v1/documents/visas` - Get user's visa applications
- `GET /api/v1/documents/itineraries` - Get user's itineraries

**Or unified:**
- `GET /api/v1/documents?type=flight|hotel|visa|itinerary` - Get documents by type

---

## 7. Testing Considerations

1. **Unit Tests:**
   - Test document type rejection
   - Test JSON to database mapping for each document type
   - Test date/numeric parsing edge cases

2. **Integration Tests:**
   - Test full upload flow: upload → OCR → extraction → database storage
   - Test user isolation (users can only see their own documents)
   - Test session linking

3. **Edge Cases:**
   - Missing fields in JSON
   - Null values
   - Invalid date formats
   - Large JSON structures

---

## 8. Migration Strategy

1. **Create migration script** to add new tables
2. **Run migration** on development database
3. **Update code** to use new service
4. **Test thoroughly** before deploying
5. **Optional:** Create migration script to backfill existing JSON files into database

---

## 9. Summary of Changes Required

### New Files:
1. `apps/backend/app/models/flight.py`
2. `apps/backend/app/models/hotel.py`
3. `apps/backend/app/models/visa.py`
4. `apps/backend/app/models/itinerary.py`
5. `apps/backend/app/services/document_storage.py`
6. Alembic migration file

### Modified Files:
1. `apps/backend/app/routers/chat.py` - Add rejection logic and database storage
2. `apps/backend/app/models/user.py` - Add relationships
3. `apps/backend/app/models/__init__.py` - Add new model imports
4. `apps/backend/app/services/ocr/document_detector.py` - Ensure proper "unknown" detection
5. `apps/backend/app/services/ocr/json_extractor.py` - Potentially enhance error messages

### Database Changes:
- 4 new tables: `flights`, `hotels`, `visas`, `itineraries`
- Foreign keys to `users` table
- Indexes for performance

---

## 10. Benefits

1. **Data Persistence:** Document data stored in database, not just JSON files
2. **Queryability:** Can query user's documents, filter by dates, destinations, etc.
3. **Data Integrity:** Foreign key constraints ensure data consistency
4. **User Isolation:** Clear user_id linking ensures privacy
5. **Scalability:** Database indexes improve query performance
6. **Audit Trail:** Timestamps track when documents were extracted
7. **Session Linking:** Can link documents to chat sessions for context

---

## Next Steps

1. Review and approve this proposal
2. Create database models (flight.py, hotel.py, visa.py, itinerary.py)
3. Create Alembic migration
4. Implement DocumentStorageService
5. Update upload endpoint with rejection logic and storage
6. Update User model relationships
7. Test thoroughly
8. Deploy

