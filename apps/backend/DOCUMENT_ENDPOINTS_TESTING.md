# Document Endpoints Testing Guide

This guide helps you test all document handling endpoints in the API.

## 📋 Available Endpoints

1. **GET `/api/v1/documents`** - List all documents
2. **GET `/api/v1/documents?type={type}`** - List documents filtered by type (flight, hotel, visa, itinerary)
3. **GET `/api/v1/documents?limit={limit}&offset={offset}`** - List documents with pagination
4. **GET `/api/v1/documents/{document_id}`** - Get specific document details
5. **GET `/api/v1/documents/{document_id}/file`** - Download the original document file

## 🚀 Quick Start

### Option 1: Simple Test Script

```bash
# Set your Supabase access token
export SUPABASE_ACCESS_TOKEN="your_token_here"

# Run the test script
cd apps/backend
python test_documents.py
```

### Option 2: Comprehensive Test Suite

```bash
# Set your Supabase access token
export SUPABASE_ACCESS_TOKEN="your_token_here"

# Run pytest tests
cd apps/backend
pytest tests/test_documents_endpoints.py -v
```

### Option 3: Manual Testing with curl

```bash
# Set your token
TOKEN="your_supabase_access_token"

# 1. List all documents
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/documents

# 2. List flight documents only
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/documents?type=flight"

# 3. List with pagination
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8000/api/v1/documents?limit=10&offset=0"

# 4. Get specific document (replace DOCUMENT_ID)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/documents/DOCUMENT_ID

# 5. Download document file (replace DOCUMENT_ID)
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/documents/DOCUMENT_ID/file \
  --output downloaded_file.pdf
```

## 🔑 Getting Your Access Token

### Method 1: From Browser (Easiest)

1. Open your application in the browser (e.g., http://localhost:3000)
2. Log in to your account
3. Open Developer Tools (F12)
4. Go to **Application** tab → **Local Storage** → `http://localhost:3000`
5. Find `supabase.auth.token` key
6. Copy the `access_token` value from the JSON

### Method 2: From Browser Console

```javascript
// In browser console after logging in:
const session = await supabase.auth.getSession();
console.log(session.data.session.access_token);
```

### Method 3: Using Supabase Client

```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
response = supabase.auth.sign_in_with_password({
    "email": "your_email@example.com",
    "password": "your_password"
})
token = response.session.access_token
```

## 📝 Test Scenarios

### 1. List All Documents
- **Expected**: Returns list of all documents (flights, hotels, visas, itineraries)
- **Status**: Should be 200 OK
- **Response format**: `{"documents": [...], "total": N, "limit": 50, "offset": 0}`

### 2. Filter by Type
- **Types**: `flight`, `hotel`, `visa`, `itinerary`
- **Expected**: Returns only documents of specified type
- **Invalid type**: Should return 400 Bad Request

### 3. Pagination
- **Parameters**: `limit` (1-100), `offset` (≥0)
- **Expected**: Returns paginated results
- **Test**: Request page 1, then page 2, verify different results

### 4. Get Document Details
- **Expected**: Returns full document details including extracted data
- **Invalid ID**: Should return 404 Not Found
- **Response includes**: All fields from the document model

### 5. Download File
- **Expected**: Returns file with proper Content-Type headers
- **No file**: Should return 404 if file_path is null
- **Headers**: Should include `Content-Type` and `Content-Disposition`

### 6. Error Cases
- **No auth token**: Should return 401 Unauthorized
- **Invalid document ID**: Should return 404 Not Found
- **Invalid type**: Should return 400 Bad Request

## 🧪 Running Specific Tests

### Using the test script:

```bash
# Run specific test
python test_documents.py --test list

# Available test names:
# - list: List all documents
# - list-paginated: Test pagination
# - list-flight: List flight documents
# - list-hotel: List hotel documents
# - list-visa: List visa documents
# - list-itinerary: List itinerary documents
# - get: Get document by ID
# - download: Download document file
```

### Using pytest:

```bash
# Run all document tests
pytest tests/test_documents_endpoints.py -v

# Run specific test
pytest tests/test_documents_endpoints.py::DocumentEndpointTester::test_list_all_documents -v

# Run with verbose output
pytest tests/test_documents_endpoints.py -v -s
```

## 🔍 Verifying Results

### Successful Response Examples

**List Documents:**
```json
{
  "documents": [
    {
      "id": "uuid-here",
      "type": "flight",
      "filename": "flight_confirmation.pdf",
      "extracted_at": "2024-01-01T12:00:00Z",
      "created_at": "2024-01-01T12:00:00Z",
      "summary": {
        "airline": "Singapore Airlines",
        "departure_date": "2024-02-01",
        "destination": "Tokyo, Japan"
      }
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Get Document:**
```json
{
  "id": "uuid-here",
  "type": "flight",
  "filename": "flight_confirmation.pdf",
  "source_filename": "flight_confirmation.pdf",
  "extracted_at": "2024-01-01T12:00:00Z",
  "created_at": "2024-01-01T12:00:00Z",
  "session_id": "session-uuid",
  "file_path": "documents/user_id/flight/filename.pdf",
  "file_size": 12345,
  "file_content_type": "application/pdf",
  "airline_name": "Singapore Airlines",
  "departure_date": "2024-02-01",
  "destination_country": "Japan",
  "destination_city": "Tokyo",
  "extracted_data": {...}
}
```

## 🐛 Troubleshooting

### Connection Errors
- **Error**: `ConnectionError - Backend not running`
- **Solution**: Make sure backend is running on `http://localhost:8000`

### Authentication Errors
- **Error**: `401 Unauthorized`
- **Solution**: Check that your token is valid and not expired

### No Documents Found
- **Issue**: Tests return empty document lists
- **Solution**: Upload some documents first via the chat interface (`/api/v1/chat/upload-image`)

### Database Errors
- **Error**: Database connection issues
- **Solution**: Check database connection and ensure tables exist (run migrations)

## 📊 Expected Test Results

When all tests pass, you should see:

```
✅ PASS - List all documents (Status: 200)
✅ PASS - List documents (paginated) (Status: 200)
✅ PASS - List flight documents (Status: 200)
✅ PASS - List hotel documents (Status: 200)
✅ PASS - List visa documents (Status: 200)
✅ PASS - List itinerary documents (Status: 200)
✅ PASS - List invalid type (error case) (Status: 400)
✅ PASS - Get document by ID (Status: 200)
✅ PASS - Get nonexistent document (error case) (Status: 404)
✅ PASS - Download document file (Status: 200)
✅ PASS - Download nonexistent file (error case) (Status: 404)
✅ PASS - Unauthorized access (error case) (Status: 401)
```

## 🎯 Next Steps

After testing:
1. Review backend logs for any warnings or errors
2. Verify file storage is working (check uploads directory or Supabase Storage)
3. Test document upload flow via chat interface
4. Verify extracted data is correctly stored

