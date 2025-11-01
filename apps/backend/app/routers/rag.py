"""RAG router for policy document search."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import get_current_user_supabase as get_current_user
from app.models.user import User
from app.schemas.rag import RagSearchRequest, RagSearchResponse, RagIngestRequest
from app.services.rag import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/search", response_model=RagSearchResponse)
async def search_documents(
    q: str,
    limit: int = 5,
    product_type: str = None,
    insurer_name: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search policy documents."""
    
    rag_service = RAGService(db=db)
    
    search_request = RagSearchRequest(
        query=q,
        limit=limit,
        product_type=product_type,
        insurer_name=insurer_name
    )
    
    search_response = rag_service.search_documents(db, search_request)
    
    return search_response


@router.post("/ingest")
async def ingest_document(
    ingest_data: RagIngestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ingest a policy document."""
    
    rag_service = RAGService(db=db)
    
    documents = rag_service.ingest_document(
        db,
        ingest_data.title,
        ingest_data.insurer_name,
        ingest_data.product_code,
        ingest_data.content,
        ingest_data.split_by_sections
    )
    
    return {
        "message": "Document ingested successfully",
        "document_count": len(documents),
        "documents": [
            {
                "id": str(doc.id),
                "title": doc.title,
                "section_id": doc.section_id,
                "heading": doc.heading
            }
            for doc in documents
        ]
    }
