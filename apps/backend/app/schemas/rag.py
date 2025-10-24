"""RAG schemas."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from uuid import UUID


class RagSearchRequest(BaseModel):
    """Schema for RAG search request."""
    query: str
    limit: int = 5
    product_type: Optional[str] = None
    insurer_name: Optional[str] = None


class RagDocumentResponse(BaseModel):
    """Schema for RAG document response."""
    id: UUID
    title: str
    insurer_name: str
    product_code: str
    section_id: str
    heading: str
    text: str
    citations: Optional[Dict[str, Any]] = None
    similarity_score: Optional[float] = None
    
    class Config:
        from_attributes = True


class RagSearchResponse(BaseModel):
    """Schema for RAG search response."""
    query: str
    documents: List[RagDocumentResponse]
    total_results: int


class RagIngestRequest(BaseModel):
    """Schema for RAG document ingestion."""
    title: str
    insurer_name: str
    product_code: str
    content: str  # Full document content
    split_by_sections: bool = True
