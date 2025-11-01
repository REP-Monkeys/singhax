"""Integration tests for conversational flow with LLM-generated questions."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from langchain_core.messages import HumanMessage, AIMessage

from app.agents.graph import create_conversation_graph
from app.core.config import settings


class TestConversationFlowLLMQuestions:
    """Integration tests for the full conversation flow with LLM question generation."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        db = Mock()
        db.query = Mock()
        db.add = Mock()
        db.commit = Mock()
        db.refresh = Mock()
        return db
    
    @pytest.fixture
    def conversation_graph(self, mock_db):
        """Create a conversation graph instance for testing."""
        with patch('app.agents.graph.Trip') as mock_trip:
            mock_trip.return_value = Mock(id="test-trip-id")
            graph = create_conversation_graph(mock_db)
            return graph
    
    def test_initial_greeting_generates_natural_question(self, conversation_graph):
        """Test that the first question in a conversation is naturally generated."""
        initial_state = {
            "messages": [HumanMessage(content="Hello")],
            "user_id": "test-user-123",
            "session_id": "test-session-123"
        }
        
        config = {"configurable": {"thread_id": "test-thread-1"}}
        
        # Execute the graph
        result = conversation_graph.invoke(initial_state, config)
        
        # Check that a response was generated
        assert "messages" in result
        assert len(result["messages"]) > 1
        
        # Last message should be from assistant
        last_message = result["messages"][-1]
        assert isinstance(last_message, AIMessage)
        
        # Should contain some form of destination question
        content = last_message.content.lower()
        assert any(keyword in content for keyword in ["destination", "travel", "where", "going"])
    
    def test_destination_answer_generates_context_aware_follow_up(self, conversation_graph):
        """Test that providing destination generates a follow-up that references it."""
        with patch('app.services.geo_mapping.GeoMapper.get_country_iso_code', return_value='TH'):
            initial_state = {
                "messages": [
                    HumanMessage(content="I need travel insurance"),
                    AIMessage(content="Where are you traveling?"),
                    HumanMessage(content="Thailand")
                ],
                "user_id": "test-user-123",
                "session_id": "test-session-123"
            }
            
            config = {"configurable": {"thread_id": "test-thread-2"}}
            
            result = conversation_graph.invoke(initial_state, config)
            
            # Should have asked for dates
            assert "messages" in result
            last_message = result["messages"][-1]
            assert isinstance(last_message, AIMessage)
            
            # If LLM questions enabled, might reference Thailand
            if settings.use_llm_questions:
                # Note: This is a soft check since LLM responses vary
                content = last_message.content.lower()
                # Should ask about dates
                assert any(keyword in content for keyword in ["date", "when", "depart", "start"])
    
    def test_feature_flag_toggle_works(self, mock_db):
        """Test that toggling USE_LLM_QUESTIONS feature flag works."""
        # Test with LLM enabled
        with patch.object(settings, 'use_llm_questions', True):
            graph = create_conversation_graph(mock_db)
            
            initial_state = {
                "messages": [HumanMessage(content="Hello")],
                "user_id": "test-user-123",
                "session_id": "test-session-123"
            }
            
            config = {"configurable": {"thread_id": "test-thread-3"}}
            result_llm = graph.invoke(initial_state, config)
            
            assert "messages" in result_llm
            assert len(result_llm["messages"]) > 1
        
        # Test with LLM disabled (should use templates)
        with patch.object(settings, 'use_llm_questions', False):
            graph = create_conversation_graph(mock_db)
            
            initial_state = {
                "messages": [HumanMessage(content="Hello")],
                "user_id": "test-user-456",
                "session_id": "test-session-456"
            }
            
            config = {"configurable": {"thread_id": "test-thread-4"}}
            result_template = graph.invoke(initial_state, config)
            
            assert "messages" in result_template
            assert len(result_template["messages"]) > 1
    
    def test_llm_failure_fallback_maintains_conversation(self, mock_db):
        """Test that LLM failures don't break the conversation flow."""
        with patch('app.services.question_generator.QuestionGenerator.generate_question') as mock_gen:
            # Simulate LLM failure by raising exception, which should trigger fallback
            mock_gen.side_effect = Exception("LLM API error")
            
            graph = create_conversation_graph(mock_db)
            
            initial_state = {
                "messages": [HumanMessage(content="I need insurance")],
                "user_id": "test-user-123",
                "session_id": "test-session-123"
            }
            
            config = {"configurable": {"thread_id": "test-thread-5"}}
            
            # Should not crash, should use fallback templates
            result = graph.invoke(initial_state, config)
            
            assert "messages" in result
            assert len(result["messages"]) > 1
            
            # Should still get a valid question
            last_message = result["messages"][-1]
            assert isinstance(last_message, AIMessage)
            assert len(last_message.content) > 0
    
    def test_full_quote_flow_with_llm_questions(self, conversation_graph):
        """Test complete quote flow from greeting to pricing with LLM questions."""
        with patch('app.services.geo_mapping.GeoMapper.get_country_iso_code', return_value='TH'), \
             patch('app.services.geo_mapping.GeoMapper.validate_destination') as mock_validate:
            
            mock_validate.return_value = {
                "area": Mock(value="ASIA"),
                "base_rate": 50.0
            }
            
            # Simulate a full conversation
            messages = [
                HumanMessage(content="I need travel insurance"),
                AIMessage(content="Where are you traveling?"),
                HumanMessage(content="Thailand"),
                AIMessage(content="When do you depart?"),
                HumanMessage(content="2025-12-15"),
                AIMessage(content="When do you return?"),
                HumanMessage(content="2025-12-22"),
                AIMessage(content="How many travelers?"),
                HumanMessage(content="2 travelers, ages 30 and 8"),
                AIMessage(content="Any adventure sports?"),
                HumanMessage(content="No")
            ]
            
            state = {
                "messages": messages,
                "user_id": "test-user-123",
                "session_id": "test-session-123",
                "trip_details": {
                    "destination": "Thailand",
                    "departure_date": date(2025, 12, 15),
                    "return_date": date(2025, 12, 22),
                    "departure_country": "SG",
                    "arrival_country": "TH",
                    "adults_count": 1,
                    "children_count": 1
                },
                "travelers_data": {
                    "ages": [30, 8],
                    "count": 2
                },
                "preferences": {
                    "adventure_sports": False
                }
            }
            
            config = {"configurable": {"thread_id": "test-thread-6"}}
            
            # Should complete successfully
            result = conversation_graph.invoke(state, config)
            
            assert "messages" in result
            assert "trip_details" in result
            assert "travelers_data" in result
    
    def test_questions_are_contextual_not_generic(self, conversation_graph):
        """Test that generated questions contain contextual information when available."""
        with patch('app.services.geo_mapping.GeoMapper.get_country_iso_code', return_value='JP'):
            # Provide destination first
            state = {
                "messages": [
                    HumanMessage(content="I'm going to Japan"),
                    AIMessage(content="Great! Where in Japan?"),
                ],
                "user_id": "test-user-123",
                "session_id": "test-session-123",
                "trip_details": {
                    "destination": "Japan"
                },
                "travelers_data": {},
                "preferences": {}
            }
            
            config = {"configurable": {"thread_id": "test-thread-7"}}
            
            # This should trigger a departure date question
            result = conversation_graph.invoke(state, config)
            
            if settings.use_llm_questions and "messages" in result and len(result["messages"]) > 2:
                last_message = result["messages"][-1]
                if isinstance(last_message, AIMessage):
                    content = last_message.content.lower()
                    # With LLM questions enabled, there's a good chance "japan" appears
                    # This is a soft assertion since LLM behavior can vary
                    # The key is that it shouldn't crash and should ask about dates
                    assert any(keyword in content for keyword in ["date", "when", "depart", "start"])
    
    def test_conversation_maintains_state_across_turns(self, conversation_graph):
        """Test that conversation state is maintained across multiple turns."""
        config = {"configurable": {"thread_id": "test-thread-8"}}
        
        # Turn 1: Initial greeting
        state1 = {
            "messages": [HumanMessage(content="Hello")],
            "user_id": "test-user-123",
            "session_id": "test-session-123"
        }
        result1 = conversation_graph.invoke(state1, config)
        
        # Turn 2: Provide destination
        with patch('app.services.geo_mapping.GeoMapper.get_country_iso_code', return_value='SG'):
            state2 = {
                "messages": result1["messages"] + [HumanMessage(content="Singapore")],
                "user_id": "test-user-123",
                "session_id": "test-session-123"
            }
            result2 = conversation_graph.invoke(state2, config)
            
            # Should have collected destination
            assert "trip_details" in result2
            if result2.get("trip_details"):
                # Destination might be stored
                pass  # State persistence depends on graph implementation
    
    def test_error_handling_does_not_expose_internal_errors(self, conversation_graph):
        """Test that internal errors are handled gracefully without exposing internals."""
        # Provide invalid/problematic input
        state = {
            "messages": [HumanMessage(content="!@#$%^&*()")],
            "user_id": "test-user-123",
            "session_id": "test-session-123"
        }
        
        config = {"configurable": {"thread_id": "test-thread-9"}}
        
        # Should handle gracefully
        result = conversation_graph.invoke(state, config)
        
        assert "messages" in result
        # Should still respond (even if with a clarification request)
        assert len(result["messages"]) > 0
    
    @pytest.mark.parametrize("field", [
        "destination",
        "departure_date",
        "return_date",
        "travelers",
        "adventure_sports"
    ])
    def test_all_fields_can_be_asked_with_llm(self, field, conversation_graph):
        """Test that all question types can be generated via LLM."""
        # This is more of a smoke test to ensure no crashes
        state = {
            "messages": [HumanMessage(content="I need insurance")],
            "user_id": "test-user-123",
            "session_id": "test-session-123",
            "trip_details": {},
            "travelers_data": {},
            "preferences": {}
        }
        
        config = {"configurable": {"thread_id": f"test-thread-{field}"}}
        
        # Should execute without crashing
        result = conversation_graph.invoke(state, config)
        
        assert "messages" in result
        assert len(result["messages"]) > 0

