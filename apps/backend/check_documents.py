#!/usr/bin/env python3
"""Script to check if documents were successfully stored in the database."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.db import SessionLocal
from app.models.flight import Flight
from app.models.hotel import Hotel
from app.models.visa import Visa
from app.models.itinerary import Itinerary
import json

def check_documents(session_id: str = None, user_id: str = None):
    """Check documents in database."""
    db = SessionLocal()
    
    try:
        print("=" * 70)
        print("📋 CHECKING DOCUMENTS IN DATABASE")
        print("=" * 70)
        
        # Flights
        flights_query = db.query(Flight)
        if session_id:
            flights_query = flights_query.filter(Flight.session_id == session_id)
        if user_id:
            flights_query = flights_query.filter(Flight.user_id == user_id)
        flights = flights_query.order_by(Flight.created_at.desc()).limit(10).all()
        
        print(f"\n✈️  FLIGHTS ({len(flights)} found):")
        for flight in flights:
            print(f"\n  📄 Document ID: {flight.id}")
            print(f"     Session ID: {flight.session_id}")
            print(f"     Filename: {flight.original_filename or flight.source_filename}")
            print(f"     Airline: {flight.airline_name} ({flight.airline_code})")
            print(f"     Destination: {flight.destination_city}, {flight.destination_country}")
            print(f"     Departure: {flight.departure_date}")
            print(f"     JSON File Path: {flight.json_file_path}")
            print(f"     Extracted Data: {'✅ Present' if flight.extracted_data else '❌ Missing'}")
            if flight.extracted_data:
                print(f"     Extracted Data Keys: {list(flight.extracted_data.keys())[:5]}...")
                # Show sample of extracted_data
                if 'airline' in flight.extracted_data:
                    print(f"     Airline (from JSON): {flight.extracted_data.get('airline')}")
        
        # Hotels
        hotels_query = db.query(Hotel)
        if session_id:
            hotels_query = hotels_query.filter(Hotel.session_id == session_id)
        if user_id:
            hotels_query = hotels_query.filter(Hotel.user_id == user_id)
        hotels = hotels_query.order_by(Hotel.created_at.desc()).limit(10).all()
        
        print(f"\n🏨 HOTELS ({len(hotels)} found):")
        for hotel in hotels:
            print(f"\n  📄 Document ID: {hotel.id}")
            print(f"     Session ID: {hotel.session_id}")
            print(f"     Filename: {hotel.original_filename or hotel.source_filename}")
            print(f"     Hotel: {hotel.hotel_name}")
            print(f"     Extracted Data: {'✅ Present' if hotel.extracted_data else '❌ Missing'}")
        
        # Visas
        visas_query = db.query(Visa)
        if session_id:
            visas_query = visas_query.filter(Visa.session_id == session_id)
        if user_id:
            visas_query = visas_query.filter(Visa.user_id == user_id)
        visas = visas_query.order_by(Visa.created_at.desc()).limit(10).all()
        
        print(f"\n🛂 VISAS ({len(visas)} found):")
        for visa in visas:
            print(f"\n  📄 Document ID: {visa.id}")
            print(f"     Session ID: {visa.session_id}")
            print(f"     Filename: {visa.original_filename or visa.source_filename}")
            print(f"     Visa Type: {visa.visa_type}")
            print(f"     Extracted Data: {'✅ Present' if visa.extracted_data else '❌ Missing'}")
        
        # Itineraries
        itineraries_query = db.query(Itinerary)
        if session_id:
            itineraries_query = itineraries_query.filter(Itinerary.session_id == session_id)
        if user_id:
            itineraries_query = itineraries_query.filter(Itinerary.user_id == user_id)
        itineraries = itineraries_query.order_by(Itinerary.created_at.desc()).limit(10).all()
        
        print(f"\n🗺️  ITINERARIES ({len(itineraries)} found):")
        for itinerary in itineraries:
            print(f"\n  📄 Document ID: {itinerary.id}")
            print(f"     Session ID: {itinerary.session_id}")
            print(f"     Filename: {itinerary.original_filename or itinerary.source_filename}")
            print(f"     Trip Title: {itinerary.trip_title}")
            print(f"     Extracted Data: {'✅ Present' if itinerary.extracted_data else '❌ Missing'}")
        
        print("\n" + "=" * 70)
        print("✅ Check complete!")
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def show_document_json(document_id: str, doc_type: str = "flight"):
    """Show the full extracted JSON for a specific document."""
    db = SessionLocal()
    
    try:
        if doc_type == "flight":
            doc = db.query(Flight).filter(Flight.id == document_id).first()
        elif doc_type == "hotel":
            doc = db.query(Hotel).filter(Hotel.id == document_id).first()
        elif doc_type == "visa":
            doc = db.query(Visa).filter(Visa.id == document_id).first()
        elif doc_type == "itinerary":
            doc = db.query(Itinerary).filter(Itinerary.id == document_id).first()
        else:
            print(f"❌ Unknown document type: {doc_type}")
            return
        
        if not doc:
            print(f"❌ Document not found: {document_id}")
            return
        
        print("=" * 70)
        print(f"📄 DOCUMENT JSON: {document_id}")
        print("=" * 70)
        print(f"Type: {doc_type}")
        print(f"Filename: {doc.original_filename or doc.source_filename}")
        print(f"Session ID: {doc.session_id}")
        print(f"\n📋 EXTRACTED DATA (JSON):")
        print(json.dumps(doc.extracted_data, indent=2, default=str))
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Check documents in database")
    parser.add_argument("--session-id", help="Filter by session ID")
    parser.add_argument("--user-id", help="Filter by user ID")
    parser.add_argument("--document-id", help="Show full JSON for specific document")
    parser.add_argument("--type", choices=["flight", "hotel", "visa", "itinerary"], 
                       default="flight", help="Document type (for --document-id)")
    
    args = parser.parse_args()
    
    if args.document_id:
        show_document_json(args.document_id, args.type)
    else:
        check_documents(args.session_id, args.user_id)

