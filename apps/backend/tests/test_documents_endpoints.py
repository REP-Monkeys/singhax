"""
Comprehensive test script for document handling endpoints.

This script tests all document API endpoints:
1. GET /api/v1/documents - List documents
2. GET /api/v1/documents?type={type} - List filtered documents
3. GET /api/v1/documents/{document_id} - Get document details
4. GET /api/v1/documents/{document_id}/file - Download document file

Usage:
    # Set environment variables or pass token directly
    export SUPABASE_ACCESS_TOKEN="your_token_here"
    python -m pytest tests/test_documents_endpoints.py -v
    
    # Or run directly with requests
    python tests/test_documents_endpoints.py
"""

import os
import sys
import requests
import json
from typing import Optional, Dict, Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings


class DocumentEndpointTester:
    """Test suite for document endpoints."""
    
    def __init__(self, base_url: str = None, auth_token: str = None):
        """
        Initialize tester.
        
        Args:
            base_url: Backend API base URL (defaults to http://localhost:8000/api/v1)
            auth_token: Supabase JWT token (can also be set via SUPABASE_ACCESS_TOKEN env var)
        """
        self.base_url = base_url or os.getenv("API_URL", "http://localhost:8000/api/v1")
        self.auth_token = auth_token or os.getenv("SUPABASE_ACCESS_TOKEN")
        
        if not self.auth_token:
            print("⚠️  Warning: No auth token provided. Tests requiring authentication will fail.")
            print("   Set SUPABASE_ACCESS_TOKEN environment variable or pass token to constructor.")
        
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}" if self.auth_token else None,
            "Content-Type": "application/json"
        }
        
        # Remove None headers
        self.headers = {k: v for k, v in self.headers.items() if v is not None}
        
        self.test_results = []
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request and return response."""
        url = f"{self.base_url}{endpoint}"
        print(f"\n{'='*60}")
        print(f"🌐 {method} {url}")
        if kwargs.get("params"):
            print(f"   Query params: {kwargs['params']}")
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=self.headers,
                **kwargs
            )
            
            status_emoji = "✅" if 200 <= response.status_code < 300 else "❌"
            print(f"{status_emoji} Status: {response.status_code} {response.reason}")
            
            result = {
                "method": method,
                "endpoint": endpoint,
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "response": None,
                "error": None
            }
            
            try:
                result["response"] = response.json()
                if result["success"]:
                    print(f"   Response keys: {list(result['response'].keys())}")
                else:
                    print(f"   Error: {result['response'].get('detail', 'Unknown error')}")
            except:
                result["response"] = response.text[:200]  # First 200 chars
                if not result["success"]:
                    result["error"] = response.text[:200]
                    print(f"   Error: {result['error']}")
            
            return result
            
        except requests.exceptions.ConnectionError:
            error_msg = f"❌ Connection failed - is the backend running at {self.base_url}?"
            print(error_msg)
            return {
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "success": False,
                "error": "ConnectionError - Backend not running"
            }
        except Exception as e:
            error_msg = f"❌ Request failed: {str(e)}"
            print(error_msg)
            return {
                "method": method,
                "endpoint": endpoint,
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
    
    def test_list_all_documents(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents - List all documents."""
        print("\n📋 Test 1: List all documents")
        result = self._make_request("GET", "/documents")
        self.test_results.append(("List all documents", result))
        return result
    
    def test_list_documents_with_pagination(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents with pagination."""
        print("\n📋 Test 2: List documents with pagination")
        result = self._make_request(
            "GET",
            "/documents",
            params={"limit": 10, "offset": 0}
        )
        self.test_results.append(("List documents (paginated)", result))
        return result
    
    def test_list_flight_documents(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents?type=flight."""
        print("\n✈️  Test 3: List flight documents")
        result = self._make_request(
            "GET",
            "/documents",
            params={"type": "flight"}
        )
        self.test_results.append(("List flight documents", result))
        return result
    
    def test_list_hotel_documents(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents?type=hotel."""
        print("\n🏨 Test 4: List hotel documents")
        result = self._make_request(
            "GET",
            "/documents",
            params={"type": "hotel"}
        )
        self.test_results.append(("List hotel documents", result))
        return result
    
    def test_list_visa_documents(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents?type=visa."""
        print("\n🛂 Test 5: List visa documents")
        result = self._make_request(
            "GET",
            "/documents",
            params={"type": "visa"}
        )
        self.test_results.append(("List visa documents", result))
        return result
    
    def test_list_itinerary_documents(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents?type=itinerary."""
        print("\n📅 Test 6: List itinerary documents")
        result = self._make_request(
            "GET",
            "/documents",
            params={"type": "itinerary"}
        )
        self.test_results.append(("List itinerary documents", result))
        return result
    
    def test_list_invalid_type(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents?type=invalid - Should return 400."""
        print("\n❌ Test 7: List documents with invalid type (should fail)")
        result = self._make_request(
            "GET",
            "/documents",
            params={"type": "invalid_type"}
        )
        self.test_results.append(("List invalid type (error case)", result))
        # This should fail with 400
        if result["status_code"] == 400:
            print("   ✅ Correctly rejected invalid document type")
        return result
    
    def test_get_document_by_id(self, document_id: str = None) -> Dict[str, Any]:
        """
        Test GET /api/v1/documents/{document_id}.
        
        Args:
            document_id: Document ID to fetch. If None, tries to get one from list.
        """
        print("\n🔍 Test 8: Get document by ID")
        
        # If no document_id provided, try to get one from listing
        if not document_id:
            list_result = self.test_list_all_documents()
            if list_result["success"] and list_result["response"]:
                documents = list_result["response"].get("documents", [])
                if documents:
                    document_id = documents[0]["id"]
                    print(f"   Using document ID from list: {document_id}")
                else:
                    print("   ⚠️  No documents found to test with")
                    result = {
                        "method": "GET",
                        "endpoint": f"/documents/{document_id}",
                        "status_code": 0,
                        "success": False,
                        "error": "No documents available for testing"
                    }
                    self.test_results.append(("Get document by ID", result))
                    return result
            else:
                print("   ⚠️  Could not fetch document list")
                result = {
                    "method": "GET",
                    "endpoint": f"/documents/{document_id}",
                    "status_code": 0,
                    "success": False,
                    "error": "Could not fetch document list"
                }
                self.test_results.append(("Get document by ID", result))
                return result
        
        result = self._make_request("GET", f"/documents/{document_id}")
        self.test_results.append(("Get document by ID", result))
        return result
    
    def test_get_nonexistent_document(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents/{invalid_id} - Should return 404."""
        print("\n❌ Test 9: Get nonexistent document (should fail)")
        fake_id = "00000000-0000-0000-0000-000000000000"
        result = self._make_request("GET", f"/documents/{fake_id}")
        self.test_results.append(("Get nonexistent document (error case)", result))
        # This should fail with 404
        if result["status_code"] == 404:
            print("   ✅ Correctly returned 404 for nonexistent document")
        return result
    
    def test_download_document_file(self, document_id: str = None) -> Dict[str, Any]:
        """
        Test GET /api/v1/documents/{document_id}/file.
        
        Args:
            document_id: Document ID to download. If None, tries to get one from list.
        """
        print("\n⬇️  Test 10: Download document file")
        
        # If no document_id provided, try to get one from listing
        if not document_id:
            list_result = self.test_list_all_documents()
            if list_result["success"] and list_result["response"]:
                documents = list_result["response"].get("documents", [])
                if documents:
                    document_id = documents[0]["id"]
                    print(f"   Using document ID from list: {document_id}")
                else:
                    print("   ⚠️  No documents found to test with")
                    result = {
                        "method": "GET",
                        "endpoint": f"/documents/{document_id}/file",
                        "status_code": 0,
                        "success": False,
                        "error": "No documents available for testing"
                    }
                    self.test_results.append(("Download document file", result))
                    return result
        
        url = f"{self.base_url}/documents/{document_id}/file"
        print(f"\n{'='*60}")
        print(f"🌐 GET {url}")
        
        try:
            response = requests.get(url, headers=self.headers, stream=True)
            status_emoji = "✅" if 200 <= response.status_code < 300 else "❌"
            print(f"{status_emoji} Status: {response.status_code} {response.reason}")
            
            result = {
                "method": "GET",
                "endpoint": f"/documents/{document_id}/file",
                "status_code": response.status_code,
                "success": 200 <= response.status_code < 300,
                "content_type": response.headers.get("Content-Type"),
                "content_length": response.headers.get("Content-Length"),
                "error": None
            }
            
            if result["success"]:
                print(f"   Content-Type: {result['content_type']}")
                print(f"   Content-Length: {result['content_length']} bytes")
                # Don't download the full file, just verify headers
            else:
                try:
                    error_detail = response.json().get("detail", "Unknown error")
                    result["error"] = error_detail
                    print(f"   Error: {error_detail}")
                except:
                    result["error"] = response.text[:200]
                    print(f"   Error: {result['error']}")
            
            self.test_results.append(("Download document file", result))
            return result
            
        except Exception as e:
            error_msg = f"❌ Request failed: {str(e)}"
            print(error_msg)
            result = {
                "method": "GET",
                "endpoint": f"/documents/{document_id}/file",
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
            self.test_results.append(("Download document file", result))
            return result
    
    def test_download_nonexistent_file(self) -> Dict[str, Any]:
        """Test GET /api/v1/documents/{invalid_id}/file - Should return 404."""
        print("\n❌ Test 11: Download nonexistent file (should fail)")
        fake_id = "00000000-0000-0000-0000-000000000000"
        url = f"{self.base_url}/documents/{fake_id}/file"
        print(f"\n{'='*60}")
        print(f"🌐 GET {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            status_emoji = "✅" if response.status_code == 404 else "❌"
            print(f"{status_emoji} Status: {response.status_code} {response.reason}")
            
            result = {
                "method": "GET",
                "endpoint": f"/documents/{fake_id}/file",
                "status_code": response.status_code,
                "success": response.status_code == 404,  # 404 is expected
                "error": None
            }
            
            if result["status_code"] == 404:
                print("   ✅ Correctly returned 404 for nonexistent file")
            else:
                result["error"] = "Expected 404 but got different status"
            
            self.test_results.append(("Download nonexistent file (error case)", result))
            return result
            
        except Exception as e:
            result = {
                "method": "GET",
                "endpoint": f"/documents/{fake_id}/file",
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
            self.test_results.append(("Download nonexistent file (error case)", result))
            return result
    
    def test_unauthorized_access(self) -> Dict[str, Any]:
        """Test accessing endpoints without authentication - Should return 401."""
        print("\n🔒 Test 12: Unauthorized access (should fail)")
        headers_no_auth = {"Content-Type": "application/json"}
        url = f"{self.base_url}/documents"
        print(f"\n{'='*60}")
        print(f"🌐 GET {url} (no auth token)")
        
        try:
            response = requests.get(url, headers=headers_no_auth)
            status_emoji = "✅" if response.status_code == 401 else "❌"
            print(f"{status_emoji} Status: {response.status_code} {response.reason}")
            
            result = {
                "method": "GET",
                "endpoint": "/documents",
                "status_code": response.status_code,
                "success": response.status_code == 401,  # 401 is expected
                "error": None
            }
            
            if result["status_code"] == 401:
                print("   ✅ Correctly rejected unauthorized access")
            else:
                result["error"] = f"Expected 401 but got {response.status_code}"
            
            self.test_results.append(("Unauthorized access (error case)", result))
            return result
            
        except Exception as e:
            result = {
                "method": "GET",
                "endpoint": "/documents",
                "status_code": 0,
                "success": False,
                "error": str(e)
            }
            self.test_results.append(("Unauthorized access (error case)", result))
            return result
    
    def run_all_tests(self):
        """Run all test cases."""
        print("\n" + "="*60)
        print("🧪 DOCUMENT ENDPOINTS TEST SUITE")
        print("="*60)
        print(f"Base URL: {self.base_url}")
        print(f"Auth Token: {'✅ Set' if self.auth_token else '❌ Not set'}")
        print("="*60)
        
        # Run all tests
        self.test_list_all_documents()
        self.test_list_documents_with_pagination()
        self.test_list_flight_documents()
        self.test_list_hotel_documents()
        self.test_list_visa_documents()
        self.test_list_itinerary_documents()
        self.test_list_invalid_type()
        self.test_get_document_by_id()
        self.test_get_nonexistent_document()
        self.test_download_document_file()
        self.test_download_nonexistent_file()
        self.test_unauthorized_access()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary."""
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        total = len(self.test_results)
        passed = sum(1 for _, result in self.test_results if result.get("success", False))
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/total*100):.1f}%")
        
        print("\n" + "-"*60)
        print("Detailed Results:")
        print("-"*60)
        
        for test_name, result in self.test_results:
            status = "✅ PASS" if result.get("success", False) else "❌ FAIL"
            status_code = result.get("status_code", "N/A")
            print(f"{status} - {test_name} (Status: {status_code})")
            if not result.get("success") and result.get("error"):
                print(f"      Error: {result['error']}")
        
        print("\n" + "="*60)


def main():
    """Main entry point for running tests."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test document endpoints")
    parser.add_argument(
        "--url",
        default=None,
        help="Backend API URL (default: http://localhost:8000/api/v1)"
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Supabase JWT token (or set SUPABASE_ACCESS_TOKEN env var)"
    )
    parser.add_argument(
        "--test",
        default=None,
        help="Run specific test (e.g., 'list', 'get', 'download')"
    )
    
    args = parser.parse_args()
    
    tester = DocumentEndpointTester(base_url=args.url, auth_token=args.token)
    
    if args.test:
        # Run specific test
        test_map = {
            "list": tester.test_list_all_documents,
            "list-paginated": tester.test_list_documents_with_pagination,
            "list-flight": tester.test_list_flight_documents,
            "list-hotel": tester.test_list_hotel_documents,
            "list-visa": tester.test_list_visa_documents,
            "list-itinerary": tester.test_list_itinerary_documents,
            "get": tester.test_get_document_by_id,
            "download": tester.test_download_document_file,
        }
        
        if args.test in test_map:
            test_map[args.test]()
            tester.print_summary()
        else:
            print(f"Unknown test: {args.test}")
            print(f"Available tests: {', '.join(test_map.keys())}")
    else:
        # Run all tests
        tester.run_all_tests()


if __name__ == "__main__":
    main()

