"""
Interactive testing script for chat conversations.

Provides both predefined test scenarios and interactive mode
for manual testing of the chat API endpoints.
"""

import requests
import json
from datetime import datetime
import sys
import os

# Allow overriding via environment variable
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/api/v1")
print(f"Using API base URL: {BASE_URL}\n")


def create_session():
    """Create a new chat session."""
    response = requests.post(f"{BASE_URL}/chat/session", json={})
    response.raise_for_status()
    return response.json()["session_id"]


def send_message(session_id, message):
    """Send a message and get response."""
    response = requests.post(
        f"{BASE_URL}/chat/message",
        json={"session_id": session_id, "message": message}
    )
    response.raise_for_status()
    return response.json()


def print_response(data):
    """Pretty print agent response."""
    print("\n" + "="*60)
    print("AGENT:", data["message"])
    
    if data.get("quote"):
        print("\n--- QUOTE AVAILABLE ---")
        print(json.dumps(data["quote"], indent=2))
    
    print("="*60 + "\n")


def run_test_scenario(scenario_name, messages):
    """Run a predefined test scenario."""
    print(f"\n{'='*60}")
    print(f"Running scenario: {scenario_name}")
    print(f"{'='*60}\n")
    
    session_id = create_session()
    print(f"Session ID: {session_id}\n")
    
    for user_message in messages:
        print(f"USER: {user_message}")
        response = send_message(session_id, user_message)
        print_response(response)
        
        if response.get("requires_human"):
            print("⚠️ Human handoff required")
            break


def interactive_mode():
    """Interactive conversation mode."""
    print("\n" + "="*60)
    print("INTERACTIVE CHAT MODE")
    print("Type 'quit' to exit, 'new' for new session")
    print("="*60 + "\n")
    
    session_id = create_session()
    print(f"Session ID: {session_id}\n")
    
    while True:
        user_input = input("YOU: ").strip()
        
        if user_input.lower() == 'quit':
            break
        elif user_input.lower() == 'new':
            session_id = create_session()
            print(f"\nNew session: {session_id}\n")
            continue
        elif not user_input:
            continue
        
        try:
            response = send_message(session_id, user_input)
            print_response(response)
        except Exception as e:
            print(f"ERROR: {e}\n")


# Test scenarios
SCENARIOS = {
    "happy_path": [
        "I need travel insurance",
        "Japan",
        "2025-12-15",
        "2025-12-22",
        "1 traveler, age 30",
        "No",
        "Yes"
    ],
    
    "all_at_once": [
        "Quote for Thailand Dec 1-14, 2025, 2 adults ages 30 and 35, 1 child age 8, no adventure sports",
        "Yes, that's correct"
    ],
    
    "with_correction": [
        "I need insurance for Japan",
        "December 15 to 22, 2025",
        "2 travelers, ages 30 and 35",
        "No",
        "No, actually it's 3 travelers",
        "Ages 30, 35, and 8",
        "No adventure sports",
        "Yes"
    ],
    
    "policy_questions": [
        "What does travel insurance cover?",
        "What's the difference between standard and premium plans?",
        "How do I file a claim?"
    ],
    
    "claims_guidance": [
        "I need help filing a claim",
        "My luggage was lost",
        "What documents do I need?"
    ]
}


if __name__ == "__main__":
    if len(sys.argv) > 1:
        scenario = sys.argv[1]
        if scenario in SCENARIOS:
            run_test_scenario(scenario, SCENARIOS[scenario])
        elif scenario == "interactive":
            interactive_mode()
        else:
            print(f"Unknown scenario: {scenario}")
            print(f"Available: {', '.join(SCENARIOS.keys())}, interactive")
    else:
        print("Usage: python test_conversation.py [scenario_name|interactive]")
        print(f"Available scenarios: {', '.join(SCENARIOS.keys())}")
        print("\nExamples:")
        print("  python test_conversation.py happy_path")
        print("  python test_conversation.py all_at_once")
        print("  python test_conversation.py interactive")