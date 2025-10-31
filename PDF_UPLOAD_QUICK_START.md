# PDF Upload Feature - Quick Start Guide

## 🚀 What's Been Implemented

Your travel insurance chat now supports **instant PDF document processing** with automatic information extraction and policy recommendation!

## ✨ Features

1. **📄 PDF Upload Button** - Upload flight confirmations, hotel bookings, itineraries, or visa applications
2. **🔍 Automatic OCR** - Extracts text from PDFs/images instantly
3. **🧠 Smart Detection** - LLM-based document type detection
4. **📊 Structured Extraction** - Converts document to JSON with confidence scores
5. **✅ Confirmation UI** - Beautiful card showing extracted data for review
6. **💡 Policy Recommendation** - Automatically recommends best insurance plan
7. **💬 Single Interface** - Everything happens in the chat - no separate screens

## 🎯 How It Works

### User Flow:
```
1. Click PDF upload button (📄 icon)
2. Select PDF/image file
3. System processes automatically:
   - OCR extracts text
   - Detects document type
   - Extracts structured data
   - Shows confirmation card
4. Review extracted information
5. Click "Confirm" button
6. System recommends policy
7. Quote generated automatically
```

## 📋 Document Types Supported

### ✈️ Flight Confirmations
- Extracts: Dates, destinations, travelers, ticket costs, airline info
- Individual ticket pricing per traveler (different classes)

### 🏨 Hotel Bookings
- Extracts: Check-in/out dates, location, investment value, guests
- Cancellation policies, deposit info

### 📄 Itineraries
- Extracts: Activities, destinations, timeline
- Adventure sports detection (LLM-based)
- Risk factors (extreme sports, water sports, etc.)

### 🛂 Visa Applications
- Extracts: Trip purpose, duration, applicant info
- Travel intent and requirements

## 🔧 Setup Required

### 1. Install System Dependencies

**macOS:**
```bash
brew install tesseract poppler
```

**Linux:**
```bash
sudo apt-get install tesseract-ocr poppler-utils libtesseract-dev
```

### 2. Install Python Packages

```bash
cd apps/backend
pip install pytesseract Pillow pdf2image
```

### 3. Verify Installation

```bash
# Check Tesseract
tesseract --version

# Check Python packages
python -c "import pytesseract; print('✓ OCR ready')"
python -c "from pdf2image import convert_from_bytes; print('✓ PDF support ready')"
```

## 🧪 Testing

### Test Upload Flow:

1. **Start Backend:**
   ```bash
   cd apps/backend
   python -m uvicorn app.main:app --reload
   ```

2. **Start Frontend:**
   ```bash
   cd apps/frontend
   npm run dev
   ```

3. **Test Upload:**
   - Navigate to chat interface
   - Click PDF upload button (📄 icon)
   - Upload a test PDF (flight confirmation, hotel booking, etc.)
   - Watch as it processes automatically
   - Review extracted data in confirmation card
   - Click "Confirm"
   - See policy recommendation and quote

## 📁 JSON Files

Extracted data is saved to:
```
apps/backend/uploads/documents/{session_id}_{document_type}_{timestamp}.json
```

Each JSON file contains:
- Extracted structured data
- Confidence scores for each field
- Low-confidence fields flagged
- Missing fields listed

## 🎨 UI Components

### ExtractedDataCard
- Shows extracted information in a beautiful card
- Highlights low-confidence fields
- Three action buttons:
  - **Confirm** - Accepts extracted data, triggers policy recommendation
  - **Edit** - Allows user to type corrections
  - **Reject** - Rejects extraction, asks for manual input

## 🔍 Confidence Levels

- **≥0.90 (High)**: Automatically included ✅
- **0.80-0.89 (Medium)**: Included but flagged for confirmation ⚠️
- **<0.80 (Low)**: Not included, asks user to input manually ❌

## 💡 Policy Recommendation Logic

Based on `POLICY_DECISION_CRITERIA_ANALYSIS.md`:

1. **Pre-existing conditions?**
   - Yes → TravelEasy Pre-Ex (if eligible) or Standard
   
2. **Age 70+?**
   - Yes → TravelEasy Standard (single trip only)
   
3. **Scoot airline?**
   - Yes → Scootsurance
   
4. **Annual coverage?**
   - Yes → TravelEasy Standard
   
5. **Adventure sports?**
   - Yes → Elite/Premier tier recommended

## 🐛 Troubleshooting

### OCR Not Working
- Check Tesseract installation: `tesseract --version`
- Verify Python packages: `pip list | grep pytesseract`
- Check file format (PDF, PNG, JPEG supported)

### PDF Conversion Fails
- Check Poppler installation: `pdftoppm -h`
- Verify pdf2image package: `pip list | grep pdf2image`

### LLM Extraction Fails
- Check Groq API key in `.env`
- Verify API quota/limits
- Check console logs for error messages

### File Upload Fails
- Check file size (<10MB)
- Verify file format (PDF, PNG, JPEG)
- Check backend logs for errors

## 📝 Next Steps

1. **Test with real documents** - Try with actual flight confirmations, hotel bookings
2. **Refine extraction prompts** - Improve type-specific extraction accuracy
3. **Add normalized merger** - Combine multiple documents
4. **Enhance policy matching** - Match to specific policy documents
5. **Add more document types** - Expand to other travel documents

## 🎉 Ready to Use!

The PDF upload feature is **fully implemented and ready for testing**. Upload a document and watch the magic happen! 🚀

