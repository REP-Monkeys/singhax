"""Quick test script to verify LangGraph is working."""

import requests
import uuid
import json

# Generate valid session ID
session_id = str(uuid.uuid4())

# Test endpoint
url = "http://127.0.0.1:8000/api/v1/chat/message"

payload = {
    "session_id": session_id,
    "message": "I need travel insurance for my trip to France"
}

print(f"Testing LangGraph with session_id: {session_id}")
print(f"Sending message: {payload['message']}")
print("-" * 60)

try:
    response = requests.post(url, json=payload, timeout=30)
    
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ SUCCESS! LangGraph is working!")
        print(f"\nResponse:")
        print(f"  Message: {data.get('message', 'N/A')}")
        print(f"  Intent: {data.get('state', {}).get('current_intent', 'N/A')}")
        print(f"  Requires Human: {data.get('requires_human', False)}")
        if data.get('quote'):
            print(f"  Quote Data: Yes")
    else:
        print(f"\n❌ ERROR: {response.status_code}")
        try:
            error_data = response.json()
            print(f"Error: {error_data.get('detail', 'Unknown error')}")
        except:
            print(f"Response: {response.text}")
            
except requests.exceptions.ConnectionError:
    print("❌ ERROR: Could not connect to server.")
    print("Make sure the server is running on http://127.0.0.1:8000")
except Exception as e:
    print(f"❌ ERROR: {type(e).__name__}: {e}")

