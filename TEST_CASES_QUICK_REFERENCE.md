# Test Cases Quick Reference

## 📍 Test Files Location

### Backend Tests (Automated)

**Location:** `apps/backend/tests/`

**New Test Files Created:**
1. ✅ **`test_json_builders.py`** - 14 test cases for JSON builder functions
2. ✅ **`test_quote_json_storage.py`** - 4 test cases for quote creation with JSON structures  
3. ✅ **`test_document_flow_integration.py`** - 7 test cases for document processing integration

### Frontend Test Scenarios (Manual)

**Location:** `FRONTEND_TEST_SCENARIOS.md` (in project root)

**8 Test Scenarios** covering:
- Document upload with extraction
- Inline editing functionality
- Conversation continuation
- Multiple document uploads
- Error handling
- Quote generation
- Confidence levels display
- Mobile responsiveness

---

## 🚀 Running Backend Tests

### Prerequisites
```bash
cd apps/backend
source venv/bin/activate  # Activate virtual environment
```

### Run All New Tests
```bash
pytest tests/test_json_builders.py tests/test_quote_json_storage.py tests/test_document_flow_integration.py -v
```

### Run Individual Test Files
```bash
# JSON builders tests (14 tests)
pytest tests/test_json_builders.py -v

# Quote JSON storage tests (4 tests)
pytest tests/test_quote_json_storage.py -v

# Document flow integration tests (7 tests)
pytest tests/test_document_flow_integration.py -v
```

### Run Specific Test Classes
```bash
# Test quotation JSON builder only
pytest tests/test_json_builders.py::TestAncileoQuotationJSONBuilder -v

# Test purchase JSON builder only
pytest tests/test_json_builders.py::TestAncileoPurchaseJSONBuilder -v

# Test metadata JSON builder only
pytest tests/test_json_builders.py::TestTripMetadataJSONBuilder -v
```

### Run Specific Test Functions
```bash
# Test round trip quotation builder
pytest tests/test_json_builders.py::TestAncileoQuotationJSONBuilder::test_build_round_trip_quotation -v

# Test quote creation with JSON structures
pytest tests/test_quote_json_storage.py::TestQuoteCreationWithJSONStorage::test_create_quote_with_json_structures_new_quote -v
```

### Run with Coverage
```bash
pytest tests/test_json_builders.py --cov=app.services.json_builders --cov-report=html
```

---

## 📋 Test Case Summary

### Backend Tests (`test_json_builders.py`)

**14 Test Cases:**

1. ✅ `test_build_round_trip_quotation` - Builds complete RT quotation JSON
2. ✅ `test_build_single_trip_quotation` - Builds ST quotation without returnDate
3. ✅ `test_calculate_adults_children_from_ages` - Calculates from ages array
4. ✅ `test_ensure_at_least_one_adult` - Ensures min 1 adult (API requirement)
5. ✅ `test_default_departure_country` - Defaults to "SG"
6. ✅ `test_string_date_formatting` - Handles string dates
7. ✅ `test_build_purchase_json_with_user_data` - Builds purchase JSON
8. ✅ `test_build_purchase_json_with_additional_travelers` - Multiple travelers
9. ✅ `test_empty_user_data` - Handles empty data
10. ✅ `test_build_basic_metadata` - Basic metadata JSON
11. ✅ `test_build_metadata_with_documents` - With document references
12. ✅ `test_build_metadata_with_conversation_flow` - With timestamps
13. ✅ `test_build_metadata_complete` - Full metadata
14. ✅ `test_remove_none_values_from_document_references` - Cleans None values

### Backend Tests (`test_quote_json_storage.py`)

**4 Test Cases:**

1. ✅ `test_create_quote_with_json_structures_new_quote` - Creates new quote with JSONs
2. ✅ `test_update_existing_quote_with_json_structures` - Updates existing quote
3. ✅ `test_json_structures_include_adventure_sports` - Adventure sports flag
4. ✅ `test_purchase_json_with_multiple_travelers` - Multiple travelers in purchase JSON

### Backend Tests (`test_document_flow_integration.py`)

**7 Test Cases:**

1. ✅ `test_extract_ancileo_fields_from_flight_document` - Extracts all Ancileo fields
2. ✅ `test_extract_ancileo_fields_with_children` - Handles children correctly
3. ✅ `test_route_to_needs_assessment_after_document` - Routes correctly
4. ✅ `test_check_all_ancileo_required_fields` - Checks all required fields
5. ✅ `test_prompt_for_missing_ancileo_fields` - Prompts for missing fields
6. ✅ `test_calculate_adults_children_from_ages` - Calculates counts from ages
7. ✅ `test_ensure_at_least_one_adult` - Ensures min 1 adult

---

## 🎯 Frontend Manual Test Scenarios

**Location:** `FRONTEND_TEST_SCENARIOS.md`

### Quick Test Checklist

1. **Document Upload** ✅
   - Upload flight confirmation PDF
   - Verify ExtractedDataCard appears
   - Verify extracted data displays correctly

2. **Inline Editing** ✅
   - Click "Edit" on ExtractedDataCard
   - Modify destination field
   - Click "Save"
   - Verify data updates

3. **Conversation Flow** ✅
   - Upload document
   - Verify assistant asks for missing fields
   - Respond to prompts
   - Verify quote generation

4. **Multiple Documents** ✅
   - Upload flight confirmation
   - Upload hotel booking
   - Upload itinerary
   - Verify all processed correctly

5. **Error Handling** ✅
   - Try invalid file (.txt)
   - Try corrupted PDF
   - Verify error messages

6. **Quote Generation** ✅
   - Complete conversation flow
   - Generate quotes
   - Verify quote created in database with JSON structures

---

## 🔍 Manual Testing Quick Commands

### Check Database After Tests

```sql
-- Check quotes with JSON structures
SELECT 
    id,
    price_min,
    price_max,
    ancileo_quotation_json->>'adventure_sports_activities' as adventure_sports,
    ancileo_purchase_json->'insureds'->0->>'firstName' as primary_traveler
FROM quotes
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 5;

-- Check trips with metadata
SELECT 
    id,
    session_id,
    metadata_json->'document_references' as documents,
    metadata_json->'conversation_flow' as flow
FROM trips
WHERE metadata_json IS NOT NULL
ORDER BY created_at DESC
LIMIT 5;
```

### Test API Endpoints

```bash
# Test document update endpoint
curl -X PUT http://localhost:8000/api/v1/documents/{document_id}/extracted-data \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "extracted_data": {
      "destination": {"country": "Thailand"}
    }
  }'

# Test trips endpoint (should work now)
curl http://localhost:8000/api/v1/trips?status=draft,ongoing,completed \
  -H "Authorization: Bearer {token}"
```

---

## 📚 Detailed Documentation

- **Backend Tests:** See `BACKEND_TEST_GUIDE.md` for detailed test documentation
- **Frontend Tests:** See `FRONTEND_TEST_SCENARIOS.md` for step-by-step scenarios
- **Implementation Plan:** See `document-flow-integration-and-json-storage-restructure.plan.md`

---

## ✅ Quick Verification

After running tests, verify:

1. ✅ All backend tests pass (25 total tests)
2. ✅ Database has new columns (metadata_json, ancileo_quotation_json, ancileo_purchase_json)
3. ✅ Frontend can upload documents without errors
4. ✅ ExtractedDataCard displays correctly
5. ✅ Inline editing works
6. ✅ Conversation continues after document upload
7. ✅ Quotes are created with JSON structures

---

## 🐛 Troubleshooting

### Tests Fail with Import Errors
```bash
# Make sure you're in the backend directory and venv is activated
cd apps/backend
source venv/bin/activate
pytest tests/test_json_builders.py -v
```

### Database Connection Errors
```bash
# Check DATABASE_URL in .env file
# Verify database is accessible
psql $DATABASE_URL -c "SELECT 1"
```

### Frontend Errors
- Check browser console for errors
- Verify backend is running on port 8000
- Check API endpoints are accessible
- Verify authentication token is valid

