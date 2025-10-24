"""Tests for RAG service."""

import pytest
from unittest.mock import Mock, patch
from app.services.rag import RagService
from app.schemas.rag import RagSearchRequest


class TestRagService:
    """Test cases for RAG service."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.rag_service = RagService()
    
    def test_embed_text(self):
        """Test text embedding generation."""
        text = "This is a test document about travel insurance."
        
        embedding = self.rag_service.embed_text(text)
        
        assert isinstance(embedding, list)
        assert len(embedding) == self.rag_service.embedding_dimension
        assert all(isinstance(x, float) for x in embedding)
    
    @patch('app.services.rag.text')
    def test_search_documents(self, mock_text):
        """Test document search functionality."""
        # Mock database session and query results
        mock_db = Mock()
        mock_result = Mock()
        mock_result.id = "test-id"
        mock_result.title = "Test Document"
        mock_result.insurer_name = "Test Insurer"
        mock_result.product_code = "TEST"
        mock_result.section_id = "1.1"
        mock_result.heading = "Test Section"
        mock_result.text = "This is test content about travel insurance."
        mock_result.citations = {"section": "1.1", "page": 1}
        
        mock_db.execute.return_value.fetchall.return_value = [mock_result]
        
        search_request = RagSearchRequest(
            query="travel insurance",
            limit=5
        )
        
        result = self.rag_service.search_documents(mock_db, search_request)
        
        assert result.query == "travel insurance"
        assert len(result.documents) == 1
        assert result.documents[0].title == "Test Document"
        assert result.documents[0].text == "This is test content about travel insurance."
        assert result.total_results == 1
    
    def test_ingest_document(self):
        """Test document ingestion."""
        mock_db = Mock()
        
        documents = self.rag_service.ingest_document(
            mock_db,
            "Test Policy",
            "Test Insurer",
            "TEST_POLICY",
            "This is a test policy document with multiple sections.",
            split_by_sections=True
        )
        
        assert len(documents) > 0
        assert all(doc.title == "Test Policy" for doc in documents)
        assert all(doc.insurer_name == "Test Insurer" for doc in documents)
        assert all(doc.product_code == "TEST_POLICY" for doc in documents)
    
    def test_split_content_by_sections(self):
        """Test content splitting functionality."""
        content = "This is a test document with multiple sections."
        
        sections = self.rag_service._split_content_by_sections(content)
        
        assert len(sections) > 0
        assert all("heading" in section for section in sections)
        assert all("text" in section for section in sections)
        assert all("citations" in section for section in sections)
    
    @patch('app.services.rag.text')
    def test_get_policy_explanation(self, mock_text):
        """Test policy explanation generation."""
        mock_db = Mock()
        mock_result = Mock()
        mock_result.id = "test-id"
        mock_result.title = "Test Policy"
        mock_result.section_id = "2.1"
        mock_result.text = "Medical coverage up to $100,000."
        mock_result.citations = {"section": "2.1", "page": 5}
        
        mock_db.execute.return_value.fetchall.return_value = [mock_result]
        
        explanation = self.rag_service.get_policy_explanation(
            mock_db,
            "What is covered for medical expenses?",
            "TEST_POLICY"
        )
        
        assert "Medical coverage up to $100,000" in explanation
        assert "Source: §2.1" in explanation
    
    def test_get_policy_explanation_no_results(self):
        """Test policy explanation when no results found."""
        mock_db = Mock()
        mock_db.execute.return_value.fetchall.return_value = []
        
        explanation = self.rag_service.get_policy_explanation(
            mock_db,
            "What is covered for medical expenses?",
            "TEST_POLICY"
        )
        
        assert "I couldn't find specific information" in explanation
        assert "contact our customer service team" in explanation
