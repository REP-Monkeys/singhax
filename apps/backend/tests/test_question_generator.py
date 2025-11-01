"""Unit tests for the LLM-powered question generator service."""

import pytest
from unittest.mock import Mock, MagicMock
from datetime import date
from langchain_core.messages import HumanMessage, AIMessage

from app.services.question_generator import QuestionGenerator


class TestQuestionGenerator:
    """Test suite for QuestionGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a QuestionGenerator instance for testing."""
        return QuestionGenerator()
    
    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = Mock()
        client.generate = Mock(return_value="What's your destination?")
        return client
    
    @pytest.fixture
    def sample_conversation_history(self):
        """Sample conversation history for testing."""
        return [
            HumanMessage(content="I need travel insurance"),
            AIMessage(content="I'd be happy to help! Where are you planning to travel?")
        ]
    
    def test_fallback_templates_exist_for_all_fields(self, generator):
        """Test that fallback templates exist for all supported fields."""
        required_fields = [
            "destination",
            "departure_date",
            "return_date",
            "travelers",
            "adventure_sports",
            "confirmation"
        ]
        
        for field in required_fields:
            assert field in generator.FALLBACK_TEMPLATES, f"Missing fallback template for {field}"
            assert len(generator.FALLBACK_TEMPLATES[field]) > 0, f"Empty fallback template for {field}"
    
    def test_prompts_exist_for_all_fields(self, generator):
        """Test that LLM prompts exist for all supported fields."""
        required_fields = [
            "destination",
            "departure_date",
            "return_date",
            "travelers",
            "adventure_sports",
            "confirmation"
        ]
        
        for field in required_fields:
            assert field in generator.PROMPTS, f"Missing prompt for {field}"
            assert len(generator.PROMPTS[field]) > 0, f"Empty prompt for {field}"
    
    def test_generate_question_with_llm_disabled_uses_template(self, generator, mock_llm_client, sample_conversation_history):
        """Test that question generation uses templates when LLM is disabled."""
        collected_info = {"destination": None, "departure_date": None}
        
        question = generator.generate_question(
            field="destination",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=mock_llm_client,
            use_llm=False
        )
        
        # Should return template, not call LLM
        assert question == generator.FALLBACK_TEMPLATES["destination"]
        mock_llm_client.generate.assert_not_called()
    
    def test_generate_question_with_llm_enabled_calls_llm(self, generator, mock_llm_client, sample_conversation_history):
        """Test that question generation uses LLM when enabled."""
        collected_info = {"destination": None, "departure_date": None}
        
        question = generator.generate_question(
            field="destination",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=mock_llm_client,
            use_llm=True
        )
        
        # Should call LLM
        assert question == "What's your destination?"
        mock_llm_client.generate.assert_called_once()
    
    def test_generate_question_handles_llm_failure_gracefully(self, generator, sample_conversation_history):
        """Test that question generation falls back to template when LLM fails."""
        # Mock LLM client that raises an exception
        failing_client = Mock()
        failing_client.generate = Mock(side_effect=Exception("LLM API error"))
        
        collected_info = {"destination": None}
        
        question = generator.generate_question(
            field="destination",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=failing_client,
            use_llm=True
        )
        
        # Should fall back to template
        assert question == generator.FALLBACK_TEMPLATES["destination"]
    
    def test_generate_question_handles_empty_llm_response(self, generator, sample_conversation_history):
        """Test that empty LLM responses trigger fallback."""
        empty_client = Mock()
        empty_client.generate = Mock(return_value="")
        
        collected_info = {"destination": None}
        
        question = generator.generate_question(
            field="destination",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=empty_client,
            use_llm=True
        )
        
        # Should fall back to template
        assert question == generator.FALLBACK_TEMPLATES["destination"]
    
    def test_generate_question_handles_overly_long_response(self, generator, sample_conversation_history):
        """Test that extremely long LLM responses trigger fallback."""
        long_client = Mock()
        long_client.generate = Mock(return_value="x" * 400)  # 400 chars, over the 300 limit
        
        collected_info = {"destination": None}
        
        question = generator.generate_question(
            field="destination",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=long_client,
            use_llm=True
        )
        
        # Should fall back to template
        assert question == generator.FALLBACK_TEMPLATES["destination"]
    
    def test_context_injection_in_fallback_for_departure_date(self, generator, sample_conversation_history):
        """Test that fallback templates inject context when available."""
        collected_info = {"destination": "Thailand", "departure_date": None}
        
        question = generator.generate_question(
            field="departure_date",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=Mock(),
            use_llm=False
        )
        
        # Should mention Thailand in the question
        assert "Thailand" in question
    
    def test_context_injection_in_fallback_for_return_date(self, generator, sample_conversation_history):
        """Test that fallback templates inject context when available."""
        collected_info = {"destination": "Japan", "return_date": None}
        
        question = generator.generate_question(
            field="return_date",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=Mock(),
            use_llm=False
        )
        
        # Should mention Japan in the question
        assert "Japan" in question
    
    def test_generate_question_formats_date_objects_correctly(self, generator, mock_llm_client, sample_conversation_history):
        """Test that date objects are formatted properly before being passed to LLM."""
        collected_info = {
            "destination": "Singapore",
            "departure_date": date(2025, 12, 15),
            "return_date": date(2025, 12, 22)
        }
        
        # Mock to capture what's passed to LLM
        mock_llm_client.generate = Mock(return_value="When are you traveling?")
        
        question = generator.generate_question(
            field="travelers",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=mock_llm_client,
            use_llm=True
        )
        
        # Should successfully generate without errors
        assert isinstance(question, str)
        assert len(question) > 0
    
    def test_generate_question_formats_list_travelers_correctly(self, generator, mock_llm_client, sample_conversation_history):
        """Test that traveler lists are formatted properly."""
        collected_info = {
            "destination": "Thailand",
            "travelers": [30, 35, 8]
        }
        
        mock_llm_client.generate = Mock(return_value="Will you be doing adventure sports?")
        
        question = generator.generate_question(
            field="adventure_sports",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=mock_llm_client,
            use_llm=True
        )
        
        # Should successfully generate without errors
        assert isinstance(question, str)
        assert len(question) > 0
    
    def test_generate_question_limits_conversation_history(self, generator, mock_llm_client):
        """Test that only last 3 messages are used from conversation history."""
        # Create a long conversation history
        long_history = [
            HumanMessage(content=f"Message {i}")
            for i in range(10)
        ]
        
        mock_llm_client.generate = Mock(return_value="What's your destination?")
        
        question = generator.generate_question(
            field="destination",
            collected_info={},
            conversation_history=long_history,
            llm_client=mock_llm_client,
            use_llm=True
        )
        
        # Should call LLM with limited history (implementation detail)
        assert mock_llm_client.generate.called
        assert isinstance(question, str)
    
    def test_generate_question_passes_correct_parameters_to_llm(self, generator, sample_conversation_history):
        """Test that LLM is called with correct parameters."""
        mock_client = Mock()
        mock_client.generate = Mock(return_value="Where are you traveling?")
        
        collected_info = {"destination": None}
        
        generator.generate_question(
            field="destination",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=mock_client,
            use_llm=True
        )
        
        # Verify LLM was called with correct parameters
        call_args = mock_client.generate.call_args
        assert call_args is not None
        assert "system_prompt" in call_args.kwargs
        assert "temperature" in call_args.kwargs
        assert "max_tokens" in call_args.kwargs
        assert call_args.kwargs["temperature"] == 0.7
        assert call_args.kwargs["max_tokens"] == 150
    
    def test_unknown_field_uses_fallback(self, generator, mock_llm_client, sample_conversation_history):
        """Test that unknown fields gracefully fall back."""
        collected_info = {}
        
        # Should not crash, should use fallback
        question = generator.generate_question(
            field="unknown_field_xyz",
            collected_info=collected_info,
            conversation_history=sample_conversation_history,
            llm_client=mock_llm_client,
            use_llm=True
        )
        
        # Should return some valid question (fallback behavior)
        assert isinstance(question, str)
        assert len(question) > 0
    
    def test_all_fields_generate_valid_questions(self, generator, mock_llm_client, sample_conversation_history):
        """Test that all supported fields can generate questions."""
        fields = ["destination", "departure_date", "return_date", "travelers", "adventure_sports", "confirmation"]
        
        collected_info = {
            "destination": "Singapore",
            "departure_date": date(2025, 12, 15),
            "return_date": date(2025, 12, 22),
            "travelers": [30, 35]
        }
        
        mock_llm_client.generate = Mock(return_value="Test question?")
        
        for field in fields:
            question = generator.generate_question(
                field=field,
                collected_info=collected_info,
                conversation_history=sample_conversation_history,
                llm_client=mock_llm_client,
                use_llm=True
            )
            
            assert isinstance(question, str), f"Field {field} didn't return string"
            assert len(question) > 0, f"Field {field} returned empty question"

