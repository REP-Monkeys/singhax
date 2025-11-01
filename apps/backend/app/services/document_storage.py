"""Service for storing extracted document data in database."""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date
from pathlib import Path
import uuid
import os

from app.core.config import settings
from app.models.flight import Flight
from app.models.hotel import Hotel
from app.models.visa import Visa
from app.models.itinerary import Itinerary
from app.models.trip import Trip


class DocumentStorageService:
    """Service for storing extracted document data."""
    
    def __init__(self):
        """Initialize Supabase client if configured."""
        self.supabase_client = None
        self.use_cloud_storage = False
        
        # Initialize Supabase client if credentials are available
        if settings.supabase_url and settings.supabase_service_role_key:
            try:
                from supabase import create_client, Client
                self.supabase_client: Client = create_client(
                    settings.supabase_url,
                    settings.supabase_service_role_key
                )
                self.use_cloud_storage = True
                print("✓ Supabase Storage initialized for document storage")
            except ImportError:
                print("⚠️  supabase package not installed, falling back to local storage")
            except Exception as e:
                print(f"⚠️  Failed to initialize Supabase Storage: {e}, falling back to local storage")
    
    def store_document_file(
        self,
        user_id: str,
        document_type: str,
        file_bytes: bytes,
        original_filename: str,
        content_type: str
    ) -> Dict[str, Any]:
        """
        Save uploaded file to cloud storage (Supabase Storage) or local filesystem fallback.
        
        Args:
            user_id: User UUID
            document_type: Type of document (flight_confirmation, hotel_booking, etc.)
            file_bytes: File content as bytes
            original_filename: Original filename
            content_type: MIME type
            
        Returns:
            Dictionary with file_path (storage path/URL), file_size, and metadata
        """
        # Map document type to directory name
        type_to_dir = {
            "flight_confirmation": "flight_confirmation",
            "hotel_booking": "hotel_booking",
            "visa_application": "visa_application",
            "itinerary": "itinerary"
        }
        
        dir_name = type_to_dir.get(document_type, "unknown")
        
        # Get file extension from original filename
        file_ext = Path(original_filename).suffix.lower() if original_filename else ".pdf"
        if not file_ext:
            file_ext = ".pdf"
        
        # Generate unique filename
        file_uuid = uuid.uuid4()
        filename = f"{file_uuid}{file_ext}"
        
        # Try cloud storage first, fallback to local
        if self.use_cloud_storage and self.supabase_client:
            try:
                # Storage path in Supabase: documents/{user_id}/{document_type}/{filename}
                storage_path = f"documents/{user_id}/{dir_name}/{filename}"
                
                # Upload to Supabase Storage bucket named "documents"
                # The bucket should be created in Supabase dashboard
                response = self.supabase_client.storage.from_("documents").upload(
                    path=storage_path,
                    file=file_bytes,
                    file_options={
                        "content-type": content_type,
                        "upsert": False  # Don't overwrite existing files
                    }
                )
                
                # Try to get public URL (works if bucket is public)
                # For private buckets, we'll use signed URLs when downloading
                file_url = None
                try:
                    public_url_response = self.supabase_client.storage.from_("documents").get_public_url(storage_path)
                    if hasattr(public_url_response, 'data') and public_url_response.data:
                        file_url = public_url_response.data.get("publicUrl")
                    elif isinstance(public_url_response, dict):
                        file_url = public_url_response.get("publicUrl") or public_url_response.get("url")
                except:
                    # Bucket might be private, that's okay - we'll use signed URLs
                    pass
                
                print(f"✓ File uploaded to Supabase Storage: {storage_path}")
                
                return {
                    "file_path": storage_path,  # Storage path in Supabase
                    "file_url": file_url,  # Public URL if bucket is public, None otherwise
                    "file_size": len(file_bytes),
                    "file_content_type": content_type,
                    "original_filename": original_filename,
                    "storage_type": "cloud"
                }
            except Exception as e:
                print(f"⚠️  Supabase Storage upload failed: {e}, falling back to local storage")
                # Fall through to local storage
        
        # Fallback to local filesystem storage
        base_dir = Path("apps/backend/uploads/documents")
        user_dir = base_dir / str(user_id) / dir_name
        user_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = user_dir / filename
        
        # Save file locally
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        
        # Return relative path from uploads directory
        relative_path = f"documents/{user_id}/{dir_name}/{filename}"
        
        print(f"✓ File saved to local storage: {relative_path}")
        
        return {
            "file_path": relative_path,
            "full_path": str(file_path),
            "file_size": len(file_bytes),
            "file_content_type": content_type,
            "original_filename": original_filename,
            "storage_type": "local"
        }
    
    def store_extracted_document(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        file_storage_info: Optional[Dict[str, Any]] = None,
        json_file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Store extracted document data in appropriate table.
        
        Args:
            db: Database session
            user_id: User UUID
            session_id: Chat session ID
            extracted_json: Extracted JSON data
            file_storage_info: File storage information from store_document_file()
            json_file_path: Path to saved JSON file
            
        Returns:
            Dictionary with stored record information
        """
        document_type = extracted_json.get("document_type")
        
        if document_type == "flight_confirmation":
            return self._store_flight(db, user_id, session_id, extracted_json, file_storage_info, json_file_path)
        elif document_type == "hotel_booking":
            return self._store_hotel(db, user_id, session_id, extracted_json, file_storage_info, json_file_path)
        elif document_type == "visa_application":
            return self._store_visa(db, user_id, session_id, extracted_json, file_storage_info, json_file_path)
        elif document_type == "itinerary":
            return self._store_itinerary(db, user_id, session_id, extracted_json, file_storage_info, json_file_path)
        else:
            raise ValueError(f"Unknown document type: {document_type}")
    
    def _store_flight(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        file_storage_info: Optional[Dict[str, Any]],
        json_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """Store flight confirmation data."""
        flight_data = extracted_json.get("flight_details", {}) or {}
        destination = extracted_json.get("destination", {}) or {}
        airline = extracted_json.get("airline", {}) or {}
        booking_ref = extracted_json.get("booking_reference", {}) or {}
        trip_value = extracted_json.get("trip_value", {}) or {}
        trip_duration = extracted_json.get("trip_duration", {}) or {}
        
        departure = flight_data.get("departure", {}) or {}
        return_flight = flight_data.get("return", {}) or {}
        flight_numbers = flight_data.get("flight_numbers", {}) or {}
        
        total_cost = trip_value.get("total_cost", {}) or {}
        
        flight = Flight(
            user_id=user_id,
            session_id=session_id,
            source_filename=extracted_json.get("source_filename"),
            json_file_path=json_file_path,
            
            # File storage info
            file_path=file_storage_info.get("file_path") if file_storage_info else None,
            file_size=file_storage_info.get("file_size") if file_storage_info else None,
            file_content_type=file_storage_info.get("file_content_type") if file_storage_info else None,
            original_filename=file_storage_info.get("original_filename") if file_storage_info else None,
            
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
        
        # Log successful storage
        print(f"\n{'='*70}")
        print(f"✅ FLIGHT DOCUMENT STORED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"📄 Document ID: {flight.id}")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Session ID: {session_id}")
        print(f"📁 File Path: {flight.file_path}")
        print(f"📝 Filename: {flight.original_filename or flight.source_filename}")
        print(f"📅 Stored At: {flight.created_at.isoformat()}")
        
        # Check if trip exists for this session
        trip = db.query(Trip).filter(Trip.session_id == session_id).first()
        if trip:
            print(f"🔗 Linked to Trip: {trip.id}")
            print(f"   Trip Status: {trip.status}")
            print(f"   Trip Destinations: {trip.destinations}")
        else:
            print(f"⚠️  No trip found for session_id: {session_id}")
        print(f"{'='*70}\n")
        
        return {"id": str(flight.id), "type": "flight", "stored_at": flight.created_at.isoformat()}
    
    def _store_hotel(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        file_storage_info: Optional[Dict[str, Any]],
        json_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """Store hotel booking data."""
        hotel_details = extracted_json.get("hotel_details", {}) or {}
        location = extracted_json.get("location", {}) or {}
        booking_dates = extracted_json.get("booking_dates", {}) or {}
        room_details = extracted_json.get("room_details", {}) or {}
        investment_value = extracted_json.get("investment_value", {}) or {}
        booking_ref = extracted_json.get("booking_reference", {}) or {}
        
        address = location.get("address", {}) or {}
        coordinates = location.get("coordinates", {}) or {}
        check_in = booking_dates.get("check_in", {}) or {}
        check_out = booking_dates.get("check_out", {}) or {}
        nights = booking_dates.get("nights", {}) or {}
        
        total_cost = investment_value.get("total_cost", {}) or {}
        per_night = investment_value.get("per_night", {}) or {}
        deposit_paid = investment_value.get("deposit_paid", {}) or {}
        
        hotel = Hotel(
            user_id=user_id,
            session_id=session_id,
            source_filename=extracted_json.get("source_filename"),
            json_file_path=json_file_path,
            
            # File storage info
            file_path=file_storage_info.get("file_path") if file_storage_info else None,
            file_size=file_storage_info.get("file_size") if file_storage_info else None,
            file_content_type=file_storage_info.get("file_content_type") if file_storage_info else None,
            original_filename=file_storage_info.get("original_filename") if file_storage_info else None,
            
            hotel_name=hotel_details.get("name"),
            hotel_chain=hotel_details.get("chain"),
            star_rating=hotel_details.get("star_rating"),
            
            address_street=address.get("street"),
            address_city=address.get("city"),
            address_country=address.get("country"),
            address_postal_code=address.get("postal_code"),
            address_full=address.get("full"),
            latitude=self._parse_numeric(coordinates.get("latitude")),
            longitude=self._parse_numeric(coordinates.get("longitude")),
            
            check_in_date=self._parse_date(check_in.get("date")),
            check_in_time=check_in.get("time"),
            check_out_date=self._parse_date(check_out.get("date")),
            check_out_time=check_out.get("time"),
            nights_count=nights.get("count"),
            
            room_type=room_details.get("room_type"),
            number_of_rooms=room_details.get("number_of_rooms"),
            occupancy=room_details.get("occupancy"),
            smoking_preference=room_details.get("smoking_preference"),
            
            total_cost_amount=self._parse_numeric(total_cost.get("amount")),
            total_cost_currency=total_cost.get("currency"),
            per_night_cost_amount=self._parse_numeric(per_night.get("amount")),
            per_night_cost_currency=per_night.get("currency"),
            deposit_paid_amount=self._parse_numeric(deposit_paid.get("amount")),
            deposit_paid_currency=deposit_paid.get("currency"),
            is_refundable=investment_value.get("refundable"),
            cancellation_policy=investment_value.get("cancellation_policy"),
            
            confirmation_number=booking_ref.get("confirmation_number"),
            booking_id=booking_ref.get("booking_id"),
            
            guests=extracted_json.get("guests"),
            extracted_data=extracted_json
        )
        
        db.add(hotel)
        db.commit()
        db.refresh(hotel)
        
        # Log successful storage
        print(f"\n{'='*70}")
        print(f"✅ HOTEL DOCUMENT STORED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"📄 Document ID: {hotel.id}")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Session ID: {session_id}")
        print(f"📁 File Path: {hotel.file_path}")
        print(f"📝 Filename: {hotel.original_filename or hotel.source_filename}")
        print(f"🏨 Hotel: {hotel.hotel_name}")
        print(f"📅 Check-in: {hotel.check_in_date}")
        print(f"📅 Stored At: {hotel.created_at.isoformat()}")
        
        # Check if trip exists for this session
        trip = db.query(Trip).filter(Trip.session_id == session_id).first()
        if trip:
            print(f"🔗 Linked to Trip: {trip.id}")
            print(f"   Trip Status: {trip.status}")
            print(f"   Trip Destinations: {trip.destinations}")
        else:
            print(f"⚠️  No trip found for session_id: {session_id}")
        print(f"{'='*70}\n")
        
        return {"id": str(hotel.id), "type": "hotel", "stored_at": hotel.created_at.isoformat()}
    
    def _store_visa(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        file_storage_info: Optional[Dict[str, Any]],
        json_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """Store visa application data."""
        visa_details = extracted_json.get("visa_details", {}) or {}
        applicant = extracted_json.get("applicant", {}) or {}
        trip_purpose = extracted_json.get("trip_purpose", {}) or {}
        planned_trip = extracted_json.get("planned_trip", {}) or {}
        accommodation_info = extracted_json.get("accommodation_info", {}) or {}
        financial_support = extracted_json.get("financial_support", {}) or {}
        travel_history = extracted_json.get("travel_history", {}) or {}
        
        validity_period = visa_details.get("validity_period", {}) or {}
        applicant_name = applicant.get("name", {}) or {}
        estimated_cost = financial_support.get("estimated_trip_cost", {}) or {}
        
        visa = Visa(
            user_id=user_id,
            session_id=session_id,
            source_filename=extracted_json.get("source_filename"),
            json_file_path=json_file_path,
            
            # File storage info
            file_path=file_storage_info.get("file_path") if file_storage_info else None,
            file_size=file_storage_info.get("file_size") if file_storage_info else None,
            file_content_type=file_storage_info.get("file_content_type") if file_storage_info else None,
            original_filename=file_storage_info.get("original_filename") if file_storage_info else None,
            
            visa_type=visa_details.get("visa_type"),
            destination_country=visa_details.get("destination_country"),
            entry_type=visa_details.get("entry_type"),
            validity_start_date=self._parse_date(validity_period.get("start")),
            validity_end_date=self._parse_date(validity_period.get("end")),
            
            applicant_first_name=applicant_name.get("first"),
            applicant_last_name=applicant_name.get("last"),
            applicant_full_name=applicant_name.get("full"),
            applicant_date_of_birth=self._parse_date(applicant.get("date_of_birth")),
            applicant_age=applicant.get("age"),
            applicant_passport_number=applicant.get("passport_number"),
            applicant_nationality=applicant.get("nationality"),
            
            trip_purpose_primary=trip_purpose.get("primary_purpose"),
            trip_purpose_detailed=trip_purpose.get("detailed_purpose"),
            is_business=trip_purpose.get("is_business"),
            is_medical_treatment=trip_purpose.get("is_medical_treatment"),
            
            intended_arrival_date=self._parse_date(planned_trip.get("intended_arrival_date")),
            intended_departure_date=self._parse_date(planned_trip.get("intended_departure_date")),
            duration_days=planned_trip.get("duration_days"),
            destination_cities=planned_trip.get("destination_cities"),
            
            has_hotel_booking=accommodation_info.get("has_hotel_booking"),
            hotel_name=accommodation_info.get("hotel_name"),
            hotel_address=accommodation_info.get("hotel_address"),
            
            has_sufficient_funds=financial_support.get("has_sufficient_funds"),
            estimated_trip_cost_amount=self._parse_numeric(estimated_cost.get("amount")),
            estimated_trip_cost_currency=estimated_cost.get("currency"),
            
            has_previous_travel=travel_history.get("has_previous_travel"),
            previous_destinations=travel_history.get("previous_destinations"),
            
            extracted_data=extracted_json
        )
        
        db.add(visa)
        db.commit()
        db.refresh(visa)
        
        # Log successful storage
        print(f"\n{'='*70}")
        print(f"✅ VISA DOCUMENT STORED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"📄 Document ID: {visa.id}")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Session ID: {session_id}")
        print(f"📁 File Path: {visa.file_path}")
        print(f"📝 Filename: {visa.original_filename or visa.source_filename}")
        print(f"🛂 Visa Type: {visa.visa_type}")
        print(f"🌍 Destination: {visa.destination_country}")
        print(f"👤 Applicant: {visa.applicant_full_name}")
        print(f"📅 Stored At: {visa.created_at.isoformat()}")
        
        # Check if trip exists for this session
        trip = db.query(Trip).filter(Trip.session_id == session_id).first()
        if trip:
            print(f"🔗 Linked to Trip: {trip.id}")
            print(f"   Trip Status: {trip.status}")
            print(f"   Trip Destinations: {trip.destinations}")
        else:
            print(f"⚠️  No trip found for session_id: {session_id}")
        print(f"{'='*70}\n")
        
        return {"id": str(visa.id), "type": "visa", "stored_at": visa.created_at.isoformat()}
    
    def _store_itinerary(
        self,
        db: Session,
        user_id: str,
        session_id: str,
        extracted_json: Dict[str, Any],
        file_storage_info: Optional[Dict[str, Any]],
        json_file_path: Optional[str]
    ) -> Dict[str, Any]:
        """Store itinerary data."""
        trip_overview = extracted_json.get("trip_overview", {}) or {}
        adventure_sports = extracted_json.get("adventure_sports_detected", {}) or {}
        risk_factors = extracted_json.get("risk_factors", {}) or {}
        trip_characteristics = extracted_json.get("trip_characteristics", {}) or {}
        trip_structure = extracted_json.get("trip_structure", {}) or {}
        
        itinerary = Itinerary(
            user_id=user_id,
            session_id=session_id,
            source_filename=extracted_json.get("source_filename"),
            json_file_path=json_file_path,
            
            # File storage info
            file_path=file_storage_info.get("file_path") if file_storage_info else None,
            file_size=file_storage_info.get("file_size") if file_storage_info else None,
            file_content_type=file_storage_info.get("file_content_type") if file_storage_info else None,
            original_filename=file_storage_info.get("original_filename") if file_storage_info else None,
            
            trip_title=trip_overview.get("title"),
            duration_days=trip_overview.get("duration_days"),
            start_date=self._parse_date(trip_overview.get("start_date")),
            end_date=self._parse_date(trip_overview.get("end_date")),
            
            destinations=extracted_json.get("destinations"),
            activities=extracted_json.get("activities"),
            
            has_adventure_sports=adventure_sports.get("has_adventure_sports"),
            adventure_sports_activities=adventure_sports.get("activities"),
            
            has_extreme_sports=risk_factors.get("extreme_sports"),
            has_water_sports=risk_factors.get("water_sports"),
            has_winter_sports=risk_factors.get("winter_sports"),
            has_high_altitude_activities=risk_factors.get("high_altitude_activities"),
            has_motorized_sports=risk_factors.get("motorized_sports"),
            is_group_travel=risk_factors.get("group_travel"),
            has_remote_locations=risk_factors.get("remote_locations"),
            has_political_risk_destinations=risk_factors.get("political_risk_destinations"),
            
            is_group_tour=trip_characteristics.get("is_group_tour"),
            is_solo_travel=trip_characteristics.get("is_solo_travel"),
            group_size=trip_characteristics.get("group_size"),
            includes_children=trip_characteristics.get("includes_children"),
            includes_seniors=trip_characteristics.get("includes_seniors"),
            
            trip_type=trip_structure.get("trip_type"),
            number_of_destinations=trip_structure.get("number_of_destinations"),
            requires_internal_travel=trip_structure.get("requires_internal_travel"),
            internal_transport=trip_structure.get("internal_transport"),
            
            travelers=extracted_json.get("travelers"),
            extracted_data=extracted_json
        )
        
        db.add(itinerary)
        db.commit()
        db.refresh(itinerary)
        
        # Log successful storage
        print(f"\n{'='*70}")
        print(f"✅ ITINERARY DOCUMENT STORED SUCCESSFULLY")
        print(f"{'='*70}")
        print(f"📄 Document ID: {itinerary.id}")
        print(f"👤 User ID: {user_id}")
        print(f"💬 Session ID: {session_id}")
        print(f"📁 File Path: {itinerary.file_path}")
        print(f"📝 Filename: {itinerary.original_filename or itinerary.source_filename}")
        print(f"🗺️  Trip Title: {itinerary.trip_title}")
        print(f"📅 Start Date: {itinerary.start_date}")
        print(f"📅 End Date: {itinerary.end_date}")
        print(f"⏱️  Duration: {itinerary.duration_days} days")
        print(f"🏄 Adventure Sports: {itinerary.has_adventure_sports}")
        print(f"📅 Stored At: {itinerary.created_at.isoformat()}")
        
        # Check if trip exists for this session
        trip = db.query(Trip).filter(Trip.session_id == session_id).first()
        if trip:
            print(f"🔗 Linked to Trip: {trip.id}")
            print(f"   Trip Status: {trip.status}")
            print(f"   Trip Destinations: {trip.destinations}")
        else:
            print(f"⚠️  No trip found for session_id: {session_id}")
        print(f"{'='*70}\n")
        
        return {"id": str(itinerary.id), "type": "itinerary", "stored_at": itinerary.created_at.isoformat()}
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
    
    def _parse_numeric(self, value: Any) -> Optional[float]:
        """Parse numeric value."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def get_file_download_url(self, file_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Get download URL for a file stored in Supabase Storage.
        
        Args:
            file_path: Storage path in Supabase (e.g., "documents/{user_id}/flight_confirmation/{uuid}.pdf")
            expires_in: URL expiration time in seconds (default 1 hour)
            
        Returns:
            Signed URL for file download, or None if local storage
        """
        if self.use_cloud_storage and self.supabase_client:
            try:
                # Get signed URL for private bucket, or public URL for public bucket
                response = self.supabase_client.storage.from_("documents").create_signed_url(
                    path=file_path,
                    expires_in=expires_in
                )
                # The response structure may vary, handle both cases
                if hasattr(response, 'signedURL'):
                    return response.signedURL
                elif isinstance(response, dict) and 'signedURL' in response:
                    return response['signedURL']
                elif isinstance(response, dict) and 'url' in response:
                    return response['url']
                else:
                    # Try public URL as fallback
                    public_url = self.supabase_client.storage.from_("documents").get_public_url(file_path)
                    if hasattr(public_url, 'data') and public_url.data:
                        return public_url.data.get("publicUrl")
                    return None
            except Exception as e:
                print(f"⚠️  Failed to get Supabase Storage URL: {e}")
                return None
        
        # Local storage - return None, will be handled by file system download
        return None
    
    def download_file(self, file_path: str) -> Optional[bytes]:
        """
        Download file from Supabase Storage or local filesystem.
        
        Args:
            file_path: Storage path or local file path
            
        Returns:
            File content as bytes, or None if not found
        """
        if self.use_cloud_storage and self.supabase_client:
            try:
                # Download from Supabase Storage
                response = self.supabase_client.storage.from_("documents").download(file_path)
                if response:
                    return response
            except Exception as e:
                print(f"⚠️  Failed to download from Supabase Storage: {e}")
                return None
        
        # Fallback to local filesystem
        full_path = Path("apps/backend/uploads") / file_path
        if full_path.exists():
            with open(full_path, "rb") as f:
                return f.read()
        
        return None

