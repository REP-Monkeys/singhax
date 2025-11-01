# Frontend Test Scenarios - Document Flow Integration

## Overview

These test scenarios verify the frontend integration with the new document flow and JSON storage features.

## Test Environment Setup

1. Start backend: `cd apps/backend && uvicorn app.main:app --reload`
2. Start frontend: `cd apps/frontend && npm run dev`
3. Login as test user
4. Navigate to `/app/quote`

## Test Scenarios

### Scenario 1: Document Upload with Field Extraction

**Objective:** Verify document upload extracts data and shows it in ExtractedDataCard

**Steps:**
1. Click "Upload Document" button
2. Select a flight confirmation PDF (with destination, dates, travelers)
3. Wait for document processing

**Expected Results:**
- ✅ Document preview appears in chat
- ✅ ExtractedDataCard component displays extracted data:
  - Destination (country)
  - Departure date
  - Return date
  - Number of travelers
- ✅ Assistant responds with extracted information summary
- ✅ Shows confidence levels (high/medium confidence fields)
- ✅ Shows missing fields prompt if any Ancileo fields missing

**Test Data:**
```json
{
  "destination": {"country": "Japan"},
  "flight_details": {
    "departure": {"date": "2025-12-15"},
    "return": {"date": "2025-12-22"}
  },
  "travelers": [{"age": 30}, {"age": 35}]
}
```

**Frontend Checks:**
- `ExtractedDataCard` component renders with `extractedData` prop
- Confidence badges display correctly
- Missing fields section shows if applicable
- Document preview shows filename

---

### Scenario 2: Inline Editing of Extracted Data

**Objective:** Verify users can edit extracted document data inline

**Steps:**
1. Upload document (see Scenario 1)
2. View ExtractedDataCard
3. Click "Edit" button
4. Modify destination field (e.g., change "Japan" to "Thailand")
5. Click "Save" button
6. Wait for save confirmation

**Expected Results:**
- ✅ Edit mode activates (inputs replace display text)
- ✅ Modified values are editable
- ✅ "Save" and "Cancel" buttons appear
- ✅ Save button calls `PUT /api/v1/documents/{document_id}/extracted-data`
- ✅ Success message appears: "Document updated successfully!"
- ✅ ExtractedDataCard updates with new values
- ✅ Database updated with new extracted_data

**API Call Verification:**
```javascript
// Check network tab for:
PUT /api/v1/documents/{document_id}/extracted-data
Headers: {
  Authorization: "Bearer {token}",
  Content-Type: "application/json"
}
Body: {
  extracted_data: {
    destination: {country: "Thailand"},
    // ... other fields
  }
}
Response: 200 OK with updated document
```

**Frontend Checks:**
- `isEditing` state toggles correctly
- `editedData` state updates on input change
- `handleSave` function calls API correctly
- Error handling for failed saves
- Loading state during save

---

### Scenario 3: Document Upload → Conversation Continuation

**Objective:** Verify conversation continues naturally after document upload

**Steps:**
1. Upload flight confirmation document
2. Wait for extraction and assistant response
3. Verify assistant asks for missing fields (if any)
4. Respond to missing fields prompt
5. Continue conversation until quote generation

**Expected Results:**
- ✅ After document upload, assistant response includes:
  - Summary of extracted data
  - Missing fields prompt (if applicable)
  - Natural conversation flow
- ✅ User can respond to prompts naturally
- ✅ Conversation continues without manual intervention
- ✅ Eventually routes to quote generation

**Flow Verification:**
```
User: [Uploads document]
  ↓
Backend: process_document → extracts data
  ↓
Frontend: Shows ExtractedDataCard + Assistant response
  ↓
Assistant: "I still need: departure date, traveler ages"
  ↓
User: "Leaving December 15, 2 travelers ages 30 and 35"
  ↓
Backend: needs_assessment → collects missing fields
  ↓
Assistant: Shows confirmation summary
  ↓
User: "Yes, that's correct"
  ↓
Backend: pricing → generates quotes
  ↓
Frontend: Shows quote options
```

**Frontend Checks:**
- Chat messages render correctly
- ExtractedDataCard appears in correct position
- File attachment preview shows correctly
- Conversation scrolls automatically
- Loading indicators show during processing

---

### Scenario 4: Multiple Document Uploads

**Objective:** Verify handling of multiple document uploads in same session

**Steps:**
1. Upload flight confirmation
2. Upload hotel booking
3. Upload itinerary
4. Verify all documents processed correctly

**Expected Results:**
- ✅ Each document upload shows separate ExtractedDataCard
- ✅ Extracted data from all documents combined in trip_details
- ✅ Assistant references all uploaded documents
- ✅ Trip metadata_json includes all document references

**Frontend Checks:**
- Multiple ExtractedDataCard components render
- Each card shows correct document type
- Document list/scroll handles multiple cards
- No duplicate or missing cards

---

### Scenario 5: Document Upload Error Handling

**Objective:** Verify error handling for failed document uploads

**Steps:**
1. Try uploading invalid file (e.g., .txt file)
2. Try uploading corrupted PDF
3. Try uploading with network error
4. Verify error messages

**Expected Results:**
- ✅ Error message displayed: "Failed to process document"
- ✅ User can retry upload
- ✅ Error doesn't break conversation flow
- ✅ Graceful degradation

**Frontend Checks:**
- Error toast/alert appears
- Error state handled in component
- Retry option available
- No console errors

---

### Scenario 6: Quote Generation with JSON Structures

**Objective:** Verify quote generation stores JSON structures correctly

**Steps:**
1. Complete full conversation flow (upload doc or manual entry)
2. Generate quotes
3. Verify quote created in database
4. Check quote page shows correct data

**Expected Results:**
- ✅ Quote created with:
  - `ancileo_quotation_json` stored
  - `ancileo_purchase_json` stored
  - `price_min` and `price_max` set
- ✅ Quote page displays all tiers correctly
- ✅ Purchase flow can use stored JSON structures

**API Verification:**
```javascript
// After quote generation, check:
GET /api/v1/quotes/{quote_id}
Response should include:
{
  id: "...",
  price_min: 50.00,
  price_max: 125.00,
  ancileo_quotation_json: {
    market: "SG",
    context: {...},
    adventure_sports_activities: false
  },
  ancileo_purchase_json: {
    insureds: [...],
    mainContact: {...}
  }
}
```

**Frontend Checks:**
- Quote page loads quote data
- Price range displays correctly
- Can proceed to purchase
- Purchase uses stored JSON structures

---

### Scenario 7: ExtractedDataCard Confidence Levels

**Objective:** Verify confidence level display in ExtractedDataCard

**Steps:**
1. Upload document with mixed confidence fields
2. Verify confidence badges display
3. Check low confidence fields warning

**Expected Results:**
- ✅ High confidence fields marked clearly
- ✅ Low confidence fields show warning badge
- ✅ Missing fields listed separately
- ✅ User can verify/edit low confidence fields

**Test Data:**
```json
{
  "high_confidence_fields": ["destination", "departure_date"],
  "low_confidence_fields": ["return_date", "travelers"],
  "missing_fields": ["trip_value"]
}
```

**Frontend Checks:**
- Confidence badges render correctly
- Color coding (green/yellow/red)
- Warning icon for low confidence
- Tooltip or help text for confidence levels

---

### Scenario 8: Mobile Responsiveness

**Objective:** Verify ExtractedDataCard works on mobile devices

**Steps:**
1. Open app on mobile device or resize browser
2. Upload document
3. View ExtractedDataCard
4. Try inline editing

**Expected Results:**
- ✅ ExtractedDataCard responsive layout
- ✅ Edit inputs usable on mobile
- ✅ Buttons accessible
- ✅ Text readable

**Frontend Checks:**
- CSS media queries work
- Touch targets adequate size
- Horizontal scroll if needed
- Text wrapping

---

## Component Testing

### ExtractedDataCard Component

```typescript
// Test file: apps/frontend/src/components/__tests__/ExtractedDataCard.test.tsx

describe('ExtractedDataCard', () => {
  it('renders extracted data correctly', () => {
    const extractedData = {
      document_type: 'flight_confirmation',
      destination: {country: 'Japan'},
      flight_details: {
        departure: {date: '2025-12-15'},
        return: {date: '2025-12-22'}
      }
    };
    
    render(<ExtractedDataCard extractedData={extractedData} />);
    
    expect(screen.getByText('Japan')).toBeInTheDocument();
    expect(screen.getByText('2025-12-15')).toBeInTheDocument();
  });
  
  it('enters edit mode when edit button clicked', () => {
    // Test edit mode toggle
  });
  
  it('saves edited data correctly', async () => {
    // Mock API call
    // Test save functionality
  });
  
  it('shows confidence levels', () => {
    // Test confidence badge rendering
  });
});
```

### Quote Page Integration

```typescript
// Test file: apps/frontend/src/app/app/quote/__tests__/page.test.tsx

describe('Quote Page', () => {
  it('handles document upload', async () => {
    // Test document upload flow
  });
  
  it('displays ExtractedDataCard after upload', () => {
    // Test card rendering
  });
  
  it('continues conversation after document processing', () => {
    // Test conversation flow
  });
});
```

## API Integration Tests

### Document Update Endpoint

```javascript
// Test PUT /api/v1/documents/{document_id}/extracted-data
describe('Document Update API', () => {
  it('updates document extracted_data', async () => {
    const response = await fetch(`/api/v1/documents/${docId}/extracted-data`, {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        extracted_data: {
          destination: {country: 'Thailand'}
        }
      })
    });
    
    expect(response.ok).toBe(true);
    const data = await response.json();
    expect(data.extracted_data.destination.country).toBe('Thailand');
  });
});
```

## E2E Test Scenarios (Cypress/Playwright)

```javascript
// cypress/e2e/document-flow.cy.js

describe('Document Upload Flow', () => {
  it('uploads document and continues conversation', () => {
    cy.visit('/app/quote');
    cy.login();
    
    // Upload document
    cy.get('[data-testid="upload-document"]').click();
    cy.get('input[type="file"]').attachFile('flight_confirmation.pdf');
    
    // Wait for processing
    cy.wait('@documentUpload');
    
    // Verify ExtractedDataCard appears
    cy.get('[data-testid="extracted-data-card"]').should('be.visible');
    
    // Verify assistant response
    cy.contains('extracted the following information').should('be.visible');
    
    // Continue conversation
    cy.get('[data-testid="chat-input"]').type('That looks correct');
    cy.get('[data-testid="send-button"]').click();
    
    // Verify quote generation
    cy.contains('insurance options').should('be.visible');
  });
  
  it('edits extracted data inline', () => {
    // Upload document first
    // Click edit button
    // Modify field
    // Save
    // Verify update
  });
});
```

## Performance Tests

1. **Document Upload Performance**
   - Measure time from upload to ExtractedDataCard display
   - Target: < 3 seconds

2. **Save Performance**
   - Measure time from save click to confirmation
   - Target: < 1 second

3. **Multiple Documents**
   - Measure performance with 5+ documents
   - Verify no performance degradation

## Accessibility Tests

1. **Keyboard Navigation**
   - Tab through ExtractedDataCard
   - Edit mode keyboard access
   - Save/Cancel button access

2. **Screen Reader**
   - ExtractedDataCard announcements
   - Confidence level announcements
   - Error messages

3. **ARIA Labels**
   - All interactive elements labeled
   - Form inputs labeled
   - Buttons have accessible names

## Browser Compatibility

Test on:
- ✅ Chrome (latest)
- ✅ Firefox (latest)
- ✅ Safari (latest)
- ✅ Edge (latest)
- ✅ Mobile Safari (iOS)
- ✅ Chrome Mobile (Android)

## Regression Tests

After each change, verify:
1. Document upload still works
2. ExtractedDataCard renders correctly
3. Inline editing functions
4. Conversation flow continues
5. Quote generation works
6. No console errors
7. No broken UI elements


