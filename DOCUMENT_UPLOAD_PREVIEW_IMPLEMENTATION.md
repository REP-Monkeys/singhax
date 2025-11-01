# Document Upload Preview & JSON Extraction Implementation

## Overview
Implemented ChatGPT-style document upload previews with structured JSON extraction. The system extracts text using Tesseract OCR, converts it to structured JSON based on document type (flight confirmation, hotel booking, itinerary, visa application), and processes the structured data through the LLM without showing raw OCR text to users.

## Changes Made

### Frontend Changes

#### 1. **FileAttachment Component** (`apps/frontend/src/components/FileAttachment.tsx`)
- Added colored file type icons (red for PDF, blue for images)
- Two display variants:
  - `'chat'`: For displaying files in chat messages
  - `'input'`: For preview in input area before sending (ChatGPT-style)
- Added remove button for input preview
- Shows file type label (PDF/IMAGE/FILE) and file size

#### 2. **Quote Page** (`apps/frontend/src/app/app/quote/page.tsx`)
- **File Selection Flow**:
  - `handleFileSelect()`: Stores selected file for preview (doesn't upload immediately)
  - `handleFileUpload()`: Uploads file when user sends message
  - `handleRemoveFile()`: Removes selected file from preview
  
- **Send Logic**:
  - Send button enabled when either text OR file is present
  - Allows sending file without text (like ChatGPT)
  - Uploads file first, then sends text message if provided
  
- **UI Updates**:
  - File preview shown above input area before sending
  - Placeholder changes to "Ask anything..." when file is attached
  - Chat messages display file attachment component instead of text like "[User uploaded a document: filename.pdf]"

### Backend Changes

#### 1. **Upload Endpoint** (`apps/backend/app/routers/chat.py`)
- **OCR Processing Flow**:
  1. Extract text using `OCRService` (Tesseract OCR)
  2. Extract structured JSON using `JSONExtractor`
  3. Store structured JSON in state's `document_data` instead of message content
  4. Create simple message: `[User uploaded a document: filename]` (no raw OCR text)
  5. Pass structured JSON to graph for processing

- **Key Changes**:
  - Raw OCR text no longer included in chat messages
  - Structured JSON stored in `document_data` array in state
  - Each document entry includes: `filename`, `extracted_json`, `document_type`, `uploaded_at`

#### 2. **JSON Extraction Service** (`apps/backend/app/services/ocr/json_extractor.py`)
- **Document Type Detection**:
  - Uses LLM (`DocumentTypeDetector`) to detect document type from OCR text
  - Supports: `flight_confirmation`, `hotel_booking`, `itinerary`, `visa_application`
  - Returns type with confidence score

- **Structured Extraction**:
  - Type-specific extraction functions for each document type
  - Extracts fields according to `DOCUMENT_JSON_STRUCTURES.md` schema
  - Confidence scoring for each extracted field (0.0-1.0)
  - Categorizes fields into:
    - `high_confidence_fields` (≥0.90): Auto-accepted
    - `low_confidence_fields` (0.80-0.89): Flagged for user confirmation
    - `missing_fields` (<0.80): Requires manual input

- **Extraction Process**:
  1. Detect document type using LLM
  2. Call type-specific extraction function (e.g., `_extract_flight_confirmation`)
  3. LLM extracts structured data with confidence scores
  4. Filter and categorize fields by confidence
  5. Save JSON file to disk for reference
  6. Return structured JSON matching schema

- **Document Type Handlers**:
  - **Flight Confirmation**: Airline, flight details, travelers, trip value, booking reference
  - **Hotel Booking**: Hotel details, location, booking dates, room details, investment value, guests
  - **Itinerary**: Trip overview, destinations, activities, adventure sports detection, risk factors
  - **Visa Application**: Visa details, applicant info, trip purpose, planned trip, accommodation info

#### 3. **Graph Processing** (`apps/backend/app/agents/graph.py`)
- **State Updates**:
  - Added `document_data: List[Dict[str, Any]]` to `ConversationState`
  - Added `uploaded_filename: str` to track current file

- **Document Processing Node** (`process_document()`):
  - Reads structured JSON from `state["document_data"]` instead of parsing OCR text
  - Gets most recent document from `document_data` array
  - Extracts information based on document type:
    - Flight confirmation → destination, dates, travelers
    - Hotel booking → location, check-in/out dates
    - Itinerary → destinations, dates, adventure sports
    - Visa application → destination, intended dates, applicant age
  - Updates `trip_details`, `travelers_data`, `preferences` in state
  - Removed LLM fallback that required raw OCR text (now uses structured JSON only)
  - Generates user-friendly confirmation message with extracted items

- **Processing Flow**:
  1. Check if message contains `[User uploaded a document`
  2. Retrieve latest `extracted_json` from `document_data`
  3. Parse structured JSON based on `document_type`
  4. Extract relevant fields and update conversation state
  5. Build confirmation message for user
  6. Set `awaiting_confirmation` flag if needed

## User Experience

### Before
- Raw OCR text displayed in chat: `[User uploaded a document: sample_flight_booking.pdf]`
- Document type and extracted text shown directly in message
- No preview before sending

### After
- Clean file attachment preview in chat messages (like ChatGPT)
- File preview shown in input area before sending
- Can remove file before sending
- Can send file without text
- OCR extraction happens behind the scenes
- Structured JSON data processed by LLM without showing raw text

## Technical Details

### Frontend
- File attachments stored in `Message` interface with `fileAttachment` field
- Selected file tracked in `selectedFile` state
- File validation (type and size) before showing preview
- Send button logic: `disabled={(!inputValue.trim() && !selectedFile) || isLoading || isUploading}`
- Enter key handler updated to allow sending with file attachment

### Backend JSON Extraction Pipeline

1. **OCR Text Extraction** (`OCRService`):
   - Uses Tesseract OCR to extract text from PDF/images
   - Returns text with confidence scores

2. **Document Type Detection** (`DocumentTypeDetector`):
   - LLM analyzes OCR text to determine document type
   - Returns: `{type, confidence, reasoning}`

3. **Structured JSON Extraction** (`JSONExtractor`):
   - Type-specific LLM prompts extract structured data
   - Fields extracted with confidence scores (0.0-1.0)
   - Matches schema defined in `DOCUMENT_JSON_STRUCTURES.md`

4. **Confidence Filtering**:
   - **High (≥0.90)**: Auto-included, no confirmation needed
   - **Medium (0.80-0.89)**: Included but flagged for user confirmation
   - **Low (<0.80)**: Not included, requires manual input

5. **State Storage**:
   - Structured JSON stored in `document_data` array
   - Graph reads from state instead of message content
   - No raw OCR text passed to LLM conversation

### JSON Schema Compliance
- All extracted JSON follows structures in `DOCUMENT_JSON_STRUCTURES.md`
- Includes metadata: `session_id`, `document_type`, `extracted_at`, `source_filename`
- Confidence thresholds: `high: 0.90`, `medium: 0.80`, `low: 0.80`
- Field categorization: `high_confidence_fields`, `low_confidence_fields`, `missing_fields`

## Files Modified

### Frontend
1. `apps/frontend/src/components/FileAttachment.tsx` - New component
2. `apps/frontend/src/app/app/quote/page.tsx` - Updated file handling and UI

### Backend
3. `apps/backend/app/routers/chat.py` - Updated upload endpoint with JSON extraction
4. `apps/backend/app/agents/graph.py` - Updated document processing to use structured JSON
5. `apps/backend/app/services/ocr/json_extractor.py` - JSON extraction service (already existed, now integrated)
6. `apps/backend/app/services/ocr/document_detector.py` - Document type detection (already existed)

## Data Flow

```
User uploads file
    ↓
Frontend: Show preview in input area
    ↓
User clicks send
    ↓
Backend: OCRService.extract_text() → Raw text from Tesseract
    ↓
Backend: DocumentTypeDetector.detect_type() → Document type (LLM)
    ↓
Backend: JSONExtractor.extract() → Structured JSON (LLM)
    ↓
Backend: Store JSON in state["document_data"]
    ↓
Backend: Create message "[User uploaded a document: filename]"
    ↓
Backend: Graph.process_document() → Reads structured JSON from state
    ↓
Backend: Extract trip details from JSON → Update conversation state
    ↓
Backend: Generate user-friendly confirmation message
    ↓
Frontend: Display file attachment + assistant response
```

## Benefits

1. **Clean UI**: No raw OCR text cluttering chat messages
2. **Structured Data**: Consistent JSON format for all document types
3. **Confidence Scoring**: Fields tagged by confidence level for user verification
4. **Type Safety**: Document type detection ensures correct extraction schema
5. **Efficiency**: LLM processes structured JSON instead of parsing raw text
6. **User Experience**: ChatGPT-style file previews and clean chat interface

