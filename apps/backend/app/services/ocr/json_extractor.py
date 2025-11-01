"""JSON extraction service for structured data extraction from OCR text."""

from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import uuid
from pathlib import Path

from app.agents.llm_client import GroqLLMClient
from app.services.ocr.document_detector import DocumentTypeDetector


class JSONExtractor:
    """Extract structured JSON data from OCR text with confidence scoring."""
    
    def __init__(self):
        self.llm_client = GroqLLMClient()
        self.detector = DocumentTypeDetector()
        self.high_confidence_threshold = 0.90
        self.medium_confidence_threshold = 0.80
    
    def extract(
        self,
        ocr_text: str,
        session_id: str,
        filename: str,
        language: str = 'eng',
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Extract structured JSON data from OCR text.
        
        Args:
            ocr_text: Extracted text from OCR
            session_id: Chat session ID
            filename: Original filename
            language: Language code
            
        Returns:
            Dictionary with extracted data and metadata
        """
        # Step 1: Detect document type
        detection_result = self.detector.detect_type(ocr_text)
        document_type = detection_result.get("type", "unknown")
        
        print(f"📄 Detected document type: {document_type} (confidence: {detection_result.get('confidence', 0)})")
        
        # Step 2: Extract type-specific data
        if document_type == "unknown":
            return self._create_unknown_document_json(session_id, filename, ocr_text)
        
        # Step 3: Extract structured data based on type
        extraction_function = {
            "flight_confirmation": self._extract_flight_confirmation,
            "hotel_booking": self._extract_hotel_booking,
            "itinerary": self._extract_itinerary,
            "visa_application": self._extract_visa_application
        }.get(document_type)
        
        if not extraction_function:
            return self._create_unknown_document_json(session_id, filename, ocr_text)
        
        extracted_data = extraction_function(ocr_text, session_id, filename, user_message)
        
        # Step 4: Filter by confidence and categorize fields
        filtered_data = self._filter_by_confidence(extracted_data)
        
        # Step 5: Save JSON file
        json_path = self._save_json_file(filtered_data, session_id, document_type)
        filtered_data["json_file_path"] = json_path
        
        return filtered_data
    
    def _extract_flight_confirmation(
        self,
        ocr_text: str,
        session_id: str,
        filename: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data from flight confirmation document."""
        user_context = ""
        if user_message:
            user_context = f"\n\nUser's message/context: {user_message}\nPlease use this context to help interpret the document and extract the information more accurately."
        
        prompt = f"""Extract structured information from this flight confirmation document.{user_context}

Document text:
{ocr_text[:3000]}

Extract the following information with confidence scores (0.0-1.0):
- Trip type: "one_way" if no return flight, "return" if return flight exists
- Airline name and code for outbound flight (going)
- Airline name and code for inbound flight (returning) - only if return flight exists
- Departure date, time, airport code, airport name
- Return/arrival date, time, airport code, airport name (if return flight exists)
- Flight numbers (outbound and inbound)
- Destination country and city
- Traveler names (first, last, full)
- Ticket numbers, service class (Economy/Business/First/Premium Economy), seat assignments, seat types
- Individual ticket costs per traveler
- Total trip cost
- Booking reference (PNR, booking number)
- Trip duration in days

IMPORTANT: Determine trip_type based on whether a return flight exists. If return flight exists, set trip_type to "return" and include inbound airline. If no return flight, set trip_type to "one_way" and inbound airline should be null.

Respond with ONLY a valid JSON object matching this structure:
{{
    "session_id": "{session_id}",
    "document_type": "flight_confirmation",
    "extracted_at": "{datetime.utcnow().isoformat()}Z",
    "source_filename": "{filename}",
    "trip_type": "return",
    "airline": {{
        "outbound": {{"name": "Scoot", "code": "TR", "confidence": 0.92}},
        "inbound": {{"name": "Scoot", "code": "TR", "confidence": 0.92}}
    }},
    "flight_details": {{
        "departure": {{"date": "2025-03-15", "time": "14:30", "airport_code": "SIN", "airport_name": "Singapore Changi Airport", "confidence": 0.91}},
        "return": {{"date": "2025-03-22", "time": "18:45", "airport_code": "NRT", "airport_name": "Narita International Airport", "confidence": 0.91}},
        "flight_numbers": {{"outbound": "TR892", "inbound": "TR893", "confidence": 0.93}}
    }},
    "destination": {{"country": "Japan", "city": "Tokyo", "airport_code": "NRT", "confidence": 0.92}},
    "travelers": [
        {{
            "name": {{"first": "John", "last": "Doe", "full": "John Doe", "confidence": 0.94}},
            "ticket": {{
                "ticket_number": "1234567890123",
                "class": {{"service_class": "Economy", "code": "Y", "confidence": 0.92}},
                "seat_assignment": "12A",
                "seat_type": "Standard",
                "cost": {{"amount": 650.00, "currency": "SGD", "confidence": 0.88}},
                "confidence": 0.91
            }}
        }}
    ],
    "trip_duration": {{"days": 7, "calculated_from_dates": true, "confidence": 0.95}},
    "trip_value": {{
        "total_cost": {{"amount": 1850.00, "currency": "SGD", "confidence": 0.90}},
        "breakdown": [
            {{"traveler": "John Doe", "amount": 650.00, "currency": "SGD", "class": "Economy", "confidence": 0.88}}
        ]
    }},
    "booking_reference": {{"pnr": "ABC123", "booking_number": "BK456789", "confidence": 0.93}}
}}

Only include fields where confidence >= 0.80. For fields below 0.80, set them to null."""
        
        return self._call_llm_extraction(prompt, session_id, filename, "flight_confirmation")
    
    def _extract_hotel_booking(
        self,
        ocr_text: str,
        session_id: str,
        filename: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data from hotel booking document."""
        user_context = ""
        if user_message:
            user_context = f"\n\nUser's message/context: {user_message}\nPlease use this context to help interpret the document and extract the information more accurately."
        
        prompt = f"""Extract structured information from this hotel booking confirmation.{user_context}

Document text:
{ocr_text[:3000]}

Extract the following information with confidence scores (0.0-1.0):
- Hotel name, chain, star rating
- Location: address (street, city, country, postal code), coordinates if available
- Booking dates: check-in date/time, check-out date/time, number of nights
- Room details: room type, number of rooms, occupancy, smoking preference
- Investment value: total cost, per-night cost, deposit paid, refundable status, cancellation policy
- Guests: names (first, last, full), age if available, primary guest flag, adult/child status
- Booking reference: confirmation number, booking ID

Respond with ONLY a valid JSON object matching this structure:
{{
    "session_id": "{session_id}",
    "document_type": "hotel_booking",
    "extracted_at": "{datetime.utcnow().isoformat()}Z",
    "source_filename": "{filename}",
    "hotel_details": {{
        "name": "Grand Tokyo Hotel",
        "chain": null,
        "star_rating": 4,
        "confidence": 0.92
    }},
    "location": {{
        "address": {{
            "street": "1-2-3 Shibuya",
            "city": "Tokyo",
            "country": "Japan",
            "postal_code": "150-0001",
            "full": "1-2-3 Shibuya, Tokyo, Japan 150-0001",
            "confidence": 0.91
        }},
        "coordinates": {{
            "latitude": null,
            "longitude": null,
            "confidence": 0.0
        }}
    }},
    "booking_dates": {{
        "check_in": {{"date": "2025-03-15", "time": "15:00", "confidence": 0.93}},
        "check_out": {{"date": "2025-03-22", "time": "11:00", "confidence": 0.93}},
        "nights": {{"count": 7, "calculated_from_dates": true, "confidence": 0.95}}
    }},
    "room_details": {{
        "room_type": "Deluxe Double Room",
        "number_of_rooms": 1,
        "occupancy": 2,
        "smoking_preference": "Non-smoking",
        "confidence": 0.90
    }},
    "investment_value": {{
        "total_cost": {{"amount": 3500.00, "currency": "SGD", "confidence": 0.92}},
        "per_night": {{"amount": 500.00, "currency": "SGD", "confidence": 0.92}},
        "deposit_paid": {{"amount": 700.00, "currency": "SGD", "confidence": 0.88}},
        "refundable": true,
        "cancellation_policy": "Free cancellation until 48 hours before check-in",
        "confidence": 0.85
    }},
    "guests": [
        {{
            "name": {{"first": "John", "last": "Doe", "full": "John Doe", "confidence": 0.94}},
            "age": null,
            "is_primary_guest": true,
            "is_adult": true,
            "confidence": 0.91
        }}
    ],
    "booking_reference": {{
        "confirmation_number": "HTL789456",
        "booking_id": "BK987654",
        "confidence": 0.93
    }}
}}

Only include fields where confidence >= 0.80. For fields below 0.80, set them to null."""
        return self._call_llm_extraction(prompt, session_id, filename, "hotel_booking")
    
    def _extract_itinerary(
        self,
        ocr_text: str,
        session_id: str,
        filename: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data from itinerary document."""
        user_context = ""
        if user_message:
            user_context = f"\n\nUser's message/context: {user_message}\nPlease use this context to help interpret the document and extract the information more accurately."
        
        prompt = f"""Extract structured information from this travel itinerary.{user_context}

Document text:
{ocr_text[:3000]}

Extract the following information with confidence scores (0.0-1.0):
- Trip overview: title, duration in days, start date, end date
- Destinations: cities, countries, arrival/departure dates, nights per destination
- Activities: dates, locations, activity types, descriptions, adventure sports detection, risk levels
- Adventure sports detected: has_adventure_sports flag, list of adventure activities with types, dates, locations, risk levels
- Risk factors: extreme_sports, water_sports, winter_sports, high_altitude_activities, motorized_sports, group_travel, remote_locations, political_risk_destinations
- Trip characteristics: is_group_tour, is_solo_travel, group_size, includes_children, includes_seniors (70+)
- Travelers: names (first, last, full), age if available, role
- Trip structure: trip_type (single_return, multi_city, annual), number_of_destinations, requires_internal_travel, internal_transport methods

IMPORTANT: Carefully detect adventure sports activities such as skiing, snowboarding, scuba diving, water skiing, mountain climbing, bungee jumping, skydiving, etc.

Respond with ONLY a valid JSON object matching this structure:
{{
    "session_id": "{session_id}",
    "document_type": "itinerary",
    "extracted_at": "{datetime.utcnow().isoformat()}Z",
    "source_filename": "{filename}",
    "trip_overview": {{
        "title": "Japan Adventure Tour",
        "duration_days": 10,
        "start_date": "2025-03-15",
        "end_date": "2025-03-24",
        "confidence": 0.91
    }},
    "destinations": [
        {{
            "city": "Tokyo",
            "country": "Japan",
            "arrival_date": "2025-03-15",
            "departure_date": "2025-03-18",
            "nights": 3,
            "confidence": 0.92
        }}
    ],
    "activities": [
        {{
            "date": "2025-03-17",
            "location": "Tokyo",
            "activity_type": "adventure",
            "description": "Skiing at nearby resort",
            "is_adventure_sport": true,
            "risk_level": "medium",
            "requires_special_coverage": true,
            "confidence": 0.91
        }}
    ],
    "adventure_sports_detected": {{
        "has_adventure_sports": true,
        "activities": [
            {{
                "type": "skiing",
                "date": "2025-03-17",
                "location": "Tokyo",
                "risk_level": "medium",
                "confidence": 0.91
            }}
        ],
        "confidence": 0.91
    }},
    "risk_factors": {{
        "extreme_sports": false,
        "water_sports": false,
        "winter_sports": true,
        "high_altitude_activities": false,
        "motorized_sports": false,
        "group_travel": true,
        "remote_locations": false,
        "political_risk_destinations": false,
        "confidence": 0.88
    }},
    "trip_characteristics": {{
        "is_group_tour": false,
        "is_solo_travel": false,
        "group_size": 2,
        "includes_children": false,
        "includes_seniors": false,
        "confidence": 0.85
    }},
    "travelers": [
        {{
            "name": {{"first": "John", "last": "Doe", "full": "John Doe", "confidence": 0.92}},
            "age": null,
            "role": "traveler",
            "confidence": 0.90
        }}
    ],
    "trip_structure": {{
        "trip_type": "multi_city",
        "number_of_destinations": 3,
        "requires_internal_travel": true,
        "internal_transport": ["train", "bus"],
        "confidence": 0.88
    }}
}}

Only include fields where confidence >= 0.80. For fields below 0.80, set them to null."""
        return self._call_llm_extraction(prompt, session_id, filename, "itinerary")
    
    def _extract_visa_application(
        self,
        ocr_text: str,
        session_id: str,
        filename: str,
        user_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data from visa application document."""
        user_context = ""
        if user_message:
            user_context = f"\n\nUser's message/context: {user_message}\nPlease use this context to help interpret the document and extract the information more accurately."
        
        prompt = f"""Extract structured information from this visa application.{user_context}

Document text:
{ocr_text[:3000]}

Extract the following information with confidence scores (0.0-1.0):
- Visa details: visa type (Tourist/Business/etc), destination country, entry type (Single/Multiple), validity period (start/end dates)
- Applicant: name (first, last, full), date of birth, age (calculated), passport number, nationality
- Trip purpose: primary purpose, detailed purpose, is_business flag, is_medical_treatment flag
- Planned trip: intended arrival date, intended departure date, duration in days, destination cities
- Accommodation info: has_hotel_booking flag, hotel name, hotel address
- Financial support: has_sufficient_funds flag, estimated trip cost (amount, currency)
- Travel history: has_previous_travel flag, previous destinations list

Respond with ONLY a valid JSON object matching this structure:
{{
    "session_id": "{session_id}",
    "document_type": "visa_application",
    "extracted_at": "{datetime.utcnow().isoformat()}Z",
    "source_filename": "{filename}",
    "visa_details": {{
        "visa_type": "Tourist",
        "destination_country": "Japan",
        "entry_type": "Single",
        "validity_period": {{
            "start": "2025-03-01",
            "end": "2025-06-01",
            "confidence": 0.93
        }},
        "confidence": 0.92
    }},
    "applicant": {{
        "name": {{"first": "John", "last": "Doe", "full": "John Doe", "confidence": 0.94}},
        "date_of_birth": "1990-05-15",
        "age": 34,
        "passport_number": "E12345678",
        "nationality": "Singaporean",
        "confidence": 0.91
    }},
    "trip_purpose": {{
        "primary_purpose": "Tourism",
        "detailed_purpose": "Sightseeing and cultural activities",
        "is_business": false,
        "is_medical_treatment": false,
        "confidence": 0.90
    }},
    "planned_trip": {{
        "intended_arrival_date": "2025-03-15",
        "intended_departure_date": "2025-03-22",
        "duration_days": 7,
        "destination_cities": ["Tokyo", "Kyoto"],
        "confidence": 0.91
    }},
    "accommodation_info": {{
        "has_hotel_booking": true,
        "hotel_name": "Grand Tokyo Hotel",
        "hotel_address": "Tokyo, Japan",
        "confidence": 0.88
    }},
    "financial_support": {{
        "has_sufficient_funds": true,
        "estimated_trip_cost": {{
            "amount": 5000.00,
            "currency": "SGD",
            "confidence": 0.85
        }},
        "confidence": 0.85
    }},
    "travel_history": {{
        "has_previous_travel": true,
        "previous_destinations": ["Thailand", "Malaysia"],
        "confidence": 0.87
    }}
}}

Only include fields where confidence >= 0.80. For fields below 0.80, set them to null."""
        return self._call_llm_extraction(prompt, session_id, filename, "visa_application")
    
    def _call_llm_extraction(
        self,
        prompt: str,
        session_id: str,
        filename: str,
        document_type: str
    ) -> Dict[str, Any]:
        """Call LLM for extraction."""
        try:
            # Groq may not support response_format, parse JSON from text
            response = self.llm_client.client.chat.completions.create(
                model=self.llm_client.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Check if response is empty
            if not result_text:
                raise ValueError("LLM returned empty response")
            
            import re
            
            # Try to extract JSON from response (in case LLM adds extra text)
            # First try to find a JSON object (starts with {)
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                result_text = json_match.group(0)
            else:
                # If no JSON found, raise error
                raise ValueError(f"Could not find JSON in LLM response. Response: {result_text[:200]}")
            
            # Try to parse JSON
            try:
                parsed_result = json.loads(result_text)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"   Response text: {result_text[:500]}")
                raise ValueError(f"Failed to parse JSON from LLM response: {str(e)}")
            
            # Handle case where LLM returns a list instead of a dict
            if isinstance(parsed_result, list):
                print(f"⚠️  LLM returned a list instead of dict, attempting to extract first element")
                if len(parsed_result) > 0 and isinstance(parsed_result[0], dict):
                    result = parsed_result[0]
                else:
                    raise ValueError("LLM returned a list but first element is not a dict")
            elif isinstance(parsed_result, dict):
                result = parsed_result
            else:
                raise ValueError(f"LLM returned unexpected type: {type(parsed_result)}")
            
            # Ensure required metadata fields
            result["session_id"] = session_id
            result["document_type"] = document_type
            result["extracted_at"] = datetime.utcnow().isoformat() + "Z"
            result["source_filename"] = filename
            result["confidence_thresholds"] = {
                "high": self.high_confidence_threshold,
                "medium": self.medium_confidence_threshold,
                "low": self.medium_confidence_threshold
            }
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error in LLM extraction: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise so the router can handle it properly
            raise ValueError(f"JSON parsing failed: {str(e)}")
        except ValueError as e:
            # Re-raise ValueError (from our validation checks)
            raise
        except Exception as e:
            print(f"⚠️  LLM extraction failed: {e}")
            import traceback
            traceback.print_exc()
            # Re-raise so the router can handle it properly
            raise ValueError(f"LLM extraction failed: {str(e)}")
    
    def _filter_by_confidence(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter fields by confidence and categorize them."""
        high_confidence_fields = []
        low_confidence_fields = []
        missing_fields = []
        
        # Recursively filter nested structures
        filtered = self._filter_dict(data, high_confidence_fields, low_confidence_fields, missing_fields)
        
        filtered["high_confidence_fields"] = high_confidence_fields
        filtered["low_confidence_fields"] = low_confidence_fields
        filtered["missing_fields"] = missing_fields
        
        return filtered
    
    def _filter_dict(
        self,
        obj: Any,
        high_fields: List[str],
        low_fields: List[str],
        missing_fields: List[str],
        path: str = ""
    ) -> Any:
        """Recursively filter dictionary by confidence scores."""
        if isinstance(obj, dict):
            filtered = {}
            for key, value in obj.items():
                current_path = f"{path}.{key}" if path else key
                
                if key == "confidence":
                    conf = value
                    if isinstance(conf, (int, float)):
                        if conf < self.medium_confidence_threshold:
                            # Field below threshold - don't include parent
                            return None
                        elif conf < self.high_confidence_threshold:
                            low_fields.append(current_path)
                        else:
                            high_fields.append(current_path)
                    filtered[key] = value
                elif isinstance(value, dict):
                    filtered_val = self._filter_dict(value, high_fields, low_fields, missing_fields, current_path)
                    if filtered_val is not None:
                        filtered[key] = filtered_val
                elif isinstance(value, list):
                    filtered[key] = [
                        self._filter_dict(item, high_fields, low_fields, missing_fields, f"{current_path}[{i}]")
                        for i, item in enumerate(value)
                        if self._filter_dict(item, high_fields, low_fields, missing_fields, f"{current_path}[{i}]") is not None
                    ]
                else:
                    filtered[key] = value
            return filtered
        else:
            return obj
    
    def _save_json_file(
        self,
        data: Dict[str, Any],
        session_id: str,
        document_type: str
    ) -> str:
        """Save extracted data to JSON file."""
        # Create documents directory
        docs_dir = Path("apps/backend/uploads/documents")
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{session_id}_{document_type}_{timestamp}.json"
        file_path = docs_dir / filename
        
        # Save JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved JSON to: {file_path}")
        return str(file_path)
    
    def _create_unknown_document_json(
        self,
        session_id: str,
        filename: str,
        ocr_text: str
    ) -> Dict[str, Any]:
        """Create JSON structure for unknown document type."""
        return {
            "session_id": session_id,
            "document_type": "unknown",
            "extracted_at": datetime.utcnow().isoformat() + "Z",
            "source_filename": filename,
            "confidence_thresholds": {
                "high": self.high_confidence_threshold,
                "medium": self.medium_confidence_threshold,
                "low": self.medium_confidence_threshold
            },
            "ocr_text_preview": ocr_text[:500] if ocr_text else "",
            "high_confidence_fields": [],
            "low_confidence_fields": [],
            "missing_fields": ["document_type"],
            "error": "Could not determine document type"
        }

