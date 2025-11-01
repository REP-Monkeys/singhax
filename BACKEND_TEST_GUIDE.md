# Backend Test Guide - Document Flow Integration & JSON Storage

## Test Files Created

1. **`tests/test_json_builders.py`** - Tests for JSON builder functions
2. **`tests/test_quote_json_storage.py`** - Tests for quote creation with JSON structures
3. **`tests/test_document_flow_integration.py`** - Tests for document processing and needs_assessment integration

## Running Tests

```bash
cd apps/backend

# Run all new tests
pytest tests/test_json_builders.py tests/test_quote_json_storage.py tests/test_document_flow_integration.py -v

# Run specific test file
pytest tests/test_json_builders.py -v

# Run with coverage
pytest tests/test_json_builders.py --cov=app.services.json_builders --cov-report=html
```

## Test Coverage

### 1. JSON Builders Tests (`test_json_builders.py`)

#### TestAncileoQuotationJSONBuilder
- ✅ `test_build_round_trip_quotation` - Builds RT quotation with all fields
- ✅ `test_build_single_trip_quotation` - Builds ST quotation without returnDate
- ✅ `test_calculate_adults_children_from_ages` - Calculates counts from ages array
- ✅ `test_ensure_at_least_one_adult` - Ensures min 1 adult for API
- ✅ `test_default_departure_country` - Defaults to "SG"
- ✅ `test_string_date_formatting` - Handles string dates correctly

#### TestAncileoPurchaseJSONBuilder
- ✅ `test_build_purchase_json_with_user_data` - Builds purchase JSON from user
- ✅ `test_build_purchase_json_with_additional_travelers` - Handles multiple travelers
- ✅ `test_empty_user_data` - Handles empty user data gracefully

#### TestTripMetadataJSONBuilder
- ✅ `test_build_basic_metadata` - Builds minimal metadata
- ✅ `test_build_metadata_with_documents` - Includes document references
- ✅ `test_build_metadata_with_conversation_flow` - Includes timestamps
- ✅ `test_build_metadata_complete` - Full metadata with all fields
- ✅ `test_remove_none_values_from_document_references` - Cleans None values

### 2. Quote JSON Storage Tests (`test_quote_json_storage.py`)

#### TestQuoteCreationWithJSONStorage
- ✅ `test_create_quote_with_json_structures_new_quote` - Creates new quote with JSONs
- ✅ `test_update_existing_quote_with_json_structures` - Updates existing quote
- ✅ `test_json_structures_include_adventure_sports` - Adventure sports flag included
- ✅ `test_purchase_json_with_multiple_travelers` - Multiple travelers in purchase JSON

### 3. Document Flow Integration Tests (`test_document_flow_integration.py`)

#### TestDocumentProcessingAncileoFields
- ✅ `test_extract_ancileo_fields_from_flight_document` - Extracts all Ancileo fields
- ✅ `test_extract_ancileo_fields_with_children` - Handles children correctly
- ✅ `test_route_to_needs_assessment_after_document` - Routes correctly after processing

#### TestNeedsAssessmentAncileoFields
- ✅ `test_check_all_ancileo_required_fields` - Checks all required fields
- ✅ `test_prompt_for_missing_ancileo_fields` - Prompts for missing fields
- ✅ `test_calculate_adults_children_from_ages` - Calculates counts from ages
- ✅ `test_ensure_at_least_one_adult` - Ensures min 1 adult

#### TestDocumentUpdateEndpoint
- ✅ `test_update_document_extracted_data` - Updates document data

## Manual Testing Checklist

### 1. JSON Builders

```python
# Test quotation JSON builder
from app.services.json_builders import build_ancileo_quotation_json
from datetime import date

trip_details = {
    "destination": "Japan",
    "departure_date": date(2025, 12, 15),
    "return_date": date(2025, 12, 22),
    "departure_country": "SG",
    "arrival_country": "JP",
    "adults_count": 2,
    "children_count": 0
}
travelers_data = {"ages": [30, 35], "count": 2}
preferences = {"adventure_sports": False}

quotation_json = build_ancileo_quotation_json(trip_details, travelers_data, preferences)
print(quotation_json)
# Should output: {
#   "market": "SG",
#   "context": {"tripType": "RT", ...},
#   "adventure_sports_activities": False
# }
```

### 2. Document Processing Flow

1. **Upload Flight Confirmation**
   - Upload a flight confirmation PDF
   - Verify `process_document` extracts:
     - `departure_country` (defaults to "SG")
     - `arrival_country` (from destination via GeoMapper)
     - `adults_count` and `children_count` (from travelers)
   - Verify routes to `needs_assessment`

2. **Check Missing Fields**
   - After document upload, verify missing fields prompt includes:
     - departure_country (if missing)
     - arrival_country (if missing)
     - adults_count (if missing)

3. **Quote Creation**
   - After pricing completes, verify:
     - Quote record created/updated in database
     - `ancileo_quotation_json` stored
     - `ancileo_purchase_json` stored
     - `price_min` and `price_max` set

### 3. Database Verification

```sql
-- Check quote JSON structures
SELECT 
    id,
    price_min,
    price_max,
    ancileo_quotation_json->>'adventure_sports_activities' as adventure_sports,
    ancileo_purchase_json->'insureds'->0->>'firstName' as primary_traveler_first_name
FROM quotes
WHERE created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC
LIMIT 5;

-- Check trip metadata
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

## Expected Behavior

### Document Upload Flow

1. User uploads document → `process_document` node
2. Extracts structured JSON from document
3. Extracts Ancileo API required fields:
   - `departure_country` (default: "SG")
   - `arrival_country` (from destination)
   - `adults_count` / `children_count` (from travelers)
4. Sets `_document_processed = True`
5. Routes to `needs_assessment`
6. `needs_assessment` checks for missing Ancileo fields
7. Prompts for missing fields if any
8. Routes to `pricing` when all fields present
9. `pricing` creates/updates Quote with JSON structures

### Quote Creation Flow

1. `pricing` node calculates quotes
2. Builds `ancileo_quotation_json` using builder
3. Builds `ancileo_purchase_json` using builder
4. Creates or updates Quote record:
   - Stores JSON structures
   - Sets `price_min` and `price_max`
   - Sets `status = RANGED`

## Common Issues & Solutions

### Issue: `adventure_sports_activities` sent to API
**Solution:** The field is stored in `ancileo_quotation_json` but removed before API calls. Verify `ancileo_client.py` doesn't include it in payload.

### Issue: Missing `arrival_country`
**Solution:** Ensure `GeoMapper.get_country_iso_code()` is called when destination is provided. Check `process_document` and `needs_assessment` nodes.

### Issue: Quote not created with JSON structures
**Solution:** Verify `pricing` node checks for `trip_id` and `user_id` before creating quote. Check error logs for exceptions.

### Issue: Document update doesn't trigger re-processing
**Solution:** Document update endpoint updates `extracted_data` but doesn't automatically re-process. May need to trigger graph invocation manually.

## Performance Considerations

- JSON builders are lightweight (no external calls)
- Quote creation happens synchronously in pricing node
- Document processing includes GeoMapper call (should be fast)
- Database writes for JSON structures (JSONB is efficient)

## Next Steps

1. Run all tests: `pytest tests/test_*.py -v`
2. Test document upload flow manually
3. Verify database JSON structures
4. Test quote creation with real Ancileo API (if available)
5. Test document update endpoint
6. Integration test with frontend


