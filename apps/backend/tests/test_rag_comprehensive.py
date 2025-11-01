"""
Comprehensive Unit Tests for RAG Service

Tests cover:
- Embedding generation (OpenAI)
- PDF section extraction
- Text chunking
- Full ingestion pipeline
- Vector search with pgvector
- Legacy method compatibility

Run with: pytest apps/backend/tests/test_rag_comprehensive.py -v
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import uuid
from pathlib import Path

from app.services.rag import RAGService
from app.models.rag_document import RagDocument


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    db.rollback = Mock()
    db.close = Mock()
    return db


@pytest.fixture
def rag_service(mock_db):
    """RAG service with mock database."""
    service = RAGService(db=mock_db)
    return service


@pytest.fixture
def mock_openai_embedding():
    """Mock OpenAI embedding response (1536 dimensions)."""
    return [0.1] * 1536


@pytest.fixture
def sample_pdf_text():
    """Sample PDF text with multiple sections."""
    return """
PART 1: INTRODUCTION
This is introductory text.

SECTION 1 – Medical Coverage
Medical coverage includes emergency medical treatment, hospitalization, and medical evacuation.
Coverage is provided up to the sum insured based on your selected plan tier.
This is a comprehensive section with detailed information.

SECTION 2: Baggage Protection
Baggage coverage includes loss, theft, or damage to personal belongings during your trip.
Limits vary by tier: Standard $3,000, Elite $5,000, Premier $10,000.

SECTION 3 – Trip Cancellation
Trip cancellation covers non-refundable expenses if you must cancel due to covered reasons.
Covered reasons include serious illness, injury, natural disasters, and travel warnings.

SECTION 4: Short Section
Too short.

SECTION 5 – Emergency Evacuation
Emergency medical evacuation and repatriation services are provided when medically necessary.
Our assistance team will coordinate your evacuation to appropriate medical facilities.
"""


# ============================================================================
# A. EMBEDDING GENERATION TESTS (5 tests)
# ============================================================================

class TestEmbeddingGeneration:
    """Tests for OpenAI embedding generation."""
    
    def test_generate_embedding_success(self, rag_service):
        """Test successful embedding generation."""
        with patch('openai.OpenAI') as mock_openai:
            # Mock OpenAI client and response
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Generate embedding
            result = rag_service._generate_embedding("test query about medical coverage")
            
            # Assertions
            assert len(result) == 1536
            assert all(isinstance(x, float) for x in result)
            mock_client.embeddings.create.assert_called_once()
            
            # Verify correct model used
            call_args = mock_client.embeddings.create.call_args
            assert call_args.kwargs['model'] == "text-embedding-3-small"
    
    def test_generate_embedding_truncation(self, rag_service):
        """Test that long text is truncated to 32000 chars."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Generate embedding with very long text (40000 chars)
            long_text = "word " * 8000  # ~40000 chars
            result = rag_service._generate_embedding(long_text)
            
            # Check that create was called with truncated text
            call_args = mock_client.embeddings.create.call_args
            input_text = call_args.kwargs['input']
            assert len(input_text) <= 32000
            assert len(result) == 1536
    
    def test_generate_embedding_wrong_dimension(self, rag_service):
        """Test error when OpenAI returns wrong dimension."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 512)]  # Wrong dimension
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Should raise ValueError
            with pytest.raises(ValueError, match="Expected 1536 dimensions, got 512"):
                rag_service._generate_embedding("test")
    
    def test_generate_embedding_api_error(self, rag_service):
        """Test error handling when OpenAI API fails."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_client.embeddings.create.side_effect = Exception("API Error: Rate limit")
            mock_openai.return_value = mock_client
            
            # Should raise exception
            with pytest.raises(Exception, match="API Error"):
                rag_service._generate_embedding("test")
    
    def test_generate_embedding_empty_text(self, rag_service):
        """Test embedding generation with empty text."""
        with patch('openai.OpenAI') as mock_openai:
            mock_client = Mock()
            mock_response = Mock()
            mock_response.data = [Mock(embedding=[0.1] * 1536)]
            mock_client.embeddings.create.return_value = mock_response
            mock_openai.return_value = mock_client
            
            # Should handle empty text gracefully
            result = rag_service._generate_embedding("")
            assert len(result) == 1536


# ============================================================================
# B. TEXT CHUNKING TESTS (6 tests)
# ============================================================================

class TestTextChunking:
    """Tests for text chunking functionality."""
    
    def test_chunk_text_respects_word_limit(self, rag_service):
        """Test that chunks don't exceed word limit."""
        # Create text with exactly 600 words (longer sentences)
        text = ("This is a longer sentence with many words to ensure we actually hit the word limit properly. " * 10)  # ~120 words per repetition
        chunks = rag_service._chunk_text(text, max_words=100)
        
        # Check all chunks are under limit
        for chunk in chunks:
            word_count = len(chunk.split())
            assert word_count <= 110, f"Chunk has {word_count} words, significantly exceeds limit of 100"  # Allow small overage due to sentence preservation
        
        # Should create multiple chunks
        assert len(chunks) >= 2
    
    def test_chunk_text_preserves_sentences(self, rag_service):
        """Test that chunks don't break mid-sentence."""
        text = "First sentence here. Second sentence here. Third sentence here. Fourth sentence here."
        chunks = rag_service._chunk_text(text, max_words=5)
        
        # Each chunk should end with sentence-ending punctuation
        for chunk in chunks:
            if chunk.strip():
                assert chunk.strip()[-1] in ['.', '!', '?'], f"Chunk doesn't end with sentence: '{chunk}'"
    
    def test_chunk_text_handles_empty_input(self, rag_service):
        """Test chunking with empty string."""
        chunks = rag_service._chunk_text("")
        assert chunks == [''] or chunks == []
    
    def test_chunk_text_single_long_sentence(self, rag_service):
        """Test with one sentence exceeding word limit."""
        # One sentence with 600 words
        long_sentence = " ".join(["word"] * 600) + "."
        chunks = rag_service._chunk_text(long_sentence, max_words=100)
        
        # Should still create a chunk (won't break mid-sentence)
        assert len(chunks) >= 1
        # First chunk might exceed limit due to sentence preservation
        assert chunks[0].endswith('.')
    
    def test_chunk_text_multiple_chunks(self, rag_service):
        """Test text that requires multiple chunks."""
        # Create text that should produce exactly 3 chunks
        sentences = ["Sentence number {}.".format(i) for i in range(1, 151)]  # 150 sentences
        text = " ".join(sentences)
        chunks = rag_service._chunk_text(text, max_words=100)
        
        # Should create multiple chunks
        assert len(chunks) >= 3
        # All should end with punctuation
        assert all(chunk.strip()[-1] in ['.', '!', '?'] for chunk in chunks if chunk.strip())
    
    def test_chunk_text_special_characters(self, rag_service):
        """Test chunking with special characters."""
        text = """This is a test! Does it handle questions? It should handle "quotes" and – dashes.
Also unicode: café, naïve, 你好. More sentences here."""
        
        chunks = rag_service._chunk_text(text, max_words=20)
        
        # Should not crash
        assert len(chunks) > 0
        # Should preserve special characters
        combined = " ".join(chunks)
        assert "café" in combined or "caf" in combined  # May normalize
        assert "?" in combined
        assert "!" in combined


# ============================================================================
# C. PDF EXTRACTION TESTS (5 tests)
# ============================================================================

class TestPDFExtraction:
    """Tests for PDF section extraction."""
    
    @patch('pdfplumber.open')
    def test_extract_sections_finds_all_sections(self, mock_pdfplumber, rag_service):
        """Test that all sections are found in PDF."""
        # Mock PDF with multiple sections (with sufficient content >50 chars)
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
SECTION 1 – Medical Coverage
This section covers medical expenses up to $500,000 including emergency treatment and hospitalization.

SECTION 2: Baggage Protection  
This section covers lost or damaged baggage during your trip with limits varying by tier.

SECTION 3 – Trip Cancellation
This section covers trip cancellation for covered reasons such as illness or injury.

SECTION 4: Emergency Services
This section covers emergency evacuation and repatriation services when needed.

SECTION 5 – Personal Liability
This section covers personal liability claims that arise during your travels.
"""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Extract sections
        sections = rag_service._extract_sections_from_pdf("test.pdf")
        
        # Should find all 5 sections (all have >50 chars)
        assert len(sections) == 5
        assert sections[0]['section_id'] == 'Section 1'
        assert sections[0]['heading'] == 'Medical Coverage'
        assert 'medical expenses' in sections[0]['text'].lower()
    
    @patch('pdfplumber.open')
    def test_extract_sections_handles_various_formats(self, mock_pdfplumber, rag_service):
        """Test extraction with different section formats."""
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
SECTION 1 – With Dash
Content here with sufficient length to pass the 50 character minimum filter.

Section 2: With Colon
Content here with sufficient length to pass the 50 character minimum filter.

SECTION 3 Simple
Content here with sufficient length to pass the 50 character minimum filter.

Section 41 — With Em Dash
Content here with sufficient length to not be filtered out during extraction.
"""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        sections = rag_service._extract_sections_from_pdf("test.pdf")
        
        # All formats should be recognized
        assert len(sections) >= 3
        section_ids = [s['section_id'] for s in sections]
        assert 'Section 1' in section_ids
        assert 'Section 2' in section_ids or 'Section 3' in section_ids  # At least some found
        assert 'Section 41' in section_ids
    
    @patch('pdfplumber.open')
    def test_extract_sections_skips_short_sections(self, mock_pdfplumber, rag_service):
        """Test that very short sections are skipped."""
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
SECTION 1 – Short
Too short.

SECTION 2 – Long Section
This is a much longer section with plenty of content that should not be skipped 
because it has enough text to be considered valid and useful for our policy 
documentation and search functionality.
"""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        sections = rag_service._extract_sections_from_pdf("test.pdf")
        
        # Only the long section should be extracted (>50 chars)
        assert len(sections) == 1
        assert sections[0]['section_id'] == 'Section 2'
        assert len(sections[0]['text']) > 50
    
    @patch('pdfplumber.open')
    def test_extract_sections_tracks_page_numbers(self, mock_pdfplumber, rag_service):
        """Test that page numbers are tracked correctly."""
        mock_pdf = MagicMock()
        
        # Create multiple pages with sufficient content
        mock_page1 = Mock()
        mock_page1.extract_text.return_value = "SECTION 1 – First Section\nContent on page 1 with sufficient text for extraction to work properly.\n"
        
        mock_page2 = Mock()
        mock_page2.extract_text.return_value = "More content on page 2 that continues the first section.\n"
        
        mock_page3 = Mock()
        mock_page3.extract_text.return_value = "SECTION 2 – Second Section\nContent on page 3 with sufficient text for proper extraction.\n"
        
        mock_pdf.pages = [mock_page1, mock_page2, mock_page3]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        sections = rag_service._extract_sections_from_pdf("test.pdf")
        
        # Verify page numbers are tracked
        assert len(sections) >= 1
        assert 'pages' in sections[0]
        assert isinstance(sections[0]['pages'], list)
        assert len(sections[0]['pages']) > 0
    
    @patch('pdfplumber.open')
    def test_extract_sections_empty_pdf(self, mock_pdfplumber, rag_service):
        """Test extraction from PDF with no sections."""
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = "This is just regular text with no sections."
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        sections = rag_service._extract_sections_from_pdf("test.pdf")
        
        # Should return empty list (no sections found)
        assert sections == []


# ============================================================================
# D. FULL INGESTION TESTS (4 tests)
# ============================================================================

class TestIngestion:
    """Tests for PDF ingestion pipeline."""
    
    @patch('pathlib.Path.exists')
    @patch('pdfplumber.open')
    def test_ingest_pdf_full_pipeline(self, mock_pdfplumber, mock_path_exists, rag_service, mock_db):
        """Test complete PDF ingestion pipeline."""
        # Mock file exists check
        mock_path_exists.return_value = True
        
        # Mock PDF
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
SECTION 1 – Medical Coverage
This comprehensive section describes medical coverage including emergency treatment, 
hospitalization, and medical evacuation. Coverage is provided up to the sum insured 
based on your selected plan tier.

SECTION 2 – Baggage Protection
This section covers loss or damage to personal belongings during your trip with specific limits.
"""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Mock embedding generation
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            # Ingest PDF
            result = rag_service.ingest_pdf(
                pdf_path="test.pdf",
                title="Test Policy",
                insurer_name="Test Insurer",
                product_code="TEST123",
                tier="elite"
            )
            
            # Verify ingestion stats
            assert result['sections_found'] == 2
            assert result['documents_stored'] >= 2
            assert mock_db.add.called
            assert mock_db.commit.called
    
    def test_ingest_pdf_file_not_found(self, rag_service):
        """Test handling of missing PDF file."""
        with pytest.raises(FileNotFoundError, match="PDF not found"):
            rag_service.ingest_pdf(
                pdf_path="/nonexistent/file.pdf",
                title="Test",
                insurer_name="Test",
                product_code="TEST"
            )
    
    @patch('pathlib.Path.exists')
    @patch('pdfplumber.open')
    def test_ingest_pdf_embedding_failure_continues(self, mock_pdfplumber, mock_path_exists, rag_service, mock_db):
        """Test that ingestion continues when one embedding fails."""
        # Mock file exists check
        mock_path_exists.return_value = True
        
        # Mock PDF with 3 sections
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
SECTION 1 – Good Section One
This section will succeed with sufficient content for testing purposes and proper extraction.

SECTION 2 – Will Fail  
This section will fail during embedding generation for testing error handling properly.

SECTION 3 – Good Section Three
This section will succeed again with sufficient content for our tests to validate continuation.
"""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        # Mock embedding to fail on second section
        call_count = [0]
        def mock_embed_side_effect(text):
            call_count[0] += 1
            if call_count[0] == 2:
                raise Exception("Embedding failed")
            return [0.1] * 1536
        
        with patch.object(rag_service, '_generate_embedding', side_effect=mock_embed_side_effect):
            result = rag_service.ingest_pdf(
                pdf_path="test.pdf",
                title="Test Policy",
                insurer_name="Test",
                product_code="TEST"
            )
            
            # Should still process other sections
            assert result['sections_found'] == 3
            # Only 2 should be stored (section 2 failed)
            assert result['documents_stored'] == 2
    
    @patch('pathlib.Path.exists')
    @patch('pdfplumber.open')
    def test_ingest_pdf_with_tier_metadata(self, mock_pdfplumber, mock_path_exists, rag_service, mock_db):
        """Test that tier metadata is stored in citations."""
        # Mock file exists check
        mock_path_exists.return_value = True
        
        mock_pdf = MagicMock()
        mock_page = Mock()
        mock_page.extract_text.return_value = """
SECTION 1 – Test Section
This section has sufficient content for ingestion and testing purposes to validate metadata.
"""
        mock_pdf.pages = [mock_page]
        mock_pdfplumber.return_value.__enter__.return_value = mock_pdf
        
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = rag_service.ingest_pdf(
                pdf_path="test.pdf",
                title="Elite Policy",
                insurer_name="MSIG",
                product_code="ELITE001",
                tier="elite"
            )
            
            # Verify db.add was called
            assert mock_db.add.called
            
            # Get the document that was added
            call_args = mock_db.add.call_args_list[0]
            doc = call_args[0][0]
            
            # Verify tier in citations
            assert doc.citations is not None
            assert doc.citations.get('tier') == "elite"


# ============================================================================
# E. VECTOR SEARCH TESTS (7 tests)
# ============================================================================

class TestVectorSearch:
    """Tests for pgvector similarity search."""
    
    def test_search_returns_results(self, rag_service, mock_db):
        """Test that search returns formatted results."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.5] * 1536
            
            # Mock database query result
            mock_doc = Mock(spec=RagDocument)
            mock_doc.id = uuid.uuid4()
            mock_doc.title = "Test Policy"
            mock_doc.section_id = "Section 1"
            mock_doc.heading = "Medical Coverage"
            mock_doc.text = "Medical coverage up to $500,000"
            mock_doc.citations = {"pages": [1, 2], "tier": "elite"}
            mock_doc.insurer_name = "MSIG"
            mock_doc.product_code = "TEST123"
            
            # Mock query chain
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value.limit.return_value.all.return_value = [
                (mock_doc, 0.85)  # (document, similarity)
            ]
            mock_db.query.return_value = mock_query
            
            # Execute search
            results = rag_service.search("medical coverage", limit=5)
            
            # Assertions
            assert len(results) == 1
            assert results[0]['similarity'] == 0.85
            assert results[0]['section_id'] == "Section 1"
            assert results[0]['heading'] == "Medical Coverage"
            assert results[0]['pages'] == [1, 2]
    
    def test_search_filters_by_tier(self, rag_service, mock_db):
        """Test search with tier filtering."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.5] * 1536
            
            mock_doc = Mock(spec=RagDocument)
            mock_doc.id = uuid.uuid4()
            mock_doc.title = "Elite Policy"
            mock_doc.section_id = "Section 1"
            mock_doc.heading = "Medical"
            mock_doc.text = "Content"
            mock_doc.citations = {"tier": "elite", "pages": [1]}
            mock_doc.insurer_name = "MSIG"
            mock_doc.product_code = "ELITE"
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value.limit.return_value.all.return_value = [(mock_doc, 0.8)]
            mock_db.query.return_value = mock_query
            
            # Search with tier filter
            results = rag_service.search("test query", tier="elite")
            
            # Verify filter was applied
            assert mock_query.filter.called
            assert len(results) == 1
    
    def test_search_filters_low_similarity(self, rag_service, mock_db):
        """Test that low similarity results are filtered out."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.5] * 1536
            
            # Create mock docs with varying similarity
            high_sim_doc = Mock(spec=RagDocument)
            high_sim_doc.id = uuid.uuid4()
            high_sim_doc.title = "High Match"
            high_sim_doc.section_id = "Section 1"
            high_sim_doc.heading = "Medical"
            high_sim_doc.text = "Content"
            high_sim_doc.citations = {"pages": [1]}
            high_sim_doc.insurer_name = "MSIG"
            high_sim_doc.product_code = "TEST"
            
            low_sim_doc = Mock(spec=RagDocument)
            low_sim_doc.id = uuid.uuid4()
            low_sim_doc.title = "Low Match"
            low_sim_doc.section_id = "Section 2"
            low_sim_doc.heading = "Other"
            low_sim_doc.text = "Content"
            low_sim_doc.citations = {"pages": [2]}
            low_sim_doc.insurer_name = "MSIG"
            low_sim_doc.product_code = "TEST"
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value.limit.return_value.all.return_value = [
                (high_sim_doc, 0.75),  # Above threshold
                (low_sim_doc, 0.35)     # Below threshold
            ]
            mock_db.query.return_value = mock_query
            
            # Search with min_similarity=0.5
            results = rag_service.search("test", min_similarity=0.5)
            
            # Only high similarity result should be returned
            assert len(results) == 1
            assert results[0]['similarity'] == 0.75
    
    def test_search_respects_limit(self, rag_service, mock_db):
        """Test that search respects the limit parameter."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.5] * 1536
            
            # Create 10 mock documents
            mock_docs = []
            for i in range(10):
                doc = Mock(spec=RagDocument)
                doc.id = uuid.uuid4()
                doc.title = f"Doc {i}"
                doc.section_id = f"Section {i}"
                doc.heading = f"Heading {i}"
                doc.text = f"Content {i}"
                doc.citations = {"pages": [i]}
                doc.insurer_name = "MSIG"
                doc.product_code = "TEST"
                mock_docs.append((doc, 0.6 + i * 0.01))
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value.limit.return_value.all.return_value = mock_docs
            mock_db.query.return_value = mock_query
            
            # Search with limit=3
            results = rag_service.search("test", limit=3)
            
            # Should return exactly 3 results
            assert len(results) == 3
    
    def test_search_embedding_failure(self, rag_service):
        """Test search when embedding generation fails."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.side_effect = Exception("OpenAI API error")
            
            # Search should return empty list, not crash
            results = rag_service.search("test query")
            
            assert results == []
    
    def test_search_empty_database(self, rag_service, mock_db):
        """Test search when database has no documents."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.5] * 1536
            
            # Mock empty query result
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            mock_query.order_by.return_value.limit.return_value.all.return_value = []
            mock_db.query.return_value = mock_query
            
            results = rag_service.search("test query")
            
            assert results == []
    
    def test_search_sorts_by_similarity(self, rag_service, mock_db):
        """Test that results are sorted by similarity (highest first)."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.5] * 1536
            
            # Create docs with different similarities (returned in random order)
            docs = []
            for sim in [0.55, 0.75, 0.62, 0.91, 0.48]:
                doc = Mock(spec=RagDocument)
                doc.id = uuid.uuid4()
                doc.title = f"Doc sim={sim}"
                doc.section_id = "Section 1"
                doc.heading = "Test"
                doc.text = "Content"
                doc.citations = {"pages": [1]}
                doc.insurer_name = "MSIG"
                doc.product_code = "TEST"
                docs.append((doc, sim))
            
            mock_query = Mock()
            mock_query.filter.return_value = mock_query
            # pgvector already sorts by distance, so return in sorted order
            mock_query.order_by.return_value.limit.return_value.all.return_value = sorted(
                docs, key=lambda x: 1 - x[1]  # Sort by distance (ascending)
            )
            mock_db.query.return_value = mock_query
            
            results = rag_service.search("test", limit=5, min_similarity=0.5)
            
            # Results should be sorted by similarity (highest first)
            similarities = [r['similarity'] for r in results]
            assert similarities == sorted(similarities, reverse=True)
            assert results[0]['similarity'] == 0.91  # Highest


# ============================================================================
# F. LEGACY METHOD TESTS (2 tests)
# ============================================================================

class TestLegacyMethods:
    """Tests for backward compatibility methods."""
    
    def test_embed_text_calls_generate_embedding(self, rag_service):
        """Test that legacy embed_text method works."""
        with patch.object(rag_service, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = rag_service.embed_text("test text")
            
            # Should call new method
            mock_embed.assert_called_once_with("test text")
            assert result == [0.1] * 1536
    
    def test_search_documents_compatibility(self, rag_service, mock_db):
        """Test legacy search_documents method with schemas."""
        from app.schemas.rag import RagSearchRequest, RagSearchResponse
        
        with patch.object(rag_service, 'search') as mock_search:
            # Mock new search method
            mock_search.return_value = [
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Test',
                    'section_id': 'Section 1',
                    'heading': 'Medical',
                    'text': 'Content',
                    'citations': {},
                    'insurer_name': 'MSIG',
                    'product_code': 'TEST',
                    'similarity': 0.85,
                    'pages': [1]
                }
            ]
            
            request = RagSearchRequest(
                query="test query",
                limit=5
            )
            
            response = rag_service.search_documents(mock_db, request)
            
            # Should return RagSearchResponse
            assert isinstance(response, RagSearchResponse)
            assert response.query == "test query"
            assert len(response.documents) == 1
            assert response.documents[0].similarity_score == 0.85


# ============================================================================
# TEST SUMMARY
# ============================================================================

def test_count():
    """Meta-test to verify we have all 29 tests."""
    import inspect
    
    # Count test methods
    test_classes = [
        TestEmbeddingGeneration,
        TestTextChunking,
        TestPDFExtraction,
        TestIngestion,
        TestVectorSearch,
        TestLegacyMethods
    ]
    
    total_tests = 0
    for test_class in test_classes:
        methods = [m for m in dir(test_class) if m.startswith('test_')]
        total_tests += len(methods)
    
    # Add this meta-test
    total_tests += 1
    
    print(f"\n📊 Total unit tests: {total_tests}")
    assert total_tests >= 29, f"Expected 29+ tests, found {total_tests}"

