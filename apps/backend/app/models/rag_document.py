"""RAG document model for policy sections and embeddings."""

from sqlalchemy import Column, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.db import Base


class RagDocument(Base):
    """RAG document model for policy sections with embeddings."""
    
    __tablename__ = "rag_documents"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Document metadata
    title = Column(String, nullable=False)
    insurer_name = Column(String, nullable=False)
    product_code = Column(String, nullable=False)
    section_id = Column(String, nullable=False)  # e.g., "1.2.3"
    heading = Column(String, nullable=False)
    
    # Content
    text = Column(Text, nullable=False)
    citations = Column(JSONB, nullable=True)  # Reference citations
    
    # Vector embedding (pgvector)
    embedding = Column("embedding", type_="vector(1536)")  # OpenAI embedding dimension
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<RagDocument(id={self.id}, title={self.title}, section_id={self.section_id})>"
