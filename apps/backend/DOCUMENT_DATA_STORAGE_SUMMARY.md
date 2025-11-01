# Document Data Storage Summary

This document outlines exactly what data is generated and stored when a document is uploaded.

## 📋 Overview

When a document is uploaded, the system:
1. **Extracts text** using OCR (Tesseract)
2. **Detects document type** (flight, hotel, visa, itinerary)
3. **Extracts structured JSON** using LLM (Groq)
4. **Stores the file** (local filesystem or Supabase Storage)
5. **Saves structured data** to the database (PostgreSQL)
6. **Links to session** via `session_id` (and potentially to `Trip` if one exists)

---

## 📦 Common Fields (All Document Types)

Every document stores these **metadata fields**:

| Field | Type | Description |
|-------|------|-------------|
| `id` | UUID | Unique document identifier (auto-generated) |
| `user_id` | UUID | Foreign key to User table |
| `session_id` | String | Chat session ID (links to conversation) |
| `source_filename` | String | Original filename from upload |
| `extracted_at` | DateTime | When OCR extraction completed |
| `json_file_path` | String | Path to saved JSON extraction file |
| `file_path` | String | Storage path (local or cloud) |
| `file_size` | Integer | File size in bytes |
| `file_content_type` | String | MIME type (e.g., "application/pdf") |
| `original_filename` | String | Original uploaded filename |
| `extracted_data` | JSONB | **Complete raw JSON** from LLM extraction |
| `created_at` | DateTime | When record was created |
| `updated_at` | DateTime | When record was last updated |

---

## ✈️ Flight Confirmation (`flights` table)

### File Storage
- **Path**: `documents/{user_id}/flight_confirmation/{uuid}.pdf`
- **Storage**: Local filesystem or Supabase Storage

### Structured Data Stored

#### Airline Information
- `airline_name` (String) - e.g., "Singapore Airlines"
- `airline_code` (String) - e.g., "SQ"

#### Flight Details - Departure
- `departure_date` (Date) - e.g., "2025-12-15"
- `departure_time` (String) - e.g., "10:30"
- `departure_airport_code` (String) - e.g., "SIN"
- `departure_airport_name` (String) - e.g., "Changi Airport"

#### Flight Details - Return
- `return_date` (Date)
- `return_time` (String)
- `return_airport_code` (String)
- `return_airport_name` (String)

#### Flight Numbers
- `flight_number_outbound` (String) - e.g., "SQ638"
- `flight_number_inbound` (String)

#### Destination
- `destination_country` (String) - e.g., "Japan"
- `destination_city` (String) - e.g., "Tokyo"
- `destination_airport_code` (String) - e.g., "NRT"

#### Booking Reference
- `pnr` (String) - Passenger Name Record
- `booking_number` (String)

#### Trip Information
- `trip_duration_days` (Integer)
- `total_cost_amount` (Numeric) - e.g., 850.00
- `total_cost_currency` (String) - e.g., "SGD"

#### Travelers (JSONB)
Stored as JSON array:
```json
[
  {
    "name": {
      "first": "Yuki",
      "last": "Tanaka",
      "full": "Tanaka Yuki"
    },
    "ticket": {
      "ticket_number": "...",
      "class": {
        "service_class": "Economy",
        "code": "..."
      },
      "seat_assignment": "32A",
      "seat_type": "...",
      "cost": {
        "amount": 850.0,
        "currency": "SGD"
      }
    }
  }
]
```

---

## 🏨 Hotel Booking (`hotels` table)

### File Storage
- **Path**: `documents/{user_id}/hotel_booking/{uuid}.pdf`
- **Storage**: Local filesystem or Supabase Storage

### Structured Data Stored

#### Hotel Details
- `hotel_name` (String) - e.g., "Marriott Hotel"
- `hotel_chain` (String) - e.g., "Marriott"
- `star_rating` (Integer) - e.g., 5

#### Location
- `address_street` (String)
- `address_city` (String)
- `address_country` (String)
- `address_postal_code` (String)
- `address_full` (String) - Complete address
- `latitude` (Numeric) - GPS coordinates
- `longitude` (Numeric) - GPS coordinates

#### Booking Dates
- `check_in_date` (Date)
- `check_in_time` (String)
- `check_out_date` (Date)
- `check_out_time` (String)
- `nights_count` (Integer)

#### Room Details
- `room_type` (String) - e.g., "Deluxe Suite"
- `number_of_rooms` (Integer)
- `occupancy` (Integer) - Number of guests
- `smoking_preference` (String)

#### Investment Value
- `total_cost_amount` (Numeric)
- `total_cost_currency` (String)
- `per_night_cost_amount` (Numeric)
- `per_night_cost_currency` (String)
- `deposit_paid_amount` (Numeric)
- `deposit_paid_currency` (String)
- `is_refundable` (Boolean)
- `cancellation_policy` (Text)

#### Booking Reference
- `confirmation_number` (String)
- `booking_id` (String)

#### Guests (JSONB)
Stored as JSON array:
```json
[
  {
    "name": {
      "first": "John",
      "last": "Doe",
      "full": "John Doe"
    },
    "email": "john@example.com",
    "phone": "+1234567890"
  }
]
```

---

## 🛂 Visa Application (`visas` table)

### File Storage
- **Path**: `documents/{user_id}/visa_application/{uuid}.pdf`
- **Storage**: Local filesystem or Supabase Storage

### Structured Data Stored

#### Visa Details
- `visa_type` (String) - e.g., "Tourist", "Business"
- `destination_country` (String)
- `entry_type` (String) - e.g., "Single", "Multiple"
- `validity_start_date` (Date)
- `validity_end_date` (Date)

#### Applicant Information
- `applicant_first_name` (String)
- `applicant_last_name` (String)
- `applicant_full_name` (String)
- `applicant_date_of_birth` (Date)
- `applicant_age` (Integer)
- `applicant_passport_number` (String)
- `applicant_nationality` (String)

#### Trip Purpose
- `trip_purpose_primary` (String) - e.g., "Tourism"
- `trip_purpose_detailed` (Text)
- `is_business` (Boolean)
- `is_medical_treatment` (Boolean)

#### Planned Trip
- `intended_arrival_date` (Date)
- `intended_departure_date` (Date)
- `duration_days` (Integer)
- `destination_cities` (JSONB) - Array of city names

#### Accommodation Info
- `has_hotel_booking` (Boolean)
- `hotel_name` (String)
- `hotel_address` (String)

#### Financial Support
- `has_sufficient_funds` (Boolean)
- `estimated_trip_cost_amount` (Numeric)
- `estimated_trip_cost_currency` (String)

#### Travel History
- `has_previous_travel` (Boolean)
- `previous_destinations` (JSONB) - Array of destination names

---

## 📅 Itinerary (`itineraries` table)

### File Storage
- **Path**: `documents/{user_id}/itinerary/{uuid}.pdf`
- **Storage**: Local filesystem or Supabase Storage

### Structured Data Stored

#### Trip Overview
- `trip_title` (String) - e.g., "Japan Adventure Trip"
- `duration_days` (Integer)
- `start_date` (Date)
- `end_date` (Date)

#### Destinations (JSONB)
Stored as JSON array:
```json
[
  {
    "country": "Japan",
    "city": "Tokyo",
    "region": "Kanto"
  }
]
```

#### Activities (JSONB)
Stored as JSON array:
```json
[
  {
    "name": "Skiing",
    "location": "Hakuba",
    "date": "2025-12-20"
  }
]
```

#### Adventure Sports Detection
- `has_adventure_sports` (Boolean)
- `adventure_sports_activities` (JSONB) - Array of adventure sport objects

#### Risk Factors
- `has_extreme_sports` (Boolean)
- `has_water_sports` (Boolean)
- `has_winter_sports` (Boolean)
- `has_high_altitude_activities` (Boolean)
- `has_motorized_sports` (Boolean)
- `is_group_travel` (Boolean)
- `has_remote_locations` (Boolean)
- `has_political_risk_destinations` (Boolean)

#### Trip Characteristics
- `is_group_tour` (Boolean)
- `is_solo_travel` (Boolean)
- `group_size` (Integer)
- `includes_children` (Boolean)
- `includes_seniors` (Boolean) - 70+

#### Trip Structure
- `trip_type` (String) - e.g., "single_return", "multi_city", "annual"
- `number_of_destinations` (Integer)
- `requires_internal_travel` (Boolean)
- `internal_transport` (JSONB) - Array of transport methods

#### Travelers (JSONB)
Stored as JSON array:
```json
[
  {
    "name": {
      "first": "Jane",
      "last": "Smith",
      "full": "Jane Smith"
    },
    "age": 30,
    "passport_number": "..."
  }
]
```

---

## 🔗 Linking to Trips

All documents are linked to chat sessions via `session_id`. If a `Trip` record exists with the same `session_id`, the document is effectively linked to that trip.

**Query to find documents for a trip:**
```sql
SELECT * FROM flights WHERE session_id = 'trip_session_id';
SELECT * FROM hotels WHERE session_id = 'trip_session_id';
SELECT * FROM visas WHERE session_id = 'trip_session_id';
SELECT * FROM itineraries WHERE session_id = 'trip_session_id';
```

---

## 📊 Data Flow Summary

```
1. User uploads PDF/image
   ↓
2. OCR extracts text (Tesseract)
   ↓
3. Document type detected (LLM)
   ↓
4. Structured JSON extracted (LLM)
   ↓
5. File saved to storage
   ↓
6. Database record created with:
   - All structured fields (parsed from JSON)
   - Complete JSON stored in `extracted_data` field
   - File metadata (path, size, content-type)
   - Session linkage (`session_id`)
   ↓
7. Logging confirms storage and trip connection
```

---

## 💾 Storage Locations

### File Storage
- **Local**: `apps/backend/uploads/documents/{user_id}/{document_type}/{uuid}.pdf`
- **Cloud**: Supabase Storage bucket `documents/{user_id}/{document_type}/{uuid}.pdf`

### JSON Extraction Files
- **Location**: `apps/backend/uploads/documents/{user_id}/{document_type}/{session_id}_{document_type}_{timestamp}.json`
- **Contains**: Complete extracted JSON with confidence scores

### Database
- **Tables**: `flights`, `hotels`, `visas`, `itineraries`
- **Database**: PostgreSQL (via Supabase or local)
- **Full JSON**: Stored in `extracted_data` JSONB column

---

## 🔍 Example: Complete Flight Document Record

When a flight confirmation is uploaded, a database record is created with:

**Fields populated from JSON extraction:**
- Airline: "Singapore Airlines" (SQ)
- Departure: 2025-12-15 10:30 from SIN
- Destination: Tokyo, Japan (NRT)
- Flight: SQ638
- PNR: SQ7K8P
- Cost: SGD 850.00
- Travelers: [{"name": "Tanaka Yuki", "seat": "32A", ...}]

**Metadata:**
- Document ID: `uuid-generated`
- User ID: `user-uuid`
- Session ID: `session-uuid`
- File path: `documents/user-uuid/flight_confirmation/uuid.pdf`
- File size: 12345 bytes
- Created: 2025-01-01 12:00:00 UTC

**Full JSON in `extracted_data`:**
```json
{
  "session_id": "...",
  "document_type": "flight_confirmation",
  "airline": {"name": "Singapore Airlines", "code": "SQ"},
  "flight_details": {...},
  "travelers": [...],
  "confidence_thresholds": {...},
  ...
}
```

---

## 📝 Notes

1. **All documents store the complete extracted JSON** in the `extracted_data` JSONB field, even if individual fields are also stored as columns.

2. **Confidence scores** are included in the JSON but not stored as separate database columns.

3. **Session linkage** is via `session_id`, which links to:
   - Chat conversation state
   - Potentially a `Trip` record (if `Trip.session_id` matches)

4. **File storage** is redundant (both file system and database store metadata), but provides:
   - Quick file access (file system)
   - Queryable metadata (database)
   - Backup/recovery (both locations)

5. **JSON extraction files** are saved separately for debugging/audit purposes.

