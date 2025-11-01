"""
OCR Test Case: Real Insurance Policy Documents

Tests PDF extraction and RAG ingestion with actual Ancileo/MSIG policy documents.

Test Documents:
- TA477274.pdf: Actual issued policy document
- Tiq Travel Policy Wording.pdf: Full policy wording (5837 lines)

Purpose: Validate RAG pipeline with production-quality policy documents

Run with: pytest apps/backend/tests/test_ocr_policy_docs.py -v -s
"""

import pytest
from pathlib import Path
import sys
from unittest.mock import Mock, patch, MagicMock

# Skip if OCR dependencies not installed
pytesseract_available = True
pdf2image_available = True

try:
    import pytesseract
except ImportError:
    pytesseract_available = False

try:
    import pdf2image
except ImportError:
    pdf2image_available = False


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def policy_doc_ta477274():
    """Path to TA477274.pdf (issued policy document)."""
    pdf_path = Path(__file__).parent.parent.parent.parent / "ancileo-msig-reference" / "TA477274.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Policy document not found at {pdf_path}")
    
    return str(pdf_path)


@pytest.fixture
def policy_wording_tiq():
    """Path to Tiq Travel Policy Wording.pdf (full policy terms)."""
    pdf_path = Path(__file__).parent.parent.parent.parent / "ancileo-msig-reference" / "Tiq Travel Policy Wording.pdf"
    
    if not pdf_path.exists():
        pytest.skip(f"Policy wording not found at {pdf_path}")
    
    return str(pdf_path)


@pytest.fixture
def mock_db():
    """Mock database session."""
    db = Mock()
    db.query = Mock()
    db.add = Mock()
    db.commit = Mock()
    return db


# ============================================================================
# TESTS
# ============================================================================

class TestPolicyDocumentExtraction:
    """Test extraction from real insurance policy documents."""
    
    def test_ta477274_pdf_readable(self, policy_doc_ta477274):
        """Test that pdfplumber can read TA477274.pdf."""
        import pdfplumber
        
        with pdfplumber.open(policy_doc_ta477274) as pdf:
            # Verify PDF is valid
            assert len(pdf.pages) > 0, "PDF has no pages"
            
            # Extract text from first page
            first_page_text = pdf.pages[0].extract_text()
            
            # Verify we got some text
            assert first_page_text is not None
            assert len(first_page_text) > 0
            
            print(f"\n📄 TA477274.pdf Analysis:")
            print(f"   Pages: {len(pdf.pages)}")
            print(f"   First page: {len(first_page_text)} characters")
            print(f"\n--- First 500 characters ---")
            print(first_page_text[:500])
    
    def test_tiq_wording_pdf_readable(self, policy_wording_tiq):
        """Test that pdfplumber can read Tiq Policy Wording PDF."""
        import pdfplumber
        
        with pdfplumber.open(policy_wording_tiq) as pdf:
            assert len(pdf.pages) > 0, "PDF has no pages"
            
            first_page_text = pdf.pages[0].extract_text()
            
            assert first_page_text is not None
            assert len(first_page_text) > 0
            
            print(f"\n📄 Tiq Policy Wording Analysis:")
            print(f"   Pages: {len(pdf.pages)}")
            print(f"   First page: {len(first_page_text)} characters")
            print(f"\n--- First 500 characters ---")
            print(first_page_text[:500])
    
    def test_extract_insurance_keywords(self, policy_doc_ta477274, policy_wording_tiq):
        """Test extraction of insurance-specific keywords from both documents."""
        import pdfplumber
        
        documents = {
            "TA477274": policy_doc_ta477274,
            "Tiq Wording": policy_wording_tiq
        }
        
        for doc_name, doc_path in documents.items():
            with pdfplumber.open(doc_path) as pdf:
                full_text = ""
                for page in pdf.pages[:5]:  # First 5 pages only for speed
                    page_text = page.extract_text()
                    if page_text:
                        full_text += page_text + "\n"
                
                print(f"\n📄 {doc_name}:")
                print(f"   Total pages: {len(pdf.pages)}")
                print(f"   Extracted from first 5 pages: {len(full_text)} characters")
                
                # Look for insurance keywords
                insurance_keywords = [
                    "policy", "coverage", "insured", "premium",
                    "medical", "baggage", "cancellation", "claim",
                    "exclusion", "benefit", "deductible"
                ]
                
                found_keywords = [kw for kw in insurance_keywords if kw.lower() in full_text.lower()]
                
                print(f"   Keywords found ({len(found_keywords)}/{len(insurance_keywords)}): {', '.join(found_keywords[:5])}...")
                
                # Should find at least half the keywords
                assert len(found_keywords) >= len(insurance_keywords) // 2, f"Too few insurance keywords in {doc_name}"
    
    def test_extract_sections_from_tiq_wording(self, policy_wording_tiq, mock_db):
        """Test RAG service can extract sections from Tiq policy wording."""
        from app.services.rag import RAGService
        
        rag = RAGService(db=mock_db)
        
        # Extract sections
        sections = rag._extract_sections_from_pdf(policy_wording_tiq)
        
        print(f"\n📑 Tiq Policy Wording - Extracted {len(sections)} sections")
        
        # Print first 10 sections
        for i, section in enumerate(sections[:10], 1):
            print(f"\n[{i}] {section['section_id']} - {section['heading']}")
            print(f"    Pages: {section['pages']}")
            print(f"    Text preview: {section['text'][:80]}...")
        
        # Policy wording should have many sections
        assert len(sections) > 10, f"Expected many sections in policy wording, got {len(sections)}"
        print(f"\n✅ Successfully extracted {len(sections)} sections from Tiq Policy Wording")


class TestPolicyDocumentContent:
    """Test extracting specific information from policy documents."""
    
    def test_ta477274_structure(self, policy_doc_ta477274):
        """Analyze structure of TA477274 policy document."""
        import pdfplumber
        
        with pdfplumber.open(policy_doc_ta477274) as pdf:
            print(f"\n📋 TA477274.pdf Structure:")
            print(f"   Total pages: {len(pdf.pages)}")
            
            # Check if encrypted/password protected
            print(f"   Encrypted: {pdf.doc is not None and hasattr(pdf.doc, 'is_encrypted')}")
            
            # Try to extract from a few pages
            readable_pages = 0
            total_chars = 0
            
            for i, page in enumerate(pdf.pages[:3], 1):
                text = page.extract_text()
                if text and len(text) > 10:
                    readable_pages += 1
                    total_chars += len(text)
                    print(f"   Page {i}: {len(text)} chars")
            
            print(f"   Readable pages (first 3): {readable_pages}/3")
            print(f"   Total chars extracted: {total_chars}")
            
            # Should be able to read at least some pages
            assert readable_pages > 0, "Could not read any pages from TA477274"
    
    def test_tiq_wording_sections(self, policy_wording_tiq):
        """Test Tiq policy wording for section markers."""
        import pdfplumber
        import re
        
        with pdfplumber.open(policy_wording_tiq) as pdf:
            full_text = ""
            # Sample first 20 pages
            for page in pdf.pages[:20]:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
            
            print(f"\n📋 Tiq Policy Wording Content Analysis:")
            print(f"   Total pages: {len(pdf.pages)}")
            print(f"   Sampled first 20 pages: {len(full_text)} characters")
            
            # Find section markers
            section_pattern = r'(?:^|\n)(?:SECTION|Section)\s+(\d+)'
            sections = re.findall(section_pattern, full_text)
            
            print(f"   Sections found in sample: {len(sections)}")
            if sections:
                print(f"   Section numbers: {', '.join(sections[:10])}...")
            
            # Look for coverage types
            coverage_types = ["medical", "baggage", "cancellation", "delay", "emergency"]
            found_coverage = [c for c in coverage_types if c.lower() in full_text.lower()]
            
            print(f"   Coverage types found: {', '.join(found_coverage)}")
            
            assert len(found_coverage) >= 3, "Should find multiple coverage types"


class TestPolicyDocumentAsRAGSource:
    """Test using real policy documents for RAG ingestion."""
    
    def test_ingest_tiq_policy_wording(self, policy_wording_tiq, mock_db):
        """Test that Tiq policy wording can be ingested into RAG system."""
        from app.services.rag import RAGService
        
        rag = RAGService(db=mock_db)
        
        # Mock embedding generation to avoid API calls
        with patch.object(rag, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            # Attempt to ingest
            result = rag.ingest_pdf(
                pdf_path=policy_wording_tiq,
                title="Tiq Travel Insurance Policy Wording",
                insurer_name="MSIG",
                product_code="TIQ-WORDING",
                tier="all"  # Policy wording applies to all tiers
            )
            
            print(f"\n📊 Tiq Wording Ingestion Results:")
            print(f"   Sections found: {result['sections_found']}")
            print(f"   Chunks created: {result['chunks_created']}")
            print(f"   Documents stored: {result['documents_stored']}")
            
            # Policy wording should have substantial content
            assert result['sections_found'] > 0, "Should find sections in policy wording"
            assert result['documents_stored'] > 0, "Should store documents"
            
            print(f"\n✅ Successfully ingested Tiq policy wording")
    
    def test_ingest_ta477274(self, policy_doc_ta477274, mock_db):
        """Test ingestion of TA477274 policy document."""
        from app.services.rag import RAGService
        
        rag = RAGService(db=mock_db)
        
        with patch.object(rag, '_generate_embedding') as mock_embed:
            mock_embed.return_value = [0.1] * 1536
            
            result = rag.ingest_pdf(
                pdf_path=policy_doc_ta477274,
                title="MSIG Policy TA477274",
                insurer_name="MSIG",
                product_code="TA477274",
                tier=None
            )
            
            print(f"\n📊 TA477274 Ingestion Results:")
            print(f"   Sections found: {result['sections_found']}")
            print(f"   Chunks created: {result['chunks_created']}")
            print(f"   Documents stored: {result['documents_stored']}")
            
            # Document should ingest without errors
            assert result['sections_found'] >= 0
            assert result['chunks_created'] >= 0
            
            if result['sections_found'] == 0:
                print(f"\n⚠️  No sections found (may be encrypted or non-standard format)")
            else:
                print(f"\n✅ Successfully extracted sections from TA477274")


class TestPolicyDocumentStructure:
    """Analyze the structure of policy documents."""
    
    def test_compare_document_sizes(self, policy_doc_ta477274, policy_wording_tiq):
        """Compare sizes of the two policy documents."""
        import pdfplumber
        
        print(f"\n{'='*60}")
        print(f"POLICY DOCUMENT COMPARISON")
        print(f"{'='*60}")
        
        docs = {
            "TA477274 (Issued Policy)": policy_doc_ta477274,
            "Tiq Policy Wording": policy_wording_tiq
        }
        
        for name, path in docs.items():
            with pdfplumber.open(path) as pdf:
                page_count = len(pdf.pages)
                
                # Extract sample text
                sample_text = ""
                for page in pdf.pages[:3]:
                    text = page.extract_text()
                    if text:
                        sample_text += text
                
                print(f"\n📄 {name}:")
                print(f"   Pages: {page_count}")
                print(f"   Sample text (first 3 pages): {len(sample_text)} chars")
                print(f"   Avg chars/page: {len(sample_text) // min(3, page_count) if page_count > 0 else 0}")
        
        print(f"\n{'='*60}")
    
    def test_tiq_wording_text_preview(self, policy_wording_tiq):
        """Extract and preview text from Tiq policy wording."""
        import pdfplumber
        
        with pdfplumber.open(policy_wording_tiq) as pdf:
            print(f"\n{'='*60}")
            print(f"TIQ POLICY WORDING - TEXT PREVIEW")
            print(f"{'='*60}")
            print(f"Total pages: {len(pdf.pages)}")
            
            # Extract first page
            first_page = pdf.pages[0]
            text = first_page.extract_text()
            
            if text:
                print(f"\n--- PAGE 1 (first 1000 characters) ---")
                print(text[:1000])
            else:
                print("\n⚠️  Could not extract text from first page")
            
            print(f"\n{'='*60}")


# ============================================================================
# INTEGRATION TEST: OCR Service
# ============================================================================

class TestRAGServiceWithPolicyDocs:
    """Test RAG service with real policy documents."""
    
    def test_chunk_policy_text(self, policy_wording_tiq, mock_db):
        """Test chunking of policy document text."""
        import pdfplumber
        from app.services.rag import RAGService
        
        rag = RAGService(db=mock_db)
        
        # Extract a page of text
        with pdfplumber.open(policy_wording_tiq) as pdf:
            page_text = pdf.pages[5].extract_text() if len(pdf.pages) > 5 else pdf.pages[0].extract_text()
        
        if page_text and len(page_text) > 100:
            # Chunk the text
            chunks = rag._chunk_text(page_text, max_words=500)
            
            print(f"\n✂️  Text Chunking Results:")
            print(f"   Original text: {len(page_text)} chars, {len(page_text.split())} words")
            print(f"   Chunks created: {len(chunks)}")
            
            for i, chunk in enumerate(chunks[:3], 1):
                word_count = len(chunk.split())
                print(f"   Chunk {i}: {word_count} words, {len(chunk)} chars")
            
            # Verify chunks are reasonable
            assert len(chunks) > 0, "Should create at least one chunk"
            
            # Check word limits
            for chunk in chunks:
                words = len(chunk.split())
                # Allow some overage due to sentence preservation
                assert words <= 550, f"Chunk exceeded limit: {words} words"
            
            print(f"\n✅ Text chunking working correctly")


# ============================================================================
# PRACTICAL USE CASE TESTS
# ============================================================================

class TestPolicyDocumentRAGSuitability:
    """Test suitability of policy documents for RAG Q&A."""
    
    def test_tiq_wording_rag_suitability(self, policy_wording_tiq):
        """Assess Tiq policy wording for RAG Q&A suitability."""
        import pdfplumber
        
        with pdfplumber.open(policy_wording_tiq) as pdf:
            # Sample first 30 pages for analysis
            sample_text = ""
            for page in pdf.pages[:30]:
                text = page.extract_text()
                if text:
                    sample_text += text
        
        word_count = len(sample_text.split())
        char_count = len(sample_text)
        
        # Check for Q&A-relevant content
        qa_keywords = [
            "covered", "coverage", "limit", "exclusion",
            "benefit", "claim", "emergency", "medical",
            "baggage", "cancellation", "delay", "deductible",
            "reimbursement", "indemnity", "policyholder"
        ]
        
        keyword_count = sum(1 for keyword in qa_keywords if keyword.lower() in sample_text.lower())
        
        print(f"\n📈 Tiq Policy Wording - RAG Suitability:")
        print(f"   Total pages: {len(pdf.pages)}")
        print(f"   Sample (30 pages) - Words: {word_count}, Chars: {char_count}")
        print(f"   Q&A keywords found: {keyword_count}/{len(qa_keywords)}")
        
        # Determine suitability
        if keyword_count >= 10:
            suitability = "✅ EXCELLENT - Comprehensive policy content"
        elif keyword_count >= 5:
            suitability = "✅ SUITABLE - Good policy coverage"
        else:
            suitability = "⚠️  LIMITED - Few coverage details"
        
        print(f"\n{suitability}")
        
        assert keyword_count >= 5, "Should have substantial policy content"
    
    def test_compare_both_documents_for_rag(self, policy_doc_ta477274, policy_wording_tiq):
        """Compare both documents for RAG ingestion value."""
        import pdfplumber
        
        print(f"\n{'='*60}")
        print(f"RAG INGESTION VALUE COMPARISON")
        print(f"{'='*60}")
        
        docs = {
            "TA477274": policy_doc_ta477274,
            "Tiq Wording": policy_wording_tiq
        }
        
        for name, path in docs.items():
            with pdfplumber.open(path) as pdf:
                # Sample first few pages
                sample_size = min(10, len(pdf.pages))
                sample_text = ""
                
                for page in pdf.pages[:sample_size]:
                    text = page.extract_text()
                    if text:
                        sample_text += text
                
                word_count = len(sample_text.split())
                
                # Count insurance keywords
                keywords = ["medical", "coverage", "benefit", "exclusion", "claim"]
                found = sum(1 for kw in keywords if kw in sample_text.lower())
                
                print(f"\n{name}:")
                print(f"   Pages: {len(pdf.pages)}")
                print(f"   Sample: {sample_size} pages, {word_count} words")
                print(f"   Key terms: {found}/{len(keywords)}")
                
                # Recommendation
                if found >= 4 and word_count > 2000:
                    print(f"   → ✅ RECOMMENDED for RAG ingestion")
                elif found >= 2:
                    print(f"   → ⚠️  OK for RAG, limited content")
                else:
                    print(f"   → ❌ NOT RECOMMENDED")
        
        print(f"\n{'='*60}")


# ============================================================================
# RUN SUMMARY
# ============================================================================

def test_policy_docs_summary():
    """Summary test that always passes and prints info."""
    print(f"\n{'='*60}")
    print(f"POLICY DOCUMENT OCR TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Documents Tested:")
    print(f"  1. TA477274.pdf - Actual issued policy")
    print(f"  2. Tiq Travel Policy Wording.pdf - Full T&Cs")
    print(f"Purpose: Validate RAG pipeline with real insurance documents")
    print(f"{'='*60}")
    
    assert True  # Meta-test


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

