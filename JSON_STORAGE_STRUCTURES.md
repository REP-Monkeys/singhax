# JSON Storage Structures Reference

This document provides a comprehensive list of all JSON structures stored in the system, organized by category and storage location.

---

## 📋 Table of Contents

1. [Document Extraction JSONs (OCR/LLM)](#document-extraction-jsons)
2. [Database JSONB Fields](#database-jsonb-fields)
3. [Business Logic JSON Structures](#business-logic-json-structures)
4. [Other JSON Structures](#other-json-structures)

---

## 📄 Document Extraction JSONs

These JSONs are generated when documents are uploaded and processed via OCR/LLM. They are stored both as files and in database `extracted_data` JSONB columns.

### Common Metadata (All Document Types)

All document JSONs include:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "flight_confirmation|hotel_booking|itinerary|visa_application",
  "extracted_at": "2025-01-15T10:30:00Z",
  "confidence_thresholds": {
    "high": 0.90,
    "medium": 0.80,
    "low": 0.80
  },
  "source_filename": "document.pdf",
  "low_confidence_fields": [],
  "missing_fields": [],
  "high_confidence_fields": []
}
```

### 1. Flight Confirmation (`flights.extracted_data`)

**Storage Location:**
- File: `uploads/documents/{user_id}/flight_confirmation/{session_id}_flight_confirmation_{timestamp}.json`
- Database: `flights.extracted_data` (JSONB)

**Structure:**
```json
{
  "session_id": "...",
  "document_type": "flight_confirmation",
  "extracted_at": "...",
  "airline": {
    "name": "Scoot",
    "code": "TR",
    "confidence": 0.92
  },
  "flight_details": {
    "departure": {
      "date": "2025-03-15",
      "time": "14:30",
      "airport_code": "SIN",
      "airport_name": "Singapore Changi Airport",
      "confidence": 0.91
    },
    "return": {
      "date": "2025-03-22",
      "time": "18:45",
      "airport_code": "NRT",
      "airport_name": "Narita International Airport",
      "confidence": 0.91
    },
    "flight_numbers": {
      "outbound": "TR892",
      "inbound": "TR893",
      "confidence": 0.93
    }
  },
  "destination": {
    "country": "Japan",
    "city": "Tokyo",
    "airport_code": "NRT",
    "confidence": 0.92
  },
  "travelers": [
    {
      "name": {
        "first": "John",
        "last": "Doe",
        "full": "John Doe",
        "confidence": 0.94
      },
      "ticket": {
        "ticket_number": "1234567890123",
        "class": {
          "service_class": "Economy",
          "code": "Y",
          "confidence": 0.92
        },
        "seat_assignment": "12A",
        "seat_type": "Standard",
        "cost": {
          "amount": 650.00,
          "currency": "SGD",
          "confidence": 0.88
        }
      }
    }
  ],
  "trip_duration": {
    "days": 7,
    "calculated_from_dates": true,
    "confidence": 0.95
  },
  "trip_value": {
    "total_cost": {
      "amount": 1850.00,
      "currency": "SGD",
      "confidence": 0.90
    },
    "breakdown": [...]
  },
  "booking_reference": {
    "pnr": "ABC123",
    "booking_number": "BK456789",
    "confidence": 0.93
  }
}
```

**Also stored in:** `flights.travelers` (JSONB array)

---

### 2. Hotel Booking (`hotels.extracted_data`)

**Storage Location:**
- File: `uploads/documents/{user_id}/hotel_booking/{session_id}_hotel_booking_{timestamp}.json`
- Database: `hotels.extracted_data` (JSONB)

**Structure:**
```json
{
  "session_id": "...",
  "document_type": "hotel_booking",
  "extracted_at": "...",
  "hotel_details": {
    "name": "Grand Tokyo Hotel",
    "chain": null,
    "star_rating": 4,
    "confidence": 0.92
  },
  "location": {
    "address": {
      "street": "1-2-3 Shibuya",
      "city": "Tokyo",
      "country": "Japan",
      "postal_code": "150-0001",
      "full": "1-2-3 Shibuya, Tokyo, Japan 150-0001",
      "confidence": 0.91
    },
    "coordinates": {
      "latitude": null,
      "longitude": null
    }
  },
  "booking_dates": {
    "check_in": {
      "date": "2025-03-15",
      "time": "15:00",
      "confidence": 0.93
    },
    "check_out": {
      "date": "2025-03-22",
      "time": "11:00",
      "confidence": 0.93
    },
    "nights": {
      "count": 7,
      "calculated_from_dates": true,
      "confidence": 0.95
    }
  },
  "room_details": {
    "room_type": "Deluxe Double Room",
    "number_of_rooms": 1,
    "occupancy": 2,
    "smoking_preference": "Non-smoking",
    "confidence": 0.90
  },
  "investment_value": {
    "total_cost": {
      "amount": 3500.00,
      "currency": "SGD",
      "confidence": 0.92
    },
    "per_night": {
      "amount": 500.00,
      "currency": "SGD"
    },
    "deposit_paid": {
      "amount": 700.00,
      "currency": "SGD"
    },
    "refundable": true,
    "cancellation_policy": "Free cancellation until 48 hours before check-in"
  },
  "guests": [
    {
      "name": {
        "first": "John",
        "last": "Doe",
        "full": "John Doe"
      },
      "is_primary_guest": true,
      "is_adult": true
    }
  ],
  "booking_reference": {
    "confirmation_number": "HTL789456",
    "booking_id": "BK987654"
  }
}
```

**Also stored in:** `hotels.guests` (JSONB array)

---

### 3. Itinerary (`itineraries.extracted_data`)

**Storage Location:**
- File: `uploads/documents/{user_id}/itinerary/{session_id}_itinerary_{timestamp}.json`
- Database: `itineraries.extracted_data` (JSONB)

**Structure:**
```json
{
  "session_id": "...",
  "document_type": "itinerary",
  "extracted_at": "...",
  "trip_overview": {
    "title": "Japan Adventure Tour",
    "duration_days": 10,
    "start_date": "2025-03-15",
    "end_date": "2025-03-24",
    "confidence": 0.91
  },
  "destinations": [
    {
      "city": "Tokyo",
      "country": "Japan",
      "arrival_date": "2025-03-15",
      "departure_date": "2025-03-18",
      "nights": 3,
      "confidence": 0.92
    }
  ],
  "activities": [
    {
      "date": "2025-03-16",
      "location": "Tokyo",
      "activity_type": "sightseeing",
      "description": "Senso-ji Temple visit",
      "is_adventure_sport": false,
      "risk_level": "low",
      "confidence": 0.90
    },
    {
      "date": "2025-03-17",
      "location": "Tokyo",
      "activity_type": "adventure",
      "description": "Skiing at nearby resort",
      "is_adventure_sport": true,
      "risk_level": "medium",
      "requires_special_coverage": true,
      "confidence": 0.91
    }
  ],
  "adventure_sports_detected": {
    "has_adventure_sports": true,
    "activities": [
      {
        "type": "skiing",
        "date": "2025-03-17",
        "location": "Tokyo",
        "risk_level": "medium",
        "confidence": 0.91
      }
    ]
  },
  "risk_factors": {
    "extreme_sports": false,
    "water_sports": false,
    "winter_sports": true,
    "high_altitude_activities": false,
    "motorized_sports": false,
    "group_travel": true,
    "remote_locations": false,
    "political_risk_destinations": false
  },
  "trip_characteristics": {
    "is_group_tour": false,
    "is_solo_travel": false,
    "group_size": 2,
    "includes_children": false,
    "includes_seniors": false
  },
  "travelers": [
    {
      "name": {
        "first": "John",
        "last": "Doe",
        "full": "John Doe"
      },
      "age": null,
      "role": "traveler"
    }
  ],
  "trip_structure": {
    "trip_type": "multi_city",
    "number_of_destinations": 3,
    "requires_internal_travel": true,
    "internal_transport": ["train", "bus"]
  }
}
```

**Also stored in:**
- `itineraries.destinations` (JSONB array)
- `itineraries.activities` (JSONB array)
- `itineraries.adventure_sports_activities` (JSONB array)
- `itineraries.internal_transport` (JSONB array)
- `itineraries.travelers` (JSONB array)

---

### 4. Visa Application (`visas.extracted_data`)

**Storage Location:**
- File: `uploads/documents/{user_id}/visa_application/{session_id}_visa_application_{timestamp}.json`
- Database: `visas.extracted_data` (JSONB)

**Structure:**
```json
{
  "session_id": "...",
  "document_type": "visa_application",
  "extracted_at": "...",
  "visa_details": {
    "visa_type": "Tourist",
    "destination_country": "Japan",
    "entry_type": "Single",
    "validity_period": {
      "start": "2025-03-01",
      "end": "2025-06-01",
      "confidence": 0.93
    }
  },
  "applicant": {
    "name": {
      "first": "John",
      "last": "Doe",
      "full": "John Doe"
    },
    "date_of_birth": "1990-05-15",
    "age": 34,
    "passport_number": "E12345678",
    "nationality": "Singaporean"
  },
  "trip_purpose": {
    "primary_purpose": "Tourism",
    "detailed_purpose": "Sightseeing and cultural activities",
    "is_business": false,
    "is_medical_treatment": false
  },
  "planned_trip": {
    "intended_arrival_date": "2025-03-15",
    "intended_departure_date": "2025-03-22",
    "duration_days": 7,
    "destination_cities": ["Tokyo", "Kyoto"]
  },
  "accommodation_info": {
    "has_hotel_booking": true,
    "hotel_name": "Grand Tokyo Hotel",
    "hotel_address": "Tokyo, Japan"
  },
  "financial_support": {
    "has_sufficient_funds": true,
    "estimated_trip_cost": {
      "amount": 5000.00,
      "currency": "SGD"
    }
  },
  "travel_history": {
    "has_previous_travel": true,
    "previous_destinations": ["Thailand", "Malaysia"]
  }
}
```

**Also stored in:**
- `visas.destination_cities` (JSONB array)
- `visas.previous_destinations` (JSONB array)

---

## 💾 Database JSONB Fields

These are JSONB columns in PostgreSQL that store structured data.

### Document Tables

| Table | Column | Type | Description |
|-------|--------|------|-------------|
| `flights` | `travelers` | JSONB | Array of traveler objects with ticket info |
| `flights` | `extracted_data` | JSONB | Complete extraction JSON |
| `hotels` | `guests` | JSONB | Array of guest objects |
| `hotels` | `extracted_data` | JSONB | Complete extraction JSON |
| `itineraries` | `destinations` | JSONB | Array of destination objects |
| `itineraries` | `activities` | JSONB | Array of activity objects |
| `itineraries` | `adventure_sports_activities` | JSONB | Array of adventure sport objects |
| `itineraries` | `internal_transport` | JSONB | Array of transport methods |
| `itineraries` | `travelers` | JSONB | Array of traveler objects |
| `itineraries` | `extracted_data` | JSONB | Complete extraction JSON |
| `visas` | `destination_cities` | JSONB | Array of city names |
| `visas` | `previous_destinations` | JSONB | Array of destination names |
| `visas` | `extracted_data` | JSONB | Complete extraction JSON |

### Business Logic Tables

| Table | Column | Type | Description |
|-------|--------|------|-------------|
| `trips` | `flight_refs` | JSONB | Array of flight booking references |
| `trips` | `accommodation_refs` | JSONB | Array of hotel/booking references |
| `quotes` | `travelers` | JSONB | List of traveler data objects |
| `quotes` | `activities` | JSONB | List of planned activities |
| `quotes` | `risk_breakdown` | JSONB | Risk assessment details |
| `quotes` | `breakdown` | JSONB | Price breakdown details |
| `quotes` | `insurer_ref` | String | JSON string with Ancileo reference data |
| `policies` | `coverage` | JSONB | Coverage details and limits |
| `policies` | `named_insureds` | JSONB | List of covered travelers |
| `claims` | `requirements` | JSONB | Required documents and info |
| `claims` | `documents` | JSONB | Uploaded documents metadata |

### Other Tables

| Table | Column | Type | Description |
|-------|--------|------|-------------|
| `travelers` | `preexisting_conditions` | JSONB | List of condition descriptions |
| `chat_history` | `rationale` | JSONB | AI reasoning and context |
| `rag_documents` | `citations` | JSONB | Reference citations |
| `audit_log` | `payload` | JSONB | Additional context and data |

---

## 💼 Business Logic JSON Structures

### 1. Quote (`quotes` table)

#### `quotes.travelers` (JSONB)
```json
[
  {
    "name": {
      "first": "John",
      "last": "Doe",
      "full": "John Doe"
    },
    "date_of_birth": "1990-05-15",
    "age": 34,
    "passport_number": "E12345678",
    "is_primary": true,
    "preexisting_conditions": []
  }
]
```

#### `quotes.activities` (JSONB)
```json
[
  {
    "type": "skiing",
    "date": "2025-03-17",
    "location": "Tokyo",
    "risk_level": "medium",
    "requires_special_coverage": true
  },
  {
    "type": "sightseeing",
    "date": "2025-03-16",
    "location": "Tokyo",
    "risk_level": "low"
  }
]
```

#### `quotes.risk_breakdown` (JSONB)
```json
{
  "overall_risk": "medium",
  "factors": {
    "adventure_sports": true,
    "destination_risk": "low",
    "trip_duration": "standard",
    "traveler_age": "standard"
  },
  "requires_additional_coverage": true,
  "recommended_tier": "elite"
}
```

#### `quotes.breakdown` (JSONB)
```json
{
  "base_price": 150.00,
  "currency": "SGD",
  "components": [
    {
      "type": "base_coverage",
      "amount": 120.00,
      "description": "Standard travel insurance"
    },
    {
      "type": "adventure_sports",
      "amount": 30.00,
      "description": "Adventure sports coverage"
    }
  ],
  "discounts": [],
  "total": 150.00
}
```

#### `quotes.insurer_ref` (String - JSON serialized)
```json
{
  "quote_id": "ancileo_quote_123",
  "offer_id": "ancileo_offer_456",
  "product_code": "TRAVEL_EASY",
  "base_price": 120.00
}
```

---

### 2. Policy (`policies` table)

#### `policies.coverage` (JSONB)
```json
{
  "medical_expenses": {
    "limit": 1000000,
    "currency": "SGD",
    "deductible": 0
  },
  "trip_cancellation": {
    "limit": 50000,
    "currency": "SGD"
  },
  "baggage_loss": {
    "limit": 5000,
    "currency": "SGD"
  },
  "adventure_sports": {
    "covered": true,
    "types": ["skiing", "snowboarding"]
  },
  "policy_type": "single_trip",
  "tier": "elite"
}
```

#### `policies.named_insureds` (JSONB)
```json
[
  {
    "name": {
      "first": "John",
      "last": "Doe",
      "full": "John Doe"
    },
    "date_of_birth": "1990-05-15",
    "passport_number": "E12345678",
    "is_primary": true
  }
]
```

---

### 3. Claim (`claims` table)

#### `claims.requirements` (JSONB)
```json
{
  "required_documents": [
    "medical_report",
    "police_report",
    "receipts"
  ],
  "required_information": [
    "incident_date",
    "incident_location",
    "description"
  ],
  "deadline": "2025-04-15"
}
```

#### `claims.documents` (JSONB)
```json
[
  {
    "document_id": "uuid-here",
    "filename": "medical_report.pdf",
    "uploaded_at": "2025-03-20T10:00:00Z",
    "file_size": 12345,
    "file_type": "application/pdf"
  }
]
```

---

### 4. Trip (`trips` table)

#### `trips.flight_refs` (JSONB)
```json
[
  {
    "flight_id": "uuid-here",
    "pnr": "ABC123",
    "booking_number": "BK456789",
    "departure_date": "2025-03-15"
  }
]
```

#### `trips.accommodation_refs` (JSONB)
```json
[
  {
    "hotel_id": "uuid-here",
    "confirmation_number": "HTL789456",
    "check_in_date": "2025-03-15",
    "check_out_date": "2025-03-22"
  }
]
```

---

### 5. Traveler (`travelers` table)

#### `travelers.preexisting_conditions` (JSONB)
```json
[
  {
    "condition": "Hypertension",
    "diagnosed_date": "2020-01-15",
    "currently_treated": true,
    "medications": ["Lisinopril"],
    "stable": true
  },
  {
    "condition": "Diabetes Type 2",
    "diagnosed_date": "2018-06-20",
    "currently_treated": true,
    "medications": ["Metformin"],
    "stable": true
  }
]
```

---

## 📝 Other JSON Structures

### 1. Chat History (`chat_history` table)

#### `chat_history.rationale` (JSONB)
```json
{
  "reasoning": "User asked about coverage for skiing. Checking policy documents...",
  "context": {
    "trip_id": "uuid-here",
    "quote_id": "uuid-here",
    "session_id": "uuid-here"
  },
  "sources": [
    {
      "type": "policy_document",
      "document_id": "uuid-here",
      "section": "Adventure Sports Coverage"
    }
  ],
  "confidence": 0.95
}
```

---

### 2. RAG Document (`rag_documents` table)

#### `rag_documents.citations` (JSONB)
```json
{
  "policy_document": "Scootsurance QSR022206",
  "section": "1.2.3",
  "page": 15,
  "subsection": "Adventure Sports Coverage",
  "related_sections": ["1.2.4", "2.1.1"]
}
```

---

### 3. Audit Log (`audit_log` table)

#### `audit_log.payload` (JSONB)
```json
{
  "action_details": "Quote created",
  "quote_id": "uuid-here",
  "trip_id": "uuid-here",
  "user_id": "uuid-here",
  "changes": {
    "status": "draft -> priced",
    "price_firm": null -> 150.00
  },
  "ip_address": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

---

## 🔄 Normalized Structure (For Policy Recommendation)

This is a merged structure combining data from multiple documents. **Not stored in database** - generated on-demand.

**Purpose:** Merge available document types into a unified structure for policy recommendation.

**Location:** Generated in memory by `policy_recommender.py`

**Structure:** See `DOCUMENT_JSON_STRUCTURES.md` section 5 for full details.

Key points:
- Merges data from flight, hotel, itinerary, and visa documents
- Tracks source of each data point
- Handles partial information (doesn't require all document types)
- Used for policy recommendation logic

---

## 📊 Summary Table

| Category | JSON Type | Storage | Format |
|----------|-----------|---------|--------|
| **Document Extraction** | Flight | File + DB JSONB | Full extraction JSON |
| **Document Extraction** | Hotel | File + DB JSONB | Full extraction JSON |
| **Document Extraction** | Itinerary | File + DB JSONB | Full extraction JSON |
| **Document Extraction** | Visa | File + DB JSONB | Full extraction JSON |
| **Business Logic** | Quote data | DB JSONB | Travelers, activities, breakdowns |
| **Business Logic** | Policy data | DB JSONB | Coverage, insureds |
| **Business Logic** | Claim data | DB JSONB | Requirements, documents |
| **Business Logic** | Trip refs | DB JSONB | Flight/accommodation references |
| **Supporting** | Chat rationale | DB JSONB | AI reasoning context |
| **Supporting** | RAG citations | DB JSONB | Document citations |
| **Supporting** | Audit payload | DB JSONB | Action context |

---

## 🔍 Query Examples

### Get all JSONB fields from a quote:
```sql
SELECT 
  travelers,
  activities,
  risk_breakdown,
  breakdown,
  insurer_ref
FROM quotes
WHERE id = 'quote-uuid';
```

### Get extracted data from a flight:
```sql
SELECT extracted_data
FROM flights
WHERE session_id = 'session-uuid';
```

### Query JSONB arrays:
```sql
-- Get all destinations from itineraries
SELECT destinations
FROM itineraries
WHERE user_id = 'user-uuid';

-- Query specific JSONB field
SELECT extracted_data->'travelers' as travelers
FROM flights
WHERE id = 'flight-uuid';
```

---

## 📝 Notes

1. **All document JSONs** are stored twice:
   - As JSON files in `uploads/documents/`
   - As JSONB in database `extracted_data` column

2. **Confidence scores** are included in extraction JSONs but not stored as separate columns

3. **JSONB vs String**: Most fields use JSONB for queryability, except `quotes.insurer_ref` which is a JSON string (for backward compatibility)

4. **Array fields**: Many JSONB fields store arrays (travelers, activities, destinations, etc.)

5. **Normalized structure**: Generated on-demand, not stored persistently

6. **File paths**: JSON extraction files use pattern: `{session_id}_{document_type}_{timestamp}.json`

