"""Tests for LLM client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.llm_client import GroqLLMClient, MultiProviderLLMClient, get_llm_client, is_llm_available


class TestGroqLLMClient:
    """Test cases for Groq LLM client."""
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.ChatGroq')
    @patch('app.agents.llm_client.Groq')
    def test_init_groq_client(self, mock_groq, mock_chat_groq, mock_settings):
        """Test initialization of GroqLLMClient."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.groq_model = "llama-3.3-70b-versatile"
        mock_settings.model_name = "llama-3.3-70b-versatile"
        
        client = GroqLLMClient()
        
        assert client.model is not None
        mock_chat_groq.assert_called_once()
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_classify_intent(self, mock_groq, mock_settings):
        """Test intent classification."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.groq_model = "llama-3.3-70b-versatile"
        mock_settings.model_name = "llama-3.3-70b-versatile"
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "quote", "confidence": 0.95, "reasoning": "User wants a quote"}'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = GroqLLMClient()
        result = client.classify_intent("I need travel insurance")
        
        assert "intent" in result
        assert "confidence" in result
        assert result["intent"] == "quote"
        assert 0 <= result["confidence"] <= 1
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_classify_intent_with_history(self, mock_groq, mock_settings):
        """Test intent classification with conversation history."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.groq_model = "llama-3.3-70b-versatile"
        mock_settings.model_name = "llama-3.3-70b-versatile"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"intent": "quote", "confidence": 0.90, "reasoning": "Continuing quote conversation"}'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = GroqLLMClient()
        result = client.classify_intent(
            "How much does it cost?",
            conversation_history=["I need insurance", "Where are you going?"]
        )
        
        assert result["intent"] == "quote"
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_extract_trip_info(self, mock_groq, mock_settings):
        """Test trip information extraction."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.groq_model = "llama-3.3-70b-versatile"
        mock_settings.model_name = "llama-3.3-70b-versatile"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"destination": "France", "departure_date": "2025-03-15", "return_date": "2025-03-22"}'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = GroqLLMClient()
        result = client.extract_trip_info("I'm going to France from March 15 to 22")
        
        assert "destination" in result
        assert result["destination"] == "France"


class TestMultiProviderLLMClient:
    """Test cases for MultiProviderLLMClient."""
    
    @patch('app.agents.llm_client.settings')
    def test_init_with_groq(self, mock_settings):
        """Test initialization with Groq provider."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.openai_api_key = None
        
        client = MultiProviderLLMClient()
        
        assert client.provider == "groq"
    
    @patch('app.agents.llm_client.settings')
    def test_init_with_openai(self, mock_settings):
        """Test initialization with OpenAI provider."""
        mock_settings.groq_api_key = None
        mock_settings.openai_api_key = "test-key"
        
        client = MultiProviderLLMClient()
        
        assert client.provider == "openai"


class TestLLMClientHelpers:
    """Test cases for helper functions."""
    
    @patch('app.agents.llm_client.settings')
    def test_is_llm_available_with_key(self, mock_settings):
        """Test LLM availability check with API key."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.openai_api_key = None
        
        assert is_llm_available() is True
    
    @patch('app.agents.llm_client.settings')
    def test_is_llm_available_without_key(self, mock_settings):
        """Test LLM availability check without API key."""
        mock_settings.groq_api_key = None
        mock_settings.openai_api_key = None
        
        assert is_llm_available() is False
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.MultiProviderLLMClient')
    def test_get_llm_client_singleton(self, mock_client_class, mock_settings):
        """Test get_llm_client returns singleton."""
        mock_settings.groq_api_key = "test-key"
        
        mock_client_instance = Mock()
        mock_client_class.return_value = mock_client_instance
        
        # Reset global client
        import app.agents.llm_client as llm_module
        llm_module._llm_client = None
        
        client1 = get_llm_client()
        client2 = get_llm_client()
        
        # Should be the same instance
        assert client1 is client2
        # Should create only once
        assert mock_client_class.call_count == 1



