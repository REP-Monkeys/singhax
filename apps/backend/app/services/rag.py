"""RAG service for policy document search and retrieval with real OpenAI embeddings and pgvector."""

from typing import List, Dict, Any, Optional
import logging
import uuid
import re
from pathlib import Path

import openai
import pdfplumber
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.rag_document import RagDocument
from app.schemas.rag import RagSearchRequest, RagSearchResponse, RagDocumentResponse

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based policy document search with real embeddings and PDF processing."""
    
    def __init__(self, db: Session = None):
        """Initialize RAG service.
        
        Args:
            db: Database session (optional, can be set later)
        """
        self.db = db
        self.embedding_dimension = settings.vector_dimension
        logger.info("RAGService initialized")
    
    def _generate_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI text-embedding-3-small.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding (1536 dimensions)
            
        Raises:
            ValueError: If embedding dimension is incorrect
            Exception: If OpenAI API call fails
        """
        try:
            client = openai.OpenAI(api_key=settings.openai_api_key)
            
            # Truncate to ~8000 tokens (32000 chars estimate)
            max_chars = 32000
            truncated_text = text[:max_chars]
            
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=truncated_text,
                encoding_format="float"
            )
            
            embedding = response.data[0].embedding
            
            if len(embedding) != 1536:
                raise ValueError(f"Expected 1536 dimensions, got {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise
    
    def _extract_sections_from_pdf(self, pdf_path: str) -> List[Dict]:
        """Extract policy sections from PDF using regex pattern matching.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            List of sections with section_id, heading, text, and pages
        """
        sections = []
        
        with pdfplumber.open(pdf_path) as pdf:
            full_text = ""
            page_boundaries = []
            
            # Extract all text and track page boundaries
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    page_boundaries.append(len(full_text))
                    full_text += text + "\n"
            
            # Pattern: SECTION 1, Section 6, SECTION 41 –, etc.
            section_pattern = r'(?:SECTION|Section)\s+(\d+)(?:\s*[:\-–—]\s*|\s+)([^\n]+?)(?=\n|$)'
            matches = list(re.finditer(section_pattern, full_text, re.IGNORECASE | re.MULTILINE))
            
            logger.info(f"Found {len(matches)} section headers in PDF")
            
            for i, match in enumerate(matches):
                section_num = match.group(1)
                section_title = match.group(2).strip()
                
                # Get text from this section to the next
                start_pos = match.end()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
                section_text = full_text[start_pos:end_pos].strip()
                
                # Skip very short sections (likely headers or errors)
                if len(section_text) < 50:
                    continue
                
                # Determine which pages this section spans
                section_pages = []
                for page_idx, boundary in enumerate(page_boundaries):
                    next_boundary = page_boundaries[page_idx + 1] if page_idx + 1 < len(page_boundaries) else len(full_text)
                    if boundary <= start_pos < next_boundary or boundary <= end_pos < next_boundary:
                        if page_idx + 1 not in section_pages:
                            section_pages.append(page_idx + 1)
                
                sections.append({
                    'section_id': f'Section {section_num}',
                    'heading': section_title,
                    'text': section_text,
                    'pages': section_pages if section_pages else [1]
                })
        
        return sections
    
    def _chunk_text(self, text: str, max_words: int = 500) -> List[str]:
        """Split text into chunks preserving sentence boundaries.
        
        Args:
            text: Text to chunk
            max_words: Maximum words per chunk
            
        Returns:
            List of text chunks
        """
        # Split into sentences (handles common abbreviations)
        sentence_pattern = r'(?<=[.!?])\s+(?=[A-Z])|(?<=[.!?])$'
        sentences = re.split(sentence_pattern, text)
        
        chunks = []
        current_chunk = []
        current_words = 0
        
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            words = len(sentence.split())
            
            # If adding this sentence exceeds limit, start new chunk
            if current_words + words > max_words and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [sentence]
                current_words = words
            else:
                current_chunk.append(sentence)
                current_words += words
        
        # Add remaining chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else ['']
    
    def ingest_pdf(
        self,
        pdf_path: str,
        title: str,
        insurer_name: str,
        product_code: str,
        tier: Optional[str] = None
    ) -> Dict[str, int]:
        """Ingest PDF policy document into RAG database.
        
        Args:
            pdf_path: Path to PDF file
            title: Document title
            insurer_name: Insurance company name
            product_code: Product code
            tier: Policy tier if applicable
            
        Returns:
            Dictionary with ingestion statistics
            
        Raises:
            FileNotFoundError: If PDF not found
        """
        logger.info(f"Starting ingestion of {pdf_path}")
        
        if not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        
        # Extract sections from PDF
        sections = self._extract_sections_from_pdf(pdf_path)
        logger.info(f"Extracted {len(sections)} sections")
        
        stored_count = 0
        chunk_count = 0
        
        for section in sections:
            # Chunk long sections
            chunks = self._chunk_text(section['text'], max_words=500)
            chunk_count += len(chunks)
            
            for chunk_idx, chunk_text in enumerate(chunks):
                try:
                    embedding = self._generate_embedding(chunk_text)
                except Exception as e:
                    logger.error(f"Failed embedding for {section['section_id']}: {e}")
                    continue
                
                # Create document record
                doc = RagDocument(
                    id=uuid.uuid4(),  # UUID object, not string
                    title=title,
                    insurer_name=insurer_name,
                    product_code=product_code,
                    section_id=section['section_id'],
                    heading=section['heading'],
                    text=chunk_text,
                    citations={
                        'pages': section['pages'],
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks),
                        'tier': tier
                    },
                    embedding=embedding
                )
                
                self.db.add(doc)
                stored_count += 1
                
                # Commit in batches of 10 to avoid memory issues
                if stored_count % 10 == 0:
                    self.db.commit()
                    logger.info(f"Committed batch ({stored_count} total)")
        
        # Final commit
        self.db.commit()
        
        result = {
            "sections_found": len(sections),
            "chunks_created": chunk_count,
            "documents_stored": stored_count
        }
        
        logger.info(f"Ingestion complete: {result}")
        return result
    
    def ingest_document(
        self,
        db: Session,
        title: str,
        insurer_name: str,
        product_code: str,
        content: str,
        split_by_sections: bool = True
    ) -> List[RagDocument]:
        """Ingest a text document into RAG database.
        
        Args:
            db: Database session
            title: Document title
            insurer_name: Insurance company name
            product_code: Product code
            content: Full document text content
            split_by_sections: Whether to split content by sections
            
        Returns:
            List of created RagDocument objects
        """
        self.db = db  # Update db session
        
        logger.info(f"Starting ingestion of document: {title}")
        
        documents = []
        
        if split_by_sections:
            # Extract sections using same pattern as PDF extraction
            section_pattern = r'(?:SECTION|Section)\s+(\d+)(?:\s*[:\-–—]\s*|\s+)([^\n]+?)(?=\n|$)'
            matches = list(re.finditer(section_pattern, content, re.IGNORECASE | re.MULTILINE))
            
            logger.info(f"Found {len(matches)} section headers in document")
            
            for i, match in enumerate(matches):
                section_num = match.group(1)
                section_title = match.group(2).strip()
                
                # Get text from this section to the next
                start_pos = match.end()
                end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(content)
                section_text = content[start_pos:end_pos].strip()
                
                # Skip very short sections
                if len(section_text) < 50:
                    continue
                
                # Chunk the section
                chunks = self._chunk_text(section_text, max_words=500)
                
                for chunk_idx, chunk_text in enumerate(chunks):
                    try:
                        embedding = self._generate_embedding(chunk_text)
                    except Exception as e:
                        logger.error(f"Failed embedding for section {section_num}: {e}")
                        continue
                    
                    # Create document record
                    doc = RagDocument(
                        id=uuid.uuid4(),
                        title=title,
                        insurer_name=insurer_name,
                        product_code=product_code,
                        section_id=f'Section {section_num}',
                        heading=section_title,
                        text=chunk_text,
                        citations={
                            'chunk_index': chunk_idx,
                            'total_chunks': len(chunks)
                        },
                        embedding=embedding
                    )
                    
                    self.db.add(doc)
                    documents.append(doc)
        else:
            # No section splitting, just chunk the entire content
            chunks = self._chunk_text(content, max_words=500)
            
            for chunk_idx, chunk_text in enumerate(chunks):
                try:
                    embedding = self._generate_embedding(chunk_text)
                except Exception as e:
                    logger.error(f"Failed embedding for chunk {chunk_idx}: {e}")
                    continue
                
                # Create document record
                doc = RagDocument(
                    id=uuid.uuid4(),
                    title=title,
                    insurer_name=insurer_name,
                    product_code=product_code,
                    section_id='1',
                    heading=title,
                    text=chunk_text,
                    citations={
                        'chunk_index': chunk_idx,
                        'total_chunks': len(chunks)
                    },
                    embedding=embedding
                )
                
                self.db.add(doc)
                documents.append(doc)
        
        # Commit all documents
        self.db.commit()
        
        logger.info(f"Ingestion complete: {len(documents)} documents created")
        return documents
    
    def search(
        self,
        query: str,
        limit: int = 5,
        tier: Optional[str] = None,
        min_similarity: float = 0.5
    ) -> List[Dict]:
        """Search documents using pgvector cosine similarity.
        
        Args:
            query: Search query
            limit: Maximum results to return
            tier: Filter by policy tier
            min_similarity: Minimum cosine similarity threshold (0-1, default 0.5)
            
        Returns:
            List of matching documents with metadata and similarity scores
        """
        try:
            query_embedding = self._generate_embedding(query)
        except Exception as e:
            logger.error(f"Failed to generate query embedding: {e}")
            return []
        
        # Calculate cosine distance using pgvector
        distance_expr = RagDocument.embedding.cosine_distance(query_embedding)
        
        # Build query with similarity calculation
        query_obj = self.db.query(
            RagDocument,
            (1 - distance_expr).label('similarity')  # Convert distance to similarity
        )
        
        # Filter by tier if provided
        if tier:
            query_obj = query_obj.filter(
                RagDocument.citations['tier'].astext == tier
            )
        
        # Order by similarity (highest first) and limit
        results = query_obj.order_by(distance_expr).limit(limit * 2).all()
        
        # Filter by minimum similarity and format results
        formatted_results = []
        for doc, similarity in results:
            if similarity >= min_similarity:
                formatted_results.append({
                    'id': doc.id,
                    'title': doc.title,
                    'section_id': doc.section_id,
                    'heading': doc.heading,
                    'text': doc.text,
                    'citations': doc.citations,
                    'insurer_name': doc.insurer_name,
                    'product_code': doc.product_code,
                    'similarity': float(similarity),
                    'pages': doc.citations.get('pages', []) if doc.citations else []
                })
            
            if len(formatted_results) >= limit:
                break
        
        logger.info(f"Search returned {len(formatted_results)} results for query: {query[:50]}...")
        return formatted_results
    
    # Legacy methods for compatibility
    
    def embed_text(self, text: str) -> List[float]:
        """Legacy method for generating embeddings (calls _generate_embedding)."""
        return self._generate_embedding(text)
    
    def search_documents(
        self,
        db: Session,
        request: RagSearchRequest
    ) -> RagSearchResponse:
        """Legacy search method for compatibility with existing routers."""
        self.db = db  # Update db session
        
        # Use new search method
        results = self.search(
            query=request.query,
            limit=request.limit,
            tier=None,  # Can be extended to support tier from request
            min_similarity=0.7
        )
        
        # Convert to response format
        documents = []
        for result in results:
            doc_response = RagDocumentResponse(
                id=result['id'],
                title=result['title'],
                insurer_name=result['insurer_name'],
                product_code=result['product_code'],
                section_id=result['section_id'],
                heading=result['heading'],
                text=result['text'],
                citations=result['citations'],
                similarity_score=result['similarity']
            )
            documents.append(doc_response)
        
        return RagSearchResponse(
            query=request.query,
            documents=documents,
            total_results=len(results)
        )
    
    def get_policy_explanation(
        self,
        db: Session,
        question: str,
        product_type: Optional[str] = None
    ) -> str:
        """Get policy explanation for a specific question."""
        self.db = db  # Update db session
        
        # Search for relevant documents
        results = self.search(query=question, limit=3)
        
        if not results:
            return "I couldn't find specific information about that in our policy documents. Please contact our customer service team for assistance."
        
        # Build explanation from search results
        explanation_parts = []
        for doc in results:
            citation = f"Source: {doc['section_id']} ({doc['heading']})"
            explanation_parts.append(f"{doc['text']}\n\n{citation}")
        
        return "\n\n---\n\n".join(explanation_parts)
