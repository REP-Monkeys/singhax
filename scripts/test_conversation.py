#!/usr/bin/env python3
"""Test script for conversation flow.

Usage:
    python scripts/test_conversation.py happy_path
"""

import sys
import uuid
import httpx
import json
from typing import Dict, Any


# API Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/v1"
CHAT_ENDPOINT = f"{BASE_URL}{API_PREFIX}/chat/message"


def send_message(session_id: str, message: str) -> Dict[str, Any]:
    """Send a message to the chat API.

    Args:
        session_id: Session ID for conversation
        message: User message

    Returns:
        Response from the API
    """
    payload = {
        "session_id": session_id,
        "message": message
    }

    try:
        response = httpx.post(CHAT_ENDPOINT, json=payload, timeout=30.0)
        response.raise_for_status()
        return response.json()
    except httpx.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


def print_exchange(user_msg: str, agent_msg: str, exchange_num: int):
    """Print a conversation exchange."""
    print(f"\n{'='*80}")
    print(f"EXCHANGE {exchange_num}")
    print(f"{'='*80}")
    print(f"\n👤 USER: {user_msg}")
    print(f"\n🤖 AGENT: {agent_msg}")


def print_quote(quote_data: Dict[str, Any]):
    """Print quote information."""
    if not quote_data:
        return

    print(f"\n{'='*80}")
    print("💰 QUOTE GENERATED")
    print(f"{'='*80}")

    print(f"\n📍 Destination: {quote_data.get('destination', 'Unknown')}")
    print(f"📅 Duration: {quote_data.get('trip_duration', 0)} days")
    print(f"👥 Travelers: {quote_data.get('travelers_count', 0)}")
    print(f"🎿 Adventure Sports: {'Yes' if quote_data.get('adventure_sports') else 'No'}")

    quotes = quote_data.get('quotes', {})

    if 'standard' in quotes:
        std = quotes['standard']
        print(f"\n🌟 STANDARD PLAN: ${std['price']:.2f} {std['currency']}")
        print(f"   Medical: ${std['coverage']['medical_coverage']:,}")
        print(f"   Cancellation: ${std['coverage']['trip_cancellation']:,}")
        print(f"   Baggage: ${std['coverage']['baggage']:,}")

    if 'elite' in quotes:
        elite = quotes['elite']
        print(f"\n⭐ ELITE PLAN: ${elite['price']:.2f} {elite['currency']}")
        print(f"   Medical: ${elite['coverage']['medical_coverage']:,}")
        print(f"   Cancellation: ${elite['coverage']['trip_cancellation']:,}")
        print(f"   Baggage: ${elite['coverage']['baggage']:,}")
        print(f"   Adventure Sports: Included")

    if 'premier' in quotes:
        premier = quotes['premier']
        print(f"\n💎 PREMIER PLAN: ${premier['price']:.2f} {premier['currency']}")
        print(f"   Medical: ${premier['coverage']['medical_coverage']:,}")
        print(f"   Cancellation: ${premier['coverage']['trip_cancellation']:,}")
        print(f"   Baggage: ${premier['coverage']['baggage']:,}")
        print(f"   Adventure Sports: Full Coverage")


def happy_path_test():
    """Run happy path conversation test.

    Flow:
    1. User: I need travel insurance
    2. Agent: Where are you traveling to?
    3. User: Japan
    4. Agent: When does your trip start?
    5. User: 2024-12-15
    6. Agent: When do you return?
    7. User: 2024-12-22
    8. Agent: How many travelers and ages?
    9. User: 2 travelers: 30 and 28
    10. Agent: Adventure sports?
    11. User: Yes
    12. Agent: Confirmation summary
    13. User: Yes
    14. Agent: 3-tier quote display
    """

    # Generate unique session ID
    session_id = str(uuid.uuid4())

    print(f"\n{'='*80}")
    print("🧪 HAPPY PATH TEST")
    print(f"{'='*80}")
    print(f"\nSession ID: {session_id}")
    print(f"Endpoint: {CHAT_ENDPOINT}")

    # Conversation flow
    exchanges = [
        ("I need travel insurance for a trip", 1),
        ("Japan", 2),
        ("2024-12-15", 3),
        ("2024-12-22", 4),
        ("2 travelers: 30 and 28", 5),
        ("Yes", 6),  # Adventure sports
        ("Yes", 7),  # Confirmation
    ]

    quote_data = None

    for user_msg, exchange_num in exchanges:
        response = send_message(session_id, user_msg)

        agent_msg = response.get('message', 'No response')
        quote_data = response.get('quote')

        print_exchange(user_msg, agent_msg, exchange_num)

        # Print state for debugging
        state = response.get('state', {})
        if state.get('awaiting_field'):
            print(f"\n📝 Awaiting: {state['awaiting_field']}")

        # Stop if we have a quote
        if quote_data:
            break

    # Print final quote
    if quote_data:
        print_quote(quote_data)
        print(f"\n{'='*80}")
        print("✅ TEST PASSED - Quote generated successfully")
        print(f"{'='*80}\n")
    else:
        print(f"\n{'='*80}")
        print("❌ TEST FAILED - No quote generated")
        print(f"{'='*80}\n")
        sys.exit(1)


def no_adventure_sports_test():
    """Test without adventure sports (only Standard plan)."""

    session_id = str(uuid.uuid4())

    print(f"\n{'='*80}")
    print("🧪 NO ADVENTURE SPORTS TEST")
    print(f"{'='*80}")
    print(f"\nSession ID: {session_id}")

    exchanges = [
        ("I need insurance", 1),
        ("Singapore", 2),
        ("2024-11-01", 3),
        ("2024-11-05", 4),
        ("1 traveler: 35", 5),
        ("No", 6),  # No adventure sports
        ("Yes", 7),  # Confirmation
    ]

    quote_data = None

    for user_msg, exchange_num in exchanges:
        response = send_message(session_id, user_msg)
        agent_msg = response.get('message', 'No response')
        quote_data = response.get('quote')

        print_exchange(user_msg, agent_msg, exchange_num)

        if quote_data:
            break

    if quote_data:
        print_quote(quote_data)
        quotes = quote_data.get('quotes', {})

        # Verify only Standard plan exists
        if 'standard' in quotes and 'elite' not in quotes and 'premier' not in quotes:
            print(f"\n✅ TEST PASSED - Only Standard plan generated (no adventure sports)")
        else:
            print(f"\n❌ TEST FAILED - Unexpected quote tiers")
            sys.exit(1)
    else:
        print(f"\n❌ TEST FAILED - No quote generated")
        sys.exit(1)


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_conversation.py <test_name>")
        print("\nAvailable tests:")
        print("  happy_path             - 7-exchange conversation with adventure sports")
        print("  no_adventure_sports    - Conversation without adventure sports")
        sys.exit(1)

    test_name = sys.argv[1]

    if test_name == "happy_path":
        happy_path_test()
    elif test_name == "no_adventure_sports":
        no_adventure_sports_test()
    else:
        print(f"❌ Unknown test: {test_name}")
        sys.exit(1)


if __name__ == "__main__":
    main()
