"""RAG service for policy document search and retrieval."""

from typing import List, Dict, Any, Optional
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.rag_document import RagDocument
from app.schemas.rag import RagSearchRequest, RagSearchResponse, RagDocumentResponse


class RagService:
    """Service for RAG-based policy document search."""
    
    def __init__(self):
        # TODO: Initialize real embedding model (OpenAI, etc.)
        self.embedding_model = None
        self.embedding_dimension = settings.vector_dimension
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for text."""
        # TODO: Replace with real embedding generation
        # For now, return a mock embedding
        return [0.1] * self.embedding_dimension
    
    def search_documents(
        self,
        db: Session,
        request: RagSearchRequest
    ) -> RagSearchResponse:
        """Search for relevant policy documents."""
        
        # Generate embedding for query
        query_embedding = self.embed_text(request.query)
        
        # Build SQL query for vector similarity search
        # TODO: Implement proper vector similarity search with pgvector
        # For now, use text search as fallback
        
        query_sql = text("""
            SELECT 
                id, title, insurer_name, product_code, section_id, 
                heading, text, citations
            FROM rag_documents 
            WHERE 
                (LOWER(text) LIKE LOWER(:query) OR 
                 LOWER(heading) LIKE LOWER(:query) OR
                 LOWER(title) LIKE LOWER(:query))
        """)
        
        if request.product_type:
            query_sql = text("""
                SELECT 
                    id, title, insurer_name, product_code, section_id, 
                    heading, text, citations
                FROM rag_documents 
                WHERE 
                    product_code = :product_type AND
                    (LOWER(text) LIKE LOWER(:query) OR 
                     LOWER(heading) LIKE LOWER(:query) OR
                     LOWER(title) LIKE LOWER(:query))
            """)
        
        if request.insurer_name:
            query_sql = text("""
                SELECT 
                    id, title, insurer_name, product_code, section_id, 
                    heading, text, citations
                FROM rag_documents 
                WHERE 
                    insurer_name = :insurer_name AND
                    (LOWER(text) LIKE LOWER(:query) OR 
                     LOWER(heading) LIKE LOWER(:query) OR
                     LOWER(title) LIKE LOWER(:query))
            """)
        
        # Execute query
        results = db.execute(
            query_sql,
            {
                "query": f"%{request.query}%",
                "product_type": request.product_type,
                "insurer_name": request.insurer_name,
            }
        ).fetchall()
        
        # Convert to response format
        documents = []
        for result in results[:request.limit]:
            doc_response = RagDocumentResponse(
                id=result.id,
                title=result.title,
                insurer_name=result.insurer_name,
                product_code=result.product_code,
                section_id=result.section_id,
                heading=result.heading,
                text=result.text,
                citations=result.citations,
                similarity_score=0.95  # Mock similarity score
            )
            documents.append(doc_response)
        
        return RagSearchResponse(
            query=request.query,
            documents=documents,
            total_results=len(results)
        )
    
    def ingest_document(
        self,
        db: Session,
        title: str,
        insurer_name: str,
        product_code: str,
        content: str,
        split_by_sections: bool = True
    ) -> List[RagDocument]:
        """Ingest a policy document and create searchable chunks."""
        
        documents = []
        
        if split_by_sections:
            # Split content by sections (mock implementation)
            sections = self._split_content_by_sections(content)
            
            for i, section in enumerate(sections):
                # Generate embedding
                embedding = self.embed_text(section["text"])
                
                # Create document
                doc = RagDocument(
                    title=title,
                    insurer_name=insurer_name,
                    product_code=product_code,
                    section_id=f"{i+1}",
                    heading=section["heading"],
                    text=section["text"],
                    citations=section.get("citations"),
                    embedding=embedding
                )
                
                db.add(doc)
                documents.append(doc)
        else:
            # Store as single document
            embedding = self.embed_text(content)
            
            doc = RagDocument(
                title=title,
                insurer_name=insurer_name,
                product_code=product_code,
                section_id="1",
                heading=title,
                text=content,
                citations=None,
                embedding=embedding
            )
            
            db.add(doc)
            documents.append(doc)
        
        db.commit()
        return documents
    
    def _split_content_by_sections(self, content: str) -> List[Dict[str, Any]]:
        """Split content into sections based on headings."""
        # TODO: Implement proper content splitting
        # For now, return mock sections
        
        sections = [
            {
                "heading": "Coverage Overview",
                "text": "This policy provides comprehensive travel insurance coverage...",
                "citations": {"section": "1.1", "page": 1}
            },
            {
                "heading": "Medical Coverage",
                "text": "Medical expenses are covered up to $100,000...",
                "citations": {"section": "2.1", "page": 5}
            },
            {
                "heading": "Trip Cancellation",
                "text": "Trip cancellation coverage applies when...",
                "citations": {"section": "3.1", "page": 10}
            }
        ]
        
        return sections
    
    def get_policy_explanation(
        self,
        db: Session,
        question: str,
        product_type: Optional[str] = None
    ) -> str:
        """Get policy explanation for a specific question."""
        
        # Search for relevant documents
        search_request = RagSearchRequest(
            query=question,
            limit=3,
            product_type=product_type
        )
        
        search_response = self.search_documents(db, search_request)
        
        if not search_response.documents:
            return "I couldn't find specific information about that in our policy documents. Please contact our customer service team for assistance."
        
        # Build explanation from search results
        explanation_parts = []
        for doc in search_response.documents:
            citation = f"Source: §{doc.section_id}"
            explanation_parts.append(f"{doc.text}\n{citation}")
        
        return "\n\n".join(explanation_parts)
