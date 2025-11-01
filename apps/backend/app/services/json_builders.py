"""JSON builders for Ancileo API formats and metadata storage."""

from typing import Dict, Any, Optional, List
from datetime import date


def build_ancileo_quotation_json(
    trip_details: Dict[str, Any],
    travelers_data: Dict[str, Any],
    preferences: Dict[str, Any]
) -> Dict[str, Any]:
    """Build Ancileo quotation request JSON format with adventure_sports_activities field.
    
    This builds the full Ancileo API request format including the adventure_sports_activities
    field. When calling the Ancileo API, remove the adventure_sports_activities field before
    sending. For local tier calculations (Standard, Premier), use adventure_sports_activities.
    
    Args:
        trip_details: Dictionary with destination, departure_date, return_date, departure_country,
                     arrival_country, adults_count, children_count
        travelers_data: Dictionary with ages list and count
        preferences: Dictionary with adventure_sports boolean
        
    Returns:
        Dictionary matching Ancileo quotation request format:
        {
            "market": "SG",
            "languageCode": "en",
            "channel": "white-label",
            "deviceType": "DESKTOP",
            "context": {
                "tripType": "RT" or "ST",
                "departureDate": "YYYY-MM-DD",
                "departureCountry": "SG",
                "arrivalCountry": "JP",
                "adultsCount": 2,
                "childrenCount": 0,
                "returnDate": "YYYY-MM-DD"  // if RT
            },
            "adventure_sports_activities": true/false
        }
    """
    # Determine trip type (RT if return_date exists, ST otherwise)
    trip_type = "RT" if trip_details.get("return_date") else "ST"
    
    # Format dates
    departure_date = trip_details.get("departure_date")
    return_date = trip_details.get("return_date")
    
    if isinstance(departure_date, date):
        departure_date_str = departure_date.strftime("%Y-%m-%d")
    else:
        departure_date_str = str(departure_date) if departure_date else None
    
    if isinstance(return_date, date):
        return_date_str = return_date.strftime("%Y-%m-%d")
    else:
        return_date_str = str(return_date) if return_date else None
    
    # Get Ancileo API required fields
    departure_country = trip_details.get("departure_country", "SG")
    arrival_country = trip_details.get("arrival_country", "")
    adults_count = trip_details.get("adults_count", 0)
    children_count = trip_details.get("children_count", 0)
    
    # Calculate adults/children from ages if not already set
    if adults_count == 0 and travelers_data.get("ages"):
        ages = travelers_data.get("ages", [])
        adults_count = sum(1 for age in ages if age >= 18)
        children_count = sum(1 for age in ages if age < 18)
        # Ensure at least 1 adult for Ancileo API
        if adults_count == 0 and children_count > 0:
            adults_count = 1
            children_count = max(0, children_count - 1)
    
    # Build context object
    context = {
        "tripType": trip_type,
        "departureDate": departure_date_str,
        "departureCountry": departure_country.upper(),
        "arrivalCountry": arrival_country.upper() if arrival_country else "",
        "adultsCount": adults_count,
        "childrenCount": children_count
    }
    
    # Add returnDate only for round trip
    if trip_type == "RT" and return_date_str:
        context["returnDate"] = return_date_str
    
    # Build full quotation JSON
    quotation_json = {
        "market": "SG",
        "languageCode": "en",
        "channel": "white-label",
        "deviceType": "DESKTOP",
        "context": context,
        "adventure_sports_activities": preferences.get("adventure_sports", False)
    }
    
    return quotation_json


def build_ancileo_purchase_json(
    user_data: Dict[str, Any],
    travelers_data: Optional[Dict[str, Any]] = None,
    additional_travelers: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """Build Ancileo purchase request JSON format with minimal required fields.
    
    Uses minimal required fields (id, firstName, lastName, email) for primary traveler
    from user data. Additional travelers can be provided via additional_travelers list.
    
    Args:
        user_data: Dictionary with user's first_name, last_name, email
        travelers_data: Optional dictionary with traveler information (ages, etc.)
        additional_travelers: Optional list of additional traveler dictionaries with
                            id, firstName, lastName, email fields
        
    Returns:
        Dictionary matching Ancileo purchase format:
        {
            "insureds": [{
                "id": "1",
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com"
            }],
            "mainContact": {
                "id": "1",
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com"
            }
        }
    """
    # Extract primary traveler from user data
    primary_traveler = {
        "id": "1",
        "firstName": user_data.get("first_name", ""),
        "lastName": user_data.get("last_name", ""),
        "email": user_data.get("email", "")
    }
    
    # Build insureds list
    insureds = [primary_traveler]
    
    # Add additional travelers if provided
    if additional_travelers:
        for idx, traveler in enumerate(additional_travelers, start=2):
            traveler_dict = {
                "id": str(idx),
                "firstName": traveler.get("firstName", traveler.get("first_name", "")),
                "lastName": traveler.get("lastName", traveler.get("last_name", "")),
                "email": traveler.get("email", primary_traveler["email"])  # Default to primary's email
            }
            insureds.append(traveler_dict)
    
    # Main contact is the same as primary traveler
    main_contact = primary_traveler.copy()
    
    purchase_json = {
        "insureds": insureds,
        "mainContact": main_contact
    }
    
    return purchase_json


def build_trip_metadata_json(
    session_id: str,
    user_id: str,
    document_data: Optional[List[Dict[str, Any]]] = None,
    chat_history_references: Optional[List[Dict[str, Any]]] = None,
    conversation_flow: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Build trip metadata JSON for storing session, document, and chat references.
    
    Args:
        session_id: Chat session ID
        user_id: User ID
        document_data: Optional list of document dictionaries with document_id, document_type,
                      file_path, extracted_at
        chat_history_references: Optional list of chat history message references
        conversation_flow: Optional dictionary with timestamps for conversation milestones
        
    Returns:
        Dictionary with metadata:
        {
            "session_id": "...",
            "user_id": "...",
            "document_references": [
                {
                    "document_id": "...",
                    "document_type": "flight_confirmation",
                    "file_path": "...",
                    "extracted_at": "..."
                }
            ],
            "chat_history_references": [...],
            "conversation_flow": {
                "started_at": "...",
                "document_uploaded_at": "...",
                "quote_generated_at": "..."
            }
        }
    """
    metadata = {
        "session_id": session_id,
        "user_id": user_id
    }
    
    # Build document references
    if document_data:
        document_references = []
        for doc in document_data:
            extracted_json = doc.get("extracted_json", {})
            doc_ref = {
                "document_id": doc.get("document_id"),
                "document_type": extracted_json.get("document_type", doc.get("document_type")),
                "file_path": doc.get("file_path"),
                "filename": doc.get("filename"),
                "extracted_at": doc.get("extracted_at", doc.get("uploaded_at"))
            }
            # Remove None values
            doc_ref = {k: v for k, v in doc_ref.items() if v is not None}
            document_references.append(doc_ref)
        
        if document_references:
            metadata["document_references"] = document_references
    
    # Add chat history references if provided
    if chat_history_references:
        metadata["chat_history_references"] = chat_history_references
    
    # Add conversation flow timestamps if provided
    if conversation_flow:
        metadata["conversation_flow"] = conversation_flow
    
    return metadata

