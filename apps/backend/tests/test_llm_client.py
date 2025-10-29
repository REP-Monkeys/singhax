"""Tests for LLM client."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from app.agents.llm_client import LLMClient, get_llm_client, is_llm_available


class TestLLMClient:
    """Test cases for LLM client."""
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_init_groq_provider(self, mock_groq, mock_settings):
        """Test initialization with Groq provider."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.model_name = "llama3-8b-8192"
        
        client = LLMClient(provider="groq")
        
        assert client.provider == "groq"
        assert client.model == "llama3-8b-8192"
        mock_groq.assert_called_once()
    
    @patch('app.agents.llm_client.settings')
    def test_init_groq_no_key(self, mock_settings):
        """Test initialization fails without API key."""
        mock_settings.groq_api_key = None
        
        with pytest.raises(ValueError, match="GROQ_API_KEY not set"):
            LLMClient(provider="groq")
    
    @patch('app.agents.llm_client.OpenAI')
    def test_init_openai_provider(self, mock_openai):
        """Test initialization with OpenAI provider."""
        client = LLMClient(provider="openai")
        
        assert client.provider == "openai"
        mock_openai.assert_called_once()
    
    def test_init_invalid_provider(self):
        """Test initialization with invalid provider."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            LLMClient(provider="invalid")
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_generate_simple(self, mock_groq, mock_settings):
        """Test simple text generation."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.model_name = "llama3-8b-8192"
        
        # Mock response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is a test response"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        result = client.generate("Test prompt")
        
        assert result == "This is a test response"
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_generate_with_system_prompt(self, mock_groq, mock_settings):
        """Test generation with system prompt."""
        mock_settings.groq_api_key = "test-key"
        mock_settings.model_name = "llama3-8b-8192"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        result = client.generate(
            "User prompt",
            system_prompt="You are a helpful assistant"
        )
        
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs['messages']
        
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "You are a helpful assistant"
        assert messages[1]["role"] == "user"
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_generate_error_handling(self, mock_groq, mock_settings):
        """Test error handling in generation."""
        mock_settings.groq_api_key = "test-key"
        
        mock_client = Mock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        result = client.generate("Test")
        
        assert "having trouble" in result.lower()
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_generate_with_history(self, mock_groq, mock_settings):
        """Test generation with conversation history."""
        mock_settings.groq_api_key = "test-key"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Response with history"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"}
        ]
        
        result = client.generate_with_history(messages)
        
        assert result == "Response with history"
        call_args = mock_client.chat.completions.create.call_args
        assert call_args.kwargs['messages'] == messages
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_detect_intent(self, mock_groq, mock_settings):
        """Test intent detection."""
        mock_settings.groq_api_key = "test-key"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "quote"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        result = client.detect_intent(
            "I need travel insurance",
            ["quote", "claim", "policy"]
        )
        
        assert "intent" in result
        assert "confidence" in result
        assert result["intent"] == "quote"
        assert 0 <= result["confidence"] <= 1
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_extract_information(self, mock_groq, mock_settings):
        """Test information extraction."""
        mock_settings.groq_api_key = "test-key"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = '{"destination": "France", "dates": "March 15-22"}'
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        result = client.extract_information(
            "I'm traveling to France from March 15 to 22",
            ["destination", "dates"]
        )
        
        assert "destination" in result
        assert result["destination"] == "France"
    
    @patch('app.agents.llm_client.settings')
    @patch('app.agents.llm_client.Groq')
    def test_extract_information_invalid_json(self, mock_groq, mock_settings):
        """Test information extraction with invalid JSON response."""
        mock_settings.groq_api_key = "test-key"
        
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Invalid JSON"
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_groq.return_value = mock_client
        
        client = LLMClient(provider="groq")
        result = client.extract_information(
            "I'm traveling to France",
            ["destination"]
        )
        
        assert result == {}
    
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
    @patch('app.agents.llm_client.Groq')
    def test_get_llm_client_singleton(self, mock_groq, mock_settings):
        """Test get_llm_client returns singleton."""
        mock_settings.groq_api_key = "test-key"
        
        # Reset global client
        import app.agents.llm_client as llm_module
        llm_module._llm_client = None
        
        client1 = get_llm_client()
        client2 = get_llm_client()
        
        # Should create only once
        assert mock_groq.call_count == 1



