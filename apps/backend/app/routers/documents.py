"""Documents API endpoints for accessing uploaded documents."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path
from datetime import datetime
import uuid

from app.core.db import get_db
from app.core.security import get_current_user_supabase
from app.models.user import User
from app.models.flight import Flight
from app.models.hotel import Hotel
from app.models.visa import Visa
from app.models.itinerary import Itinerary


router = APIRouter(prefix="/documents", tags=["documents"])


def get_document_model(document_type: str):
    """Get the appropriate model class for document type."""
    type_map = {
        "flight": Flight,
        "hotel": Hotel,
        "visa": Visa,
        "itinerary": Itinerary
    }
    return type_map.get(document_type.lower())


def get_document_type_from_model(model_instance):
    """Get document type string from model instance."""
    if isinstance(model_instance, Flight):
        return "flight"
    elif isinstance(model_instance, Hotel):
        return "hotel"
    elif isinstance(model_instance, Visa):
        return "visa"
    elif isinstance(model_instance, Itinerary):
        return "itinerary"
    return None


@router.get("")
async def list_documents(
    type: Optional[str] = Query(None, description="Filter by document type: flight, hotel, visa, itinerary"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    List all user's documents with optional filtering by type.
    
    Returns a list of documents with summary information.
    """
    documents = []
    
    if type:
        # Filter by specific type
        model_class = get_document_model(type)
        if not model_class:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid document type. Allowed: flight, hotel, visa, itinerary"
            )
        
        db_documents = db.query(model_class).filter(
            model_class.user_id == current_user.id
        ).order_by(
            model_class.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        for doc in db_documents:
            doc_type = get_document_type_from_model(doc)
            documents.append({
                "id": str(doc.id),
                "type": doc_type,
                "filename": doc.original_filename or doc.source_filename,
                "extracted_at": doc.extracted_at.isoformat() if doc.extracted_at else None,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "summary": _get_document_summary(doc, doc_type)
            })
    else:
        # Get all types
        all_docs = []
        
        # Flights
        flights = db.query(Flight).filter(
            Flight.user_id == current_user.id
        ).order_by(Flight.created_at.desc()).all()
        for doc in flights:
            all_docs.append((doc.created_at, doc, "flight"))
        
        # Hotels
        hotels = db.query(Hotel).filter(
            Hotel.user_id == current_user.id
        ).order_by(Hotel.created_at.desc()).all()
        for doc in hotels:
            all_docs.append((doc.created_at, doc, "hotel"))
        
        # Visas
        visas = db.query(Visa).filter(
            Visa.user_id == current_user.id
        ).order_by(Visa.created_at.desc()).all()
        for doc in visas:
            all_docs.append((doc.created_at, doc, "visa"))
        
        # Itineraries
        itineraries = db.query(Itinerary).filter(
            Itinerary.user_id == current_user.id
        ).order_by(Itinerary.created_at.desc()).all()
        for doc in itineraries:
            all_docs.append((doc.created_at, doc, "itinerary"))
        
        # Sort by created_at descending
        all_docs.sort(key=lambda x: x[0] if x[0] else datetime.min, reverse=True)
        
        # Apply pagination
        paginated_docs = all_docs[offset:offset + limit]
        
        for _, doc, doc_type in paginated_docs:
            documents.append({
                "id": str(doc.id),
                "type": doc_type,
                "filename": doc.original_filename or doc.source_filename,
                "extracted_at": doc.extracted_at.isoformat() if doc.extracted_at else None,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "summary": _get_document_summary(doc, doc_type)
            })
    
    return {
        "documents": documents,
        "total": len(documents),
        "limit": limit,
        "offset": offset
    }


@router.get("/{document_id}")
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    Get specific document details by ID.
    
    Returns full extracted data and metadata.
    """
    # Try to find document in any table
    document = None
    doc_type = None
    
    # Try Flight
    doc = db.query(Flight).filter(
        Flight.id == document_id,
        Flight.user_id == current_user.id
    ).first()
    if doc:
        document = doc
        doc_type = "flight"
    
    # Try Hotel
    if not document:
        doc = db.query(Hotel).filter(
            Hotel.id == document_id,
            Hotel.user_id == current_user.id
        ).first()
        if doc:
            document = doc
            doc_type = "hotel"
    
    # Try Visa
    if not document:
        doc = db.query(Visa).filter(
            Visa.id == document_id,
            Visa.user_id == current_user.id
        ).first()
        if doc:
            document = doc
            doc_type = "visa"
    
    # Try Itinerary
    if not document:
        doc = db.query(Itinerary).filter(
            Itinerary.id == document_id,
            Itinerary.user_id == current_user.id
        ).first()
        if doc:
            document = doc
            doc_type = "itinerary"
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Build response with all document fields
    response = {
        "id": str(document.id),
        "type": doc_type,
        "filename": document.original_filename or document.source_filename,
        "source_filename": document.source_filename,
        "extracted_at": document.extracted_at.isoformat() if document.extracted_at else None,
        "created_at": document.created_at.isoformat() if document.created_at else None,
        "session_id": document.session_id,
        "file_path": document.file_path,
        "file_size": document.file_size,
        "file_content_type": document.file_content_type,
        "json_file_path": document.json_file_path,
        "extracted_data": document.extracted_data
    }
    
    # Add type-specific fields
    if doc_type == "flight":
        response.update({
            "trip_type": document.trip_type,
            "airline_name": document.airline_name,
            "airline_code": document.airline_code,
            "outbound_airline_name": document.outbound_airline_name,
            "outbound_airline_code": document.outbound_airline_code,
            "inbound_airline_name": document.inbound_airline_name,
            "inbound_airline_code": document.inbound_airline_code,
            "departure_date": document.departure_date.isoformat() if document.departure_date else None,
            "departure_time": document.departure_time,
            "return_date": document.return_date.isoformat() if document.return_date else None,
            "destination_country": document.destination_country,
            "destination_city": document.destination_city,
            "pnr": document.pnr,
            "travelers": document.travelers
        })
    elif doc_type == "hotel":
        response.update({
            "hotel_name": document.hotel_name,
            "check_in_date": document.check_in_date.isoformat() if document.check_in_date else None,
            "check_out_date": document.check_out_date.isoformat() if document.check_out_date else None,
            "address_full": document.address_full,
            "guests": document.guests
        })
    elif doc_type == "visa":
        response.update({
            "visa_type": document.visa_type,
            "destination_country": document.destination_country,
            "applicant_full_name": document.applicant_full_name,
            "intended_arrival_date": document.intended_arrival_date.isoformat() if document.intended_arrival_date else None,
            "intended_departure_date": document.intended_departure_date.isoformat() if document.intended_departure_date else None
        })
    elif doc_type == "itinerary":
        response.update({
            "trip_title": document.trip_title,
            "start_date": document.start_date.isoformat() if document.start_date else None,
            "end_date": document.end_date.isoformat() if document.end_date else None,
            "has_adventure_sports": document.has_adventure_sports,
            "destinations": document.destinations,
            "travelers": document.travelers
        })
    
    return response


@router.get("/{document_id}/file")
async def download_document_file(
    document_id: str,
    current_user: User = Depends(get_current_user_supabase),
    db: Session = Depends(get_db)
):
    """
    Download the original uploaded file.
    
    Returns the file with proper content-type headers.
    """
    # Try to find document in any table
    document = None
    
    # Try Flight
    doc = db.query(Flight).filter(
        Flight.id == document_id,
        Flight.user_id == current_user.id
    ).first()
    if doc:
        document = doc
    
    # Try Hotel
    if not document:
        doc = db.query(Hotel).filter(
            Hotel.id == document_id,
            Hotel.user_id == current_user.id
        ).first()
        if doc:
            document = doc
    
    # Try Visa
    if not document:
        doc = db.query(Visa).filter(
            Visa.id == document_id,
            Visa.user_id == current_user.id
        ).first()
        if doc:
            document = doc
    
    # Try Itinerary
    if not document:
        doc = db.query(Itinerary).filter(
            Itinerary.id == document_id,
            Itinerary.user_id == current_user.id
        ).first()
        if doc:
            document = doc
    
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    if not document.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found for this document"
        )
    
    # Use DocumentStorageService to download file (supports both cloud and local)
    from app.services.document_storage import DocumentStorageService
    storage_service = DocumentStorageService()
    
    # Try to download file content
    file_content = storage_service.download_file(document.file_path)
    
    if file_content is None:
        # Fallback: check if it's a local file path
        file_path = Path("apps/backend/uploads") / document.file_path
        if file_path.exists():
            # Serve local file
            content_type = document.file_content_type or "application/pdf"
            filename = document.original_filename or document.source_filename or "document.pdf"
            return FileResponse(
                path=str(file_path),
                media_type=content_type,
                filename=filename
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on server"
            )
    
    # File content retrieved (from cloud storage)
    # Return as streaming response
    from fastapi.responses import Response
    content_type = document.file_content_type or "application/pdf"
    filename = document.original_filename or document.source_filename or "document.pdf"
    
    return Response(
        content=file_content,
        media_type=content_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


def _get_document_summary(document, doc_type: str) -> dict:
    """Get summary information for a document."""
    summary = {}
    
    if doc_type == "flight":
        summary = {
            "trip_type": document.trip_type,
            "airline": document.airline_name,  # Backward compatibility
            "outbound_airline": document.outbound_airline_name,
            "inbound_airline": document.inbound_airline_name,
            "departure_date": document.departure_date.isoformat() if document.departure_date else None,
            "destination": f"{document.destination_city}, {document.destination_country}" if document.destination_city and document.destination_country else document.destination_country
        }
    elif doc_type == "hotel":
        summary = {
            "hotel_name": document.hotel_name,
            "check_in_date": document.check_in_date.isoformat() if document.check_in_date else None,
            "location": document.address_city or document.address_country
        }
    elif doc_type == "visa":
        summary = {
            "visa_type": document.visa_type,
            "destination_country": document.destination_country,
            "applicant": document.applicant_full_name
        }
    elif doc_type == "itinerary":
        summary = {
            "trip_title": document.trip_title,
            "start_date": document.start_date.isoformat() if document.start_date else None,
            "duration_days": document.duration_days,
            "has_adventure_sports": document.has_adventure_sports
        }
    
    return summary

