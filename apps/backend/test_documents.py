#!/usr/bin/env python3
"""
Quick test script for document endpoints.

Usage:
    # Get your Supabase token from browser DevTools -> Application -> Local Storage -> supabase.auth.token
    # Or login via the frontend and copy the access_token from the JWT
    
    python test_documents.py
    
    # Or with environment variable:
    export SUPABASE_ACCESS_TOKEN="your_token_here"
    python test_documents.py
"""

import os
import requests
import json
from typing import Optional

# Configuration
BASE_URL = os.getenv("API_URL", "http://localhost:8000/api/v1")
AUTH_TOKEN = os.getenv("SUPABASE_ACCESS_TOKEN")


def print_header(text: str):
    """Print formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_section(text: str):
    """Print formatted section."""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print("─"*70)


def make_request(method: str, endpoint: str, params: dict = None, show_response: bool = True):
    """Make HTTP request and print results."""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"\n🔹 {method} {url}")
    if params:
        print(f"   Query params: {params}")
    
    try:
        response = requests.request(
            method=method,
            url=url,
            headers=headers,
            params=params
        )
        
        status_icon = "✅" if 200 <= response.status_code < 300 else "❌"
        print(f"{status_icon} Status: {response.status_code}")
        
        if show_response and response.status_code < 500:
            try:
                data = response.json()
                print(f"   Response: {json.dumps(data, indent=2)[:500]}...")
                return data
            except:
                print(f"   Response: {response.text[:200]}")
                return response.text
        
        return None
        
    except requests.exceptions.ConnectionError:
        print("❌ Connection failed - is the backend running?")
        print(f"   Expected URL: {BASE_URL}")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def test_list_documents():
    """Test listing all documents."""
    print_section("Test 1: List All Documents")
    return make_request("GET", "/documents")


def test_list_by_type():
    """Test listing documents by type."""
    print_section("Test 2: List Documents by Type")
    
    types = ["flight", "hotel", "visa", "itinerary"]
    results = {}
    
    for doc_type in types:
        print(f"\n  📄 Testing type: {doc_type}")
        result = make_request("GET", "/documents", params={"type": doc_type}, show_response=False)
        if result and isinstance(result, dict):
            count = len(result.get("documents", []))
            print(f"     Found {count} {doc_type} document(s)")
            results[doc_type] = count
        else:
            results[doc_type] = 0
    
    return results


def test_pagination():
    """Test pagination."""
    print_section("Test 3: Test Pagination")
    
    # First page
    print("\n  Page 1 (limit=2, offset=0):")
    page1 = make_request("GET", "/documents", params={"limit": 2, "offset": 0}, show_response=False)
    
    if page1 and isinstance(page1, dict):
        docs1 = page1.get("documents", [])
        print(f"     Found {len(docs1)} documents")
        
        # Second page
        print("\n  Page 2 (limit=2, offset=2):")
        page2 = make_request("GET", "/documents", params={"limit": 2, "offset": 2}, show_response=False)
        if page2 and isinstance(page2, dict):
            docs2 = page2.get("documents", [])
            print(f"     Found {len(docs2)} documents")
            
            # Check if different
            if docs1 and docs2:
                if docs1[0]["id"] != docs2[0]["id"]:
                    print("     ✅ Pagination working correctly")
                else:
                    print("     ⚠️  Same documents returned (might be all documents)")
    
    return page1, page2


def test_get_document():
    """Test getting a specific document."""
    print_section("Test 4: Get Specific Document")
    
    # First, get list to find a document ID
    print("\n  Fetching document list to get an ID...")
    list_result = make_request("GET", "/documents", show_response=False)
    
    if list_result and isinstance(list_result, dict):
        documents = list_result.get("documents", [])
        if documents:
            doc_id = documents[0]["id"]
            doc_type = documents[0]["type"]
            print(f"\n  Using document ID: {doc_id} (type: {doc_type})")
            
            result = make_request("GET", f"/documents/{doc_id}")
            return result
        else:
            print("  ⚠️  No documents found to test with")
            return None
    else:
        print("  ❌ Could not fetch document list")
        return None


def test_download_file():
    """Test downloading a document file."""
    print_section("Test 5: Download Document File")
    
    # First, get list to find a document ID
    print("\n  Fetching document list to get an ID...")
    list_result = make_request("GET", "/documents", show_response=False)
    
    if list_result and isinstance(list_result, dict):
        documents = list_result.get("documents", [])
        if documents:
            doc_id = documents[0]["id"]
            print(f"\n  Attempting to download file for document: {doc_id}")
            
            url = f"{BASE_URL}/documents/{doc_id}/file"
            headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
            
            try:
                response = requests.get(url, headers=headers, stream=True)
                print(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    content_type = response.headers.get("Content-Type", "unknown")
                    content_length = response.headers.get("Content-Length", "unknown")
                    print(f"  ✅ File download successful")
                    print(f"     Content-Type: {content_type}")
                    print(f"     Content-Length: {content_length} bytes")
                    return True
                else:
                    try:
                        error = response.json().get("detail", "Unknown error")
                        print(f"  ❌ Download failed: {error}")
                    except:
                        print(f"  ❌ Download failed: {response.text[:200]}")
                    return False
            except Exception as e:
                print(f"  ❌ Error: {str(e)}")
                return False
        else:
            print("  ⚠️  No documents found to test with")
            return None
    else:
        print("  ❌ Could not fetch document list")
        return None


def test_error_cases():
    """Test error cases."""
    print_section("Test 6: Error Cases")
    
    # Invalid document type
    print("\n  Testing invalid document type:")
    result = make_request("GET", "/documents", params={"type": "invalid_type"}, show_response=False)
    if result is None or (isinstance(result, dict) and "detail" in result):
        print("     ✅ Correctly rejected invalid type")
    
    # Invalid document ID
    print("\n  Testing invalid document ID:")
    fake_id = "00000000-0000-0000-0000-000000000000"
    result = make_request("GET", f"/documents/{fake_id}", show_response=False)
    if result is None or (isinstance(result, dict) and "detail" in result):
        print("     ✅ Correctly returned 404 for invalid ID")
    
    # Unauthorized (no token)
    print("\n  Testing unauthorized access (should fail):")
    url = f"{BASE_URL}/documents"
    try:
        response = requests.get(url, headers={"Content-Type": "application/json"})
        if response.status_code == 401:
            print("     ✅ Correctly rejected unauthorized access")
        else:
            print(f"     ⚠️  Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"     Error: {str(e)}")


def main():
    """Run all tests."""
    print_header("DOCUMENT ENDPOINTS TEST SUITE")
    
    print(f"\n📍 Configuration:")
    print(f"   Base URL: {BASE_URL}")
    
    if not AUTH_TOKEN:
        print(f"   Auth Token: ❌ NOT SET")
        print(f"\n⚠️  To run tests, set SUPABASE_ACCESS_TOKEN environment variable:")
        print(f"   export SUPABASE_ACCESS_TOKEN='your_token_here'")
        print(f"\n   Or get token from browser DevTools after logging in:")
        print(f"   Application -> Local Storage -> supabase.auth.token")
        return
    else:
        print(f"   Auth Token: ✅ Set (length: {len(AUTH_TOKEN)})")
    
    # Run tests
    test_list_documents()
    test_list_by_type()
    test_pagination()
    test_get_document()
    test_download_file()
    test_error_cases()
    
    print_header("TESTING COMPLETE")
    print("\n💡 Tips:")
    print("   - Check backend logs for detailed error messages")
    print("   - Verify documents exist in database before testing")
    print("   - Use browser DevTools Network tab to inspect requests")


if __name__ == "__main__":
    main()

