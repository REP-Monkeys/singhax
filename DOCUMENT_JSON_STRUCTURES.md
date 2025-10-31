# Document JSON Structures

This document defines the JSON structures for each document type that can be processed via OCR.

## Common Metadata (All Document Types)

All JSON files include:
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "flight_confirmation",
  "extracted_at": "2025-01-15T10:30:00Z",
  "confidence_thresholds": {
    "high": 0.90,  // Auto-include
    "medium": 0.80,  // Include but flag for confirmation
    "low": 0.80  // Below this = ask user to manually input
  },
  "source_filename": "booking_confirmation.pdf",
  "low_confidence_fields": [],  // Fields 0.80-0.89 (need confirmation)
  "missing_fields": [],  // Fields <0.80 (need manual input)
  "high_confidence_fields": []  // Fields >=0.90 (auto-accepted)
}
```

## Confidence Level Handling

- **≥0.90 (High)**: Automatically included, no user confirmation needed
- **0.80-0.89 (Medium)**: Included but flagged for user confirmation before use
- **<0.80 (Low)**: Not included, system asks user to manually input the information

---

## 1. ✈️ Flight Confirmation

**Purpose**: Extract trip dates, destinations, travelers, and trip value

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "flight_confirmation",
  "extracted_at": "2025-01-15T10:30:00Z",
  "confidence_threshold": 0.90,
  "source_filename": "flight_confirmation.pdf",
  
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
      "age": null,  // Usually not in flight confirmations
      "passport_number": null,  // Sometimes present
      "ticket": {
        "ticket_number": "1234567890123",
        "class": {
          "service_class": "Economy",
          "code": "Y",
          "confidence": 0.92
        },
        "seat_assignment": "12A",
        "seat_type": "Standard",  // Standard, Premium, Exit Row, etc.
        "cost": {
          "amount": 650.00,
          "currency": "SGD",
          "confidence": 0.88
        },
        "confidence": 0.91
      }
    },
    {
      "name": {
        "first": "Jane",
        "last": "Doe",
        "full": "Jane Doe",
        "confidence": 0.94
      },
      "age": null,
      "passport_number": null,
      "ticket": {
        "ticket_number": "1234567890124",
        "class": {
          "service_class": "Business",
          "code": "J",
          "confidence": 0.92
        },
        "seat_assignment": "12B",
        "seat_type": "Premium",
        "cost": {
          "amount": 1200.00,
          "currency": "SGD",
          "confidence": 0.88
        },
        "confidence": 0.91
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
    "breakdown": [
      {
        "traveler": "John Doe",
        "amount": 650.00,
        "currency": "SGD",
        "class": "Economy",
        "confidence": 0.88
      },
      {
        "traveler": "Jane Doe",
        "amount": 1200.00,
        "currency": "SGD",
        "class": "Business",
        "confidence": 0.88
      }
    ],
    "confidence": 0.90
  },
  
  "booking_reference": {
    "pnr": "ABC123",
    "booking_number": "BK456789",
    "confidence": 0.93
  },
  
  "low_confidence_fields": [],
  "missing_fields": ["traveler_ages", "pre_existing_conditions"]
}
```

---

## 2. 🏨 Hotel Booking

**Purpose**: Extract accommodation dates, location, and investment value

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "hotel_booking",
  "extracted_at": "2025-01-15T10:30:00Z",
  "confidence_threshold": 0.90,
  "source_filename": "hotel_confirmation.pdf",
  
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
      "longitude": null,
      "confidence": 0.0
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
      "currency": "SGD",
      "confidence": 0.92
    },
    "deposit_paid": {
      "amount": 700.00,
      "currency": "SGD",
      "confidence": 0.88
    },
    "refundable": true,
    "cancellation_policy": "Free cancellation until 48 hours before check-in",
    "confidence": 0.85
  },
  
  "guests": [
    {
      "name": {
        "first": "John",
        "last": "Doe",
        "full": "John Doe",
        "confidence": 0.94
      },
      "age": null,
      "is_primary_guest": true,  // Primary guest (person who made booking, responsible for payment)
      "is_adult": true,  // Adult vs child (affects pricing/eligibility)
      "confidence": 0.91
    },
    {
      "name": {
        "first": "Jane",
        "last": "Doe",
        "full": "Jane Doe",
        "confidence": 0.94
      },
      "age": null,
      "is_primary_guest": false,
      "is_adult": true,
      "confidence": 0.91
    }
  ],
  
  "booking_reference": {
    "confirmation_number": "HTL789456",
    "booking_id": "BK987654",
    "confidence": 0.93
  },
  
  "low_confidence_fields": ["cancellation_policy"],
  "missing_fields": ["traveler_ages", "pre_existing_conditions"]
}
```

---

## 3. 📄 Itinerary

**Purpose**: Extract activities, destinations, timeline, and trip structure

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "itinerary",
  "extracted_at": "2025-01-15T10:30:00Z",
  "confidence_threshold": 0.90,
  "source_filename": "travel_itinerary.pdf",
  
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
    },
    {
      "city": "Kyoto",
      "country": "Japan",
      "arrival_date": "2025-03-18",
      "departure_date": "2025-03-22",
      "nights": 4,
      "confidence": 0.92
    },
    {
      "city": "Osaka",
      "country": "Japan",
      "arrival_date": "2025-03-22",
      "departure_date": "2025-03-24",
      "nights": 2,
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
    },
    {
      "date": "2025-03-20",
      "location": "Kyoto",
      "activity_type": "cultural",
      "description": "Traditional tea ceremony",
      "is_adventure_sport": false,
      "risk_level": "low",
      "confidence": 0.89
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
    ],
    "confidence": 0.91
  },
  
  "risk_factors": {
    "extreme_sports": false,  // Base jumping, skydiving, etc.
    "water_sports": false,  // Scuba diving, water skiing, etc.
    "winter_sports": true,  // Skiing, snowboarding
    "high_altitude_activities": false,  // Mountain climbing >4000m
    "motorized_sports": false,  // Motor racing, motorbike touring
    "group_travel": true,  // Group tours vs solo travel (affects risk)
    "remote_locations": false,  // Remote areas with limited medical facilities
    "political_risk_destinations": false,  // Destinations with travel advisories
    "confidence": 0.88
  },
  
  "trip_characteristics": {
    "is_group_tour": false,
    "is_solo_travel": false,
    "group_size": 2,
    "includes_children": false,
    "includes_seniors": false,  // Age 70+
    "confidence": 0.85
  },
  
  "travelers": [
    {
      "name": {
        "first": "John",
        "last": "Doe",
        "full": "John Doe",
        "confidence": 0.92
      },
      "age": null,
      "role": "traveler",
      "confidence": 0.90
    }
  ],
  
  "trip_structure": {
    "trip_type": "multi_city",
    "number_of_destinations": 3,
    "requires_internal_travel": true,
    "internal_transport": ["train", "bus"],
    "confidence": 0.88
  },
  
  "low_confidence_fields": ["internal_transport"],
  "missing_fields": ["traveler_ages", "pre_existing_conditions", "trip_value"]
}
```

---

## 4. 🛂 Visa Application

**Purpose**: Extract trip purpose, duration, and travel intent

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "document_type": "visa_application",
  "extracted_at": "2025-01-15T10:30:00Z",
  "confidence_threshold": 0.90,
  "source_filename": "visa_application.pdf",
  
  "visa_details": {
    "visa_type": "Tourist",
    "destination_country": "Japan",
    "entry_type": "Single",
    "validity_period": {
      "start": "2025-03-01",
      "end": "2025-06-01",
      "confidence": 0.93
    },
    "confidence": 0.92
  },
  
  "applicant": {
    "name": {
      "first": "John",
      "last": "Doe",
      "full": "John Doe",
      "confidence": 0.94
    },
    "date_of_birth": "1990-05-15",
    "age": 34,
    "passport_number": "E12345678",
    "nationality": "Singaporean",
    "confidence": 0.91
  },
  
  "trip_purpose": {
    "primary_purpose": "Tourism",
    "detailed_purpose": "Sightseeing and cultural activities",
    "is_business": false,
    "is_medical_treatment": false,
    "confidence": 0.90
  },
  
  "planned_trip": {
    "intended_arrival_date": "2025-03-15",
    "intended_departure_date": "2025-03-22",
    "duration_days": 7,
    "destination_cities": ["Tokyo", "Kyoto"],
    "confidence": 0.91
  },
  
  "accommodation_info": {
    "has_hotel_booking": true,
    "hotel_name": "Grand Tokyo Hotel",
    "hotel_address": "Tokyo, Japan",
    "confidence": 0.88
  },
  
  "financial_support": {
    "has_sufficient_funds": true,
    "estimated_trip_cost": {
      "amount": 5000.00,
      "currency": "SGD",
      "confidence": 0.85
    },
    "confidence": 0.85
  },
  
  "travel_history": {
    "has_previous_travel": true,
    "previous_destinations": ["Thailand", "Malaysia"],
    "confidence": 0.87
  },
  
  "low_confidence_fields": ["estimated_trip_cost", "travel_history"],
  "missing_fields": ["other_travelers", "pre_existing_conditions"]
}
```

---

## 5. 🔄 Normalized Structure (For Policy Recommendation)

**Purpose**: Merge available document types into a unified structure for policy recommendation. Works with partial information - doesn't require all document types.

**Note**: Only merges information from documents that are actually uploaded. Missing documents won't prevent policy recommendation.

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "normalized_at": "2025-01-15T10:35:00Z",
  "source_documents": [
    {
      "type": "flight_confirmation",
      "filename": "flight_confirmation.pdf",
      "extracted_at": "2025-01-15T10:30:00Z"
    },
    {
      "type": "hotel_booking",
      "filename": "hotel_confirmation.pdf",
      "extracted_at": "2025-01-15T10:31:00Z"
    }
  ],
  "available_document_types": ["flight_confirmation", "hotel_booking"],
  "missing_document_types": ["itinerary", "visa_application"],  // Not uploaded, will ask if needed
  
  "travelers": [
    {
      "name": {
        "first": "John",
        "last": "Doe",
        "full": "John Doe",
        "confidence": 0.94
      },
      "age": 34,  // From visa application or follow-up question
      "confidence": 0.91,
      "pre_existing_conditions": {
        "has_conditions": false,
        "confidence": 0.90,
        "conditions": [],
        "last_treated": null,
        "hospitalizations_12_months": {
          "has_hospitalizations": false,
          "count": 0,
          "longest_stay_days": 0,
          "confidence": 0.90
        },
        "treatment_changes_30_days": {
          "has_changes": false,
          "confidence": 0.90
        },
        "stability": "stable"
      }
    }
  ],
  
  "trip_details": {
    "destination": {
      "country": "Japan",
      "cities": ["Tokyo", "Kyoto"],
      "confidence": 0.92
    },
    "departure_date": {
      "value": "2025-03-15",
      "confidence": 0.93,
      "sources": ["flight_confirmation", "hotel_booking"]
    },
    "return_date": {
      "value": "2025-03-22",
      "confidence": 0.93,
      "sources": ["flight_confirmation", "hotel_booking"]
    },
    "duration_days": {
      "value": 7,
      "confidence": 0.95,
      "sources": ["flight_confirmation", "hotel_booking", "visa_application"]
    },
    "trip_type": {
      "value": "single_return",
      "confidence": 0.90,
      "sources": ["flight_confirmation"]
    },
    "origin": {
      "value": "Singapore",
      "confidence": 0.95
    }
  },
  
  "activities": {
    "adventure_sports": {
      "value": true,
      "confidence": 0.91,
      "sources": ["itinerary"],
      "activities_list": [
        {
          "type": "skiing",
          "date": "2025-03-17",
          "location": "Tokyo",
          "confidence": 0.91
        }
      ]
    },
    "activity_types": ["sightseeing", "adventure", "cultural"],
    "confidence": 0.91
  },
  
  "trip_value": {
    "total_cost": {
      "amount": 5350.00,
      "currency": "SGD",
      "confidence": 0.90,
      "breakdown": {
        "flights": {
          "amount": 1850.00,
          "currency": "SGD",
          "details": [
            {"traveler": "John Doe", "amount": 650.00, "class": "Economy"},
            {"traveler": "Jane Doe", "amount": 1200.00, "class": "Business"}
          ],
          "sources": ["flight_confirmation"]
        },
        "hotel": {
          "amount": 3500.00,
          "currency": "SGD",
          "details": {
            "total": 3500.00,
            "per_night": 500.00,
            "nights": 7
          },
          "sources": ["hotel_booking"]
        },
        "other": {
          "amount": 0.00,
          "currency": "SGD",
          "details": "Additional costs not found in documents"
        }
      },
      "sources": ["flight_confirmation", "hotel_booking"]
    }
  },
  
  "airline_info": {
    "airline": "Scoot",
    "is_scoot": true,
    "confidence": 0.92,
    "sources": ["flight_confirmation"]
  },
  
  "low_confidence_fields": [],
  "missing_critical_fields": [
    "traveler_ages",  // Need follow-up if not in documents
    "pre_existing_conditions"  // Need follow-up question
  ],
  
  "policy_recommendation": {
    "recommended_policy": "Scootsurance",
    "recommended_tier": "Elite",
    "reasoning": "Traveling on Scoot airline, no pre-existing conditions, adventure sports detected",
    "eligibility_check": {
      "age_eligible": true,
      "pre_ex_eligible": null,
      "trip_type_eligible": true,
      "duration_eligible": true,
      "scoot_airline": true
    },
    "confidence": 0.88
  }
}
```

---

## Document Type Detection

The system should detect document type automatically using LLM (not hardcoded keywords):

```python
def detect_document_type(ocr_text: str, llm_client) -> str:
    """Detect document type from OCR text using LLM."""
    prompt = f"""Analyze this document text and determine its type.
    
Document text (first 2000 characters):
{ocr_text[:2000]}

Classify as ONE of these types:
1. flight_confirmation - Flight tickets, booking confirmations, PNR references
2. hotel_booking - Hotel reservations, accommodation confirmations
3. itinerary - Travel schedules, day-by-day plans, activity lists
4. visa_application - Visa forms, entry permits, consulate documents
5. unknown - Cannot determine type

Respond with ONLY the type name (e.g., "flight_confirmation")."""
    
    response = llm_client.generate(prompt, temperature=0.1)
    detected_type = response.strip().lower()
    
    if detected_type in ["flight_confirmation", "hotel_booking", "itinerary", "visa_application"]:
        return detected_type
    else:
        return "unknown"
```

## Adventure Sports Detection

Adventure sports detection should use LLM, not hardcoded keywords:

```python
def detect_adventure_sports(activities_text: str, llm_client) -> Dict[str, Any]:
    """Detect adventure sports from activities using LLM."""
    prompt = f"""Analyze these travel activities and identify adventure sports or high-risk activities.

Activities:
{activities_text}

Identify:
1. Adventure sports (skiing, scuba diving, hiking, etc.)
2. Extreme sports (skydiving, base jumping, etc.)
3. Water sports (scuba diving, water skiing, etc.)
4. Winter sports (skiing, snowboarding, etc.)
5. High-altitude activities (mountain climbing >4000m)
6. Motorized sports (motor racing, motorbike touring)

Respond with JSON:
{{
    "has_adventure_sports": true/false,
    "activities": [
        {{
            "type": "skiing",
            "risk_level": "medium",
            "requires_special_coverage": true
        }}
    ],
    "extreme_sports": true/false,
    "water_sports": true/false,
    "winter_sports": true/false,
    "high_altitude": true/false,
    "motorized_sports": true/false
}}"""
    
    response = llm_client.generate(prompt, temperature=0.1)
    return json.loads(response)
```

---

## Implementation Notes

1. **Multiple Documents**: Users can upload multiple document types in one session (e.g., flight + hotel + itinerary). They'll be merged into the normalized structure.

2. **Partial Information**: The system works with partial information. Users don't need all document types - missing documents won't prevent policy recommendation.

3. **Confidence Scoring**: 
   - **≥0.90 (High)**: Automatically included, no confirmation needed
   - **0.80-0.89 (Medium)**: Included but flagged for user confirmation
   - **<0.80 (Low)**: Not included, system asks user to manually input

4. **Missing Fields**: Fields below 0.80 threshold or not found are listed in `missing_fields` for follow-up questions.

5. **Source Tracking**: Normalized structure tracks which document(s) provided each piece of information.

6. **Conflict Resolution**: If multiple documents provide conflicting info, use highest confidence or most recent.

7. **Trip Value Aggregation**: Automatically sums costs from multiple documents (flights + hotel + other) with detailed breakdown showing source of each cost component.

8. **LLM-Based Detection**: Document type detection and adventure sports detection use LLM, not hardcoded keywords, for better accuracy and flexibility.

