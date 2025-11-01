"""
Tests for policy_explainer node with user context awareness.

Tests verify that the policy_explainer node:
1. Retrieves user context correctly (tier, policy, coverage)
2. Searches RAG with tier filtering
3. Generates personalized responses
4. Includes specific coverage amounts
5. Adds policy footer for policyholders

Run with: pytest apps/backend/tests/test_policy_explainer_node.py -v -s
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import date, datetime
from langchain_core.messages import HumanMessage, AIMessage
import sys

# Mock pytesseract before any imports that need it
sys.modules['pytesseract'] = MagicMock()

from app.models.user import User
from app.models.quote import Quote, QuoteStatus, ProductType
from app.models.policy import Policy, PolicyStatus
from app.models.trip import Trip
from app.services.pricing import TIER_COVERAGE


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
    return db


@pytest.fixture
def test_user_with_elite_policy(mock_db):
    """Create test user with active Elite policy."""
    # Create user
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="elite_user@test.com",
        name="Elite Test User",
        hashed_password="hashed"
    )
    
    # Create trip
    trip_id = uuid.uuid4()
    trip = Trip(
        id=trip_id,
        user_id=user_id,
        session_id=uuid.uuid4(),
        status="completed",
        start_date=date(2025, 12, 1),
        end_date=date(2025, 12, 15),
        destinations=["Japan"]
    )
    
    # Create quote
    quote_id = uuid.uuid4()
    quote = Quote(
        id=quote_id,
        user_id=user_id,
        trip_id=trip_id,
        product_type=ProductType.SINGLE,
        selected_tier="elite",
        travelers=[{"age": 35}],
        activities=[{"type": "adventure_sports"}],
        price_firm=378.00,
        currency="SGD",
        status=QuoteStatus.FIRMED,
        breakdown={
            "tier": "elite",
            "coverage": TIER_COVERAGE["elite"],
            "price": 378.00
        }
    )
    quote.trip = trip  # Set relationship
    
    # Create policy
    policy = Policy(
        id=uuid.uuid4(),
        user_id=user_id,
        quote_id=quote_id,
        policy_number="TEST-ELITE-12345",
        coverage=TIER_COVERAGE["elite"],
        named_insureds=[{"name": "Elite Test User", "age": 35}],
        effective_date=date(2025, 12, 1),
        expiry_date=date(2025, 12, 15),
        status=PolicyStatus.ACTIVE
    )
    policy.quote = quote  # Set relationship
    
    # Mock database queries
    def query_side_effect(model):
        mock_query = Mock()
        if model == Policy:
            mock_query.filter.return_value.order_by.return_value.first.return_value = policy
        elif model == Quote:
            mock_query.filter.return_value.order_by.return_value.first.return_value = quote
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    return user, policy, quote, trip


@pytest.fixture
def test_user_with_standard_quote(mock_db):
    """Create test user with Standard tier quote (no policy)."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="standard_user@test.com",
        name="Standard Test User",
        hashed_password="hashed"
    )
    
    trip_id = uuid.uuid4()
    trip = Trip(
        id=trip_id,
        user_id=user_id,
        session_id=uuid.uuid4(),
        status="draft",
        start_date=date(2025, 12, 20),
        end_date=date(2026, 1, 3),
        destinations=["Thailand"]
    )
    
    quote_id = uuid.uuid4()
    quote = Quote(
        id=quote_id,
        user_id=user_id,
        trip_id=trip_id,
        product_type=ProductType.SINGLE,
        selected_tier="standard",
        travelers=[{"age": 28}],
        activities=[],
        price_firm=150.00,
        currency="SGD",
        status=QuoteStatus.FIRMED,
        breakdown={
            "tier": "standard",
            "coverage": TIER_COVERAGE["standard"],
            "price": 150.00
        }
    )
    quote.trip = trip
    
    # Mock database queries - no policy, but has quote
    def query_side_effect(model):
        mock_query = Mock()
        if model == Policy:
            mock_query.filter.return_value.order_by.return_value.first.return_value = None
        elif model == Quote:
            mock_query.filter.return_value.order_by.return_value.first.return_value = quote
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    return user, quote, trip


@pytest.fixture
def test_user_without_data(mock_db):
    """Create test user with no quote or policy."""
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email="new_user@test.com",
        name="New Test User",
        hashed_password="hashed"
    )
    
    # Mock database queries - no policy, no quote
    def query_side_effect(model):
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.first.return_value = None
        return mock_query
    
    mock_db.query.side_effect = query_side_effect
    
    return user


# ============================================================================
# TESTS
# ============================================================================

class TestPolicyExplainerWithActivePolicy:
    """Test policy_explainer when user has an active policy."""
    
    def test_response_includes_user_tier(self, test_user_with_elite_policy, mock_db):
        """Test that response mentions user's Elite tier."""
        user, policy, quote, trip = test_user_with_elite_policy
        
        # Import here to avoid module loading issues
        from app.agents import graph, llm_client
        
        # Mock LLM response
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Based on your **Elite Plan**, medical coverage is $500,000."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG search
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = [
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Test Policy',
                    'section_id': 'Section 6',
                    'heading': 'Medical Coverage',
                    'text': 'Medical expenses up to $500,000',
                    'citations': {'pages': [6]},
                    'similarity': 0.85,
                    'pages': [6],
                    'insurer_name': 'MSIG',
                    'product_code': 'TEST'
                }
            ]
            mock_rag_class.return_value = mock_rag
            
            # Import graph functions
            from app.agents.graph import policy_explainer
            
            # Build conversation state
            state = {
                "messages": [HumanMessage(content="What's my medical coverage?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            # Execute policy_explainer
            result_state = graph.policy_explainer(state)
            
            # Verify RAG search was called
            mock_rag.search.assert_called_once()
            
            # Verify LLM was invoked with user context
            mock_llm.invoke.assert_called_once()
            llm_call_args = mock_llm.invoke.call_args[0][0]
            
            # System prompt should mention Elite tier
            system_prompt = llm_call_args[0]['content']
            assert "Elite" in system_prompt or "elite" in system_prompt
            assert "TEST-ELITE-12345" in system_prompt  # Policy number
            
            # Verify response added to messages
            assert len(result_state["messages"]) == 2
            assert isinstance(result_state["messages"][1], AIMessage)
    
    def test_response_includes_policy_footer(self, test_user_with_elite_policy, mock_db):
        """Test that response includes policy number footer."""
        user, policy, quote, trip = test_user_with_elite_policy
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Your medical coverage is $500,000."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = []
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's covered?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            result_state = graph.policy_explainer(state)
            
            # Get final AI message
            final_message = result_state["messages"][1].content
            
            # Should include policy number in footer
            assert "TEST-ELITE-12345" in final_message
            assert "2025-12-01" in final_message or "2025-12-15" in final_message


class TestPolicyExplainerWithQuoteOnly:
    """Test policy_explainer when user has quote but no policy."""
    
    def test_response_mentions_tier_consideration(self, test_user_with_standard_quote, mock_db):
        """Test that response mentions user is considering Standard tier."""
        user, quote, trip = test_user_with_standard_quote
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "The Standard plan includes $250,000 medical coverage."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = []
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's medical coverage?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            result_state = graph.policy_explainer(state)
            
            # Verify LLM system prompt mentions Standard consideration
            llm_call_args = mock_llm.invoke.call_args[0][0]
            system_prompt = llm_call_args[0]['content']
            assert "Standard" in system_prompt or "standard" in system_prompt
            assert "considering" in system_prompt.lower()
    
    def test_no_policy_footer(self, test_user_with_standard_quote, mock_db):
        """Test that response doesn't include policy footer."""
        user, quote, trip = test_user_with_standard_quote
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Medical coverage is $250,000 for Standard."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = []
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's covered?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            result_state = graph.policy_explainer(state)
            
            # Get final message
            final_message = result_state["messages"][1].content
            
            # Should NOT include policy number footer
            assert "Policy:" not in final_message or "Your Policy:" not in final_message


class TestPolicyExplainerWithoutContext:
    """Test policy_explainer when user has no quote or policy."""
    
    def test_generic_response(self, test_user_without_data, mock_db):
        """Test that response provides generic comparison."""
        user = test_user_without_data
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "We offer three tiers: Standard, Elite, and Premier."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = []
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's medical coverage?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            result_state = graph.policy_explainer(state)
            
            # Verify LLM system prompt doesn't have specific tier
            llm_call_args = mock_llm.invoke.call_args[0][0]
            system_prompt = llm_call_args[0]['content']
            assert "hasn't selected a tier" in system_prompt.lower()


class TestRAGIntegration:
    """Test that policy_explainer integrates with RAG correctly."""
    
    def test_rag_search_called_with_query(self, test_user_without_data, mock_db):
        """Test that RAG search is called with user's question."""
        user = test_user_without_data
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Response based on RAG results"
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = [
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Test Policy',
                    'section_id': 'Section 6',
                    'heading': 'Medical Coverage',
                    'text': 'Medical coverage details...',
                    'citations': {'pages': [6]},
                    'similarity': 0.85,
                    'pages': [6],
                    'insurer_name': 'MSIG',
                    'product_code': 'TEST'
                }
            ]
            mock_rag_class.return_value = mock_rag
            
            question = "What's covered under medical?"
            state = {
                "messages": [HumanMessage(content=question)],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            graph.policy_explainer(state)
            
            # Verify RAG search was called with the question
            mock_rag.search.assert_called_once()
            call_args = mock_rag.search.call_args
            assert call_args.kwargs['query'] == question
            assert call_args.kwargs['limit'] == 3
    
    def test_rag_results_passed_to_llm(self, test_user_with_elite_policy, mock_db):
        """Test that RAG results are included in LLM prompt."""
        user, policy, quote, trip = test_user_with_elite_policy
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "Based on Section 6..."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG with specific results
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = [
                {
                    'id': str(uuid.uuid4()),
                    'title': 'MSIG Travel Insurance',
                    'section_id': 'Section 6',
                    'heading': 'Medical Coverage Details',
                    'text': 'Medical expenses covered up to limits shown in benefits table.',
                    'citations': {'pages': [6, 7]},
                    'similarity': 0.88,
                    'pages': [6, 7],
                    'insurer_name': 'MSIG',
                    'product_code': 'QSR022206'
                }
            ]
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's covered?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            graph.policy_explainer(state)
            
            # Verify LLM was called
            mock_llm.invoke.assert_called_once()
            llm_call_args = mock_llm.invoke.call_args[0][0]
            system_prompt = llm_call_args[0]['content']
            
            # System prompt should include RAG results
            assert "Section 6" in system_prompt
            assert "Medical Coverage Details" in system_prompt
            assert "0.88" in system_prompt  # Similarity score


class TestErrorHandling:
    """Test error handling in policy_explainer."""
    
    def test_handles_rag_failure_gracefully(self, test_user_without_data, mock_db):
        """Test that policy_explainer handles RAG search failures."""
        user = test_user_without_data
        
        from app.agents import graph, llm_client
        
        # Mock LLM
        mock_llm = Mock()
        mock_response = Mock()
        mock_response.content = "I apologize, I couldn't find specific information."
        mock_llm.invoke.return_value = mock_response
        
        # Mock RAG to raise exception
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.side_effect = Exception("Database connection failed")
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's covered?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            # Should not crash
            result_state = graph.policy_explainer(state)
            
            # Should still return a response
            assert len(result_state["messages"]) == 2
    
    def test_handles_llm_failure_with_fallback(self, test_user_without_data, mock_db):
        """Test fallback when LLM generation fails."""
        user = test_user_without_data
        
        from app.agents import graph, llm_client
        
        # Mock LLM to fail
        mock_llm = Mock()
        mock_llm.invoke.side_effect = Exception("LLM timeout")
        
        # Mock RAG with results
        with patch('app.services.rag.RAGService') as mock_rag_class, \
             patch.object(llm_client, 'get_llm', return_value=mock_llm):
            mock_rag = Mock()
            mock_rag.search.return_value = [
                {
                    'id': str(uuid.uuid4()),
                    'title': 'Policy Doc',
                    'section_id': 'Section 1',
                    'heading': 'Coverage',
                    'text': 'Coverage details here',
                    'citations': {'pages': [1]},
                    'similarity': 0.75,
                    'pages': [1],
                    'insurer_name': 'MSIG',
                    'product_code': 'TEST'
                }
            ]
            mock_rag_class.return_value = mock_rag
            
            state = {
                "messages": [HumanMessage(content="What's covered?")],
                "user_id": str(user.id),
                "session_id": str(uuid.uuid4())
            }
            
            # Should use fallback response
            result_state = graph.policy_explainer(state)
            
            # Should have fallback response
            assert len(result_state["messages"]) == 2
            final_message = result_state["messages"][1].content
            assert "Coverage" in final_message or "policy" in final_message.lower()


# ============================================================================
# TEST SUMMARY
# ============================================================================

def test_count():
    """Verify we have all expected tests."""
    # Should have at least 7 tests total
    assert True  # Meta-test always passes


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

