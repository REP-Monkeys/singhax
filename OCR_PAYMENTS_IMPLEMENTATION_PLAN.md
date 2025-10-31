# OCR & Payments Implementation Plan

## 🎯 Overview

This document outlines a phased approach to implementing:
1. **OCR/Document Intelligence** (Block 3) - Extract trip info from travel documents
2. **Payment Processing** (Block 4) - Stripe integration for policy purchases

Each phase includes:
- ✅ Implementation steps
- 🧪 Automated testing
- 👤 Human testing instructions
- ✅ Success criteria

---

## 📦 Phase 0: Setup & Dependencies

### **Goal:** Install required dependencies and set up project structure

### **Tasks:**

1. **Add OCR dependencies:**
   ```bash
   cd apps/backend
   pip install pytesseract Pillow pdf2image
   ```

2. **Add Stripe SDK:**
   ```bash
   pip install stripe
   ```

3. **Update requirements.txt:**
   ```bash
   # OCR dependencies
   pytesseract>=0.3.10
   Pillow>=10.0.0
   pdf2image>=1.16.3
   
   # Payment processing
   stripe>=7.0.0
   ```

4. **Install system dependencies (macOS):**
   ```bash
   brew install tesseract poppler
   ```

5. **Install system dependencies (Linux/Docker):**
   ```dockerfile
   RUN apt-get update && apt-get install -y \
       tesseract-ocr \
       poppler-utils \
       libtesseract-dev
   ```

6. **Create directory structure:**
   ```bash
   mkdir -p apps/backend/app/services/ocr
   mkdir -p apps/backend/app/services/payments
   mkdir -p apps/backend/app/routers/ocr
   mkdir -p apps/backend/uploads/documents
   mkdir -p apps/backend/uploads/temp
   ```

### **Testing:**

**Automated Test:**
```python
# tests/test_setup.py
def test_ocr_dependencies():
    import pytesseract
    from PIL import Image
    assert pytesseract is not None

def test_stripe_dependency():
    import stripe
    assert stripe is not None
```

**Human Test:**
```bash
# Verify installations
python -c "import pytesseract; print('✓ OCR installed')"
python -c "import stripe; print('✓ Stripe installed')"
python -c "from PIL import Image; print('✓ Pillow installed')"
```

### **Success Criteria:**
- ✅ All dependencies installed without errors
- ✅ Tesseract OCR accessible from command line
- ✅ Directory structure created

---

## 🔍 Phase 1: OCR Service Foundation

### **Goal:** Build basic OCR service that can extract text from images/PDFs

### **Implementation Steps:**

1. **Create OCR Service** (`app/services/ocr/ocr_service.py`):
   ```python
   from typing import Dict, Any, Optional
   from PIL import Image
   import pytesseract
   from pdf2image import convert_from_bytes
   import io
   
   class OCRService:
       def extract_text(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
           """Extract text from image or PDF."""
           # Implementation here
   ```

2. **Features to implement:**
   - PDF to image conversion
   - Image preprocessing (optional but recommended)
   - Text extraction using Tesseract
   - Error handling for unsupported formats

3. **Supported formats:**
   - PDF files
   - PNG images
   - JPEG images
   - Max file size: 10MB

### **Testing:**

**Automated Test:**
```python
# tests/test_ocr_service.py
def test_extract_text_from_image():
    ocr_service = OCRService()
    # Create a simple test image with text
    # Verify text extraction works

def test_extract_text_from_pdf():
    ocr_service = OCRService()
    # Create a test PDF
    # Verify text extraction works

def test_unsupported_format():
    ocr_service = OCRService()
    # Test with unsupported format
    # Should raise appropriate error
```

**Human Test:**
1. **Prepare test document:**
   - Take a screenshot of a flight confirmation email
   - Save as `test_flight.png`
   - Include: destination, dates, passenger names

2. **Test via Python shell:**
   ```python
   from app.services.ocr.ocr_service import OCRService
   
   with open('test_flight.png', 'rb') as f:
       file_bytes = f.read()
   
   ocr = OCRService()
   result = ocr.extract_text(file_bytes, 'test_flight.png')
   print(result['text'])  # Should show extracted text
   ```

3. **Expected Output:**
   - Should see text content from the image
   - No crashes or errors
   - Text should be readable (even if not perfect)

### **Success Criteria:**
- ✅ Can extract text from PNG images
- ✅ Can extract text from JPEG images
- ✅ Can extract text from PDF files
- ✅ Handles errors gracefully
- ✅ Returns structured response with extracted text

---

## 🧠 Phase 2: Trip Information Extraction

### **Goal:** Use LLM to extract structured trip data from OCR text

### **Implementation Steps:**

1. **Create Trip Extractor** (`app/services/ocr/trip_extractor.py`):
   ```python
   from app.agents.llm_client import MultiProviderLLMClient
   
   class TripExtractor:
       def extract_trip_info(self, ocr_text: str) -> Dict[str, Any]:
           """Extract structured trip information from OCR text."""
           # Use existing LLMClient.extract_trip_info() logic
   ```

2. **Integration:**
   - Reuse `LLMClient.extract_trip_info()` method
   - Pass OCR text instead of user message
   - Extract: destination, departure_date, return_date, travelers

3. **Create endpoint** (`app/routers/ocr.py`):
   ```python
   @router.post("/extract-trip-info")
   async def extract_trip_info(
       file: UploadFile = File(...),
       current_user: User = Depends(get_current_user)
   ):
       """Extract trip information from uploaded document."""
   ```

### **Testing:**

**Automated Test:**
```python
# tests/test_trip_extractor.py
def test_extract_destination():
    extractor = TripExtractor()
    text = "Flight to Paris, France on December 20, 2025"
    result = extractor.extract_trip_info(text)
    assert result['destination'] == 'France'

def test_extract_dates():
    extractor = TripExtractor()
    text = "Departure: Dec 20, 2025. Return: Jan 3, 2026"
    result = extractor.extract_trip_info(text)
    assert result['departure_date'] is not None
    assert result['return_date'] is not None

def test_extract_travelers():
    extractor = TripExtractor()
    text = "2 passengers: John Doe (age 30), Jane Doe (age 28)"
    result = extractor.extract_trip_info(text)
    assert len(result['travelers']) == 2
```

**Human Test:**

1. **Test with real flight confirmation:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ocr/extract-trip-info \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@flight_confirmation.pdf"
   ```

2. **Expected Response:**
   ```json
   {
     "success": true,
     "extracted_data": {
       "destination": "France",
       "departure_date": "2025-12-20",
       "return_date": "2026-01-03",
       "travelers": [
         {"name": "John Doe", "age": 30},
         {"name": "Jane Doe", "age": 28}
       ]
     },
     "confidence": 0.85
   }
   ```

3. **Manual verification:**
   - Compare extracted data with actual document
   - Check date parsing accuracy
   - Verify traveler information

### **Success Criteria:**
- ✅ Can extract destination from OCR text
- ✅ Can extract dates (various formats)
- ✅ Can extract traveler information
- ✅ Handles partial/missing information gracefully
- ✅ Returns confidence scores

---

## 📤 Phase 3: Instant Quote from Document

### **Goal:** Generate quote directly from uploaded document

### **Implementation Steps:**

1. **Enhance OCR endpoint:**
   - After extraction, automatically create Trip
   - Generate Quote using PricingService
   - Return quote tiers along with extracted data

2. **Create workflow:**
   ```
   Upload Document → OCR → Extract Info → Create Trip → Generate Quote → Return
   ```

3. **Update endpoint** (`app/routers/ocr.py`):
   ```python
   @router.post("/quote-from-document")
   async def quote_from_document(
       file: UploadFile = File(...),
       current_user: User = Depends(get_current_user),
       db: Session = Depends(get_db)
   ):
       """Generate instant quote from uploaded travel document."""
   ```

### **Testing:**

**Automated Test:**
```python
# tests/test_ocr_quote.py
def test_quote_from_document():
    # Mock OCR extraction
    # Mock trip creation
    # Verify quote generation
    # Check all three tiers returned
```

**Human Test:**

1. **Upload document and get quote:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/ocr/quote-from-document \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -F "file=@flight_confirmation.pdf"
   ```

2. **Expected Response:**
   ```json
   {
     "success": true,
     "trip_id": "uuid",
     "quote_id": "uuid",
     "extracted_data": {...},
     "quotes": {
       "standard": {"price": 45.00, "coverage": {...}},
       "elite": {"price": 81.00, "coverage": {...}},
       "premier": {"price": 112.50, "coverage": {...}}
     }
   }
   ```

3. **Compare with manual quote:**
   - Enter same trip details manually via chat
   - Compare prices - should match
   - Verify coverage tiers are correct

### **Success Criteria:**
- ✅ Generates quote within 5 seconds
- ✅ Quote prices match manual entry
- ✅ All three tiers available
- ✅ Trip saved to database
- ✅ User can proceed to purchase

---

## 💳 Phase 4: Stripe Payment Setup

### **Goal:** Set up Stripe integration and payment session creation

### **Implementation Steps:**

1. **Create Payment Service** (`app/services/payments/stripe_service.py`):
   ```python
   import stripe
   from app.core.config import settings
   
   class StripePaymentService:
       def create_checkout_session(self, quote_id: str, amount: float) -> Dict:
           """Create Stripe checkout session."""
   ```

2. **Configure Stripe:**
   - Set up Stripe API keys in `.env`
   - Test mode keys initially
   - Webhook secret for webhook handler

3. **Create payment model** (if needed):
   - Track payment status
   - Link to quotes/policies
   - Store Stripe session IDs

4. **Create payment endpoint** (`app/routers/payments.py`):
   ```python
   @router.post("/create-checkout")
   async def create_checkout(
       quote_id: str,
       current_user: User = Depends(get_current_user)
   ):
       """Create Stripe checkout session for quote."""
   ```

### **Testing:**

**Automated Test:**
```python
# tests/test_stripe_service.py
def test_create_checkout_session():
    service = StripePaymentService()
    session = service.create_checkout_session("quote_id", 100.00)
    assert session['id'] is not None
    assert session['url'] is not None

def test_payment_amount_validation():
    # Test invalid amounts
    # Test negative amounts
    # Test zero amounts
```

**Human Test:**

1. **Get Stripe test keys:**
   - Go to https://dashboard.stripe.com/test/apikeys
   - Copy test publishable and secret keys
   - Add to `.env`:
     ```
     STRIPE_SECRET_KEY=sk_test_...
     STRIPE_PUBLISHABLE_KEY=pk_test_...
     ```

2. **Create checkout session:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/payments/create-checkout \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"quote_id": "your-quote-id"}'
   ```

3. **Expected Response:**
   ```json
   {
     "success": true,
     "checkout_url": "https://checkout.stripe.com/...",
     "session_id": "cs_test_...",
     "amount": 100.00
   }
   ```

4. **Test checkout flow:**
   - Open checkout URL in browser
   - Use test card: `4242 4242 4242 4242`
   - Use any future expiry date
   - Use any CVC
   - Complete payment
   - Verify redirect to success page

### **Success Criteria:**
- ✅ Can create Stripe checkout sessions
- ✅ Checkout URL is valid and accessible
- ✅ Test payment completes successfully
- ✅ Payment session ID stored in database

---

## 🔔 Phase 5: Payment Webhook Handler

### **Goal:** Handle Stripe webhooks to update payment status

### **Implementation Steps:**

1. **Create webhook handler** (`app/routers/payments.py`):
   ```python
   @router.post("/webhook")
   async def stripe_webhook(request: Request):
       """Handle Stripe webhook events."""
       # Verify webhook signature
       # Handle payment_intent.succeeded
       # Update payment status in database
   ```

2. **Webhook events to handle:**
   - `payment_intent.succeeded` - Payment completed
   - `payment_intent.payment_failed` - Payment failed
   - `checkout.session.completed` - Checkout completed

3. **Update payment status:**
   - Link webhook to quote/policy
   - Update payment record
   - Create policy if payment successful

4. **Webhook signature verification:**
   - Use Stripe webhook secret
   - Verify signature for security

### **Testing:**

**Automated Test:**
```python
# tests/test_webhook.py
def test_webhook_signature_verification():
    # Test valid signature
    # Test invalid signature
    # Test missing signature

def test_payment_succeeded_webhook():
    # Mock webhook payload
    # Verify payment status updated
    # Verify policy created
```

**Human Test:**

1. **Set up Stripe webhook:**
   - Install Stripe CLI: `brew install stripe/stripe-cli/stripe`
   - Login: `stripe login`
   - Forward webhooks: `stripe listen --forward-to localhost:8000/api/v1/payments/webhook`
   - Copy webhook signing secret

2. **Update `.env`:**
   ```
   STRIPE_WEBHOOK_SECRET=whsec_...
   ```

3. **Test webhook:**
   - Complete a test payment (from Phase 4)
   - Check webhook logs in terminal
   - Verify payment status updated in database:
     ```sql
     SELECT * FROM payments WHERE session_id = 'cs_test_...';
     ```

4. **Check policy creation:**
   - After successful payment, verify policy created:
     ```sql
     SELECT * FROM policies WHERE quote_id = '...';
     ```

### **Success Criteria:**
- ✅ Webhook receives events from Stripe
- ✅ Payment status updates correctly
- ✅ Policy created after successful payment
- ✅ Handles failed payments gracefully
- ✅ Webhook signature verified securely

---

## 🔄 Phase 6: Payment Status Polling

### **Goal:** Allow system to check payment status (for MCP/completion flow)

### **Implementation Steps:**

1. **Create status endpoint:**
   ```python
   @router.get("/payment-status/{session_id}")
   async def get_payment_status(
       session_id: str,
       current_user: User = Depends(get_current_user)
   ):
       """Get payment status for a session."""
   ```

2. **Integrate with conversation flow:**
   - After checkout URL provided, periodically check status
   - Update user when payment completes
   - Continue conversation flow after payment

3. **Status states:**
   - `pending` - Checkout created, waiting for payment
   - `processing` - Payment submitted, processing
   - `succeeded` - Payment successful
   - `failed` - Payment failed
   - `expired` - Checkout session expired

### **Testing:**

**Automated Test:**
```python
# tests/test_payment_status.py
def test_get_payment_status():
    # Create test payment session
    # Check status endpoint
    # Verify correct status returned
```

**Human Test:**

1. **Create checkout session:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/payments/create-checkout \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"quote_id": "..."}'
   ```

2. **Check status before payment:**
   ```bash
   curl http://localhost:8000/api/v1/payments/payment-status/SESSION_ID \
     -H "Authorization: Bearer YOUR_TOKEN"
   ```
   - Should return: `{"status": "pending"}`

3. **Complete payment, then check status:**
   - Complete payment in browser
   - Wait 2-3 seconds
   - Check status again
   - Should return: `{"status": "succeeded"}`

4. **Test expired session:**
   - Create checkout session
   - Wait 24 hours (or manually expire)
   - Check status
   - Should return: `{"status": "expired"}`

### **Success Criteria:**
- ✅ Can check payment status by session ID
- ✅ Status updates correctly after payment
- ✅ Handles expired sessions
- ✅ Returns appropriate error for invalid sessions

---

## 🎨 Phase 7: Frontend Integration - OCR

### **Goal:** Add document upload UI to frontend

### **Implementation Steps:**

1. **Create upload component** (`apps/frontend/src/components/DocumentUpload.tsx`):
   - File input
   - Drag & drop support
   - Progress indicator
   - Preview extracted data

2. **Add to quote page:**
   - Button: "Upload Travel Document"
   - Modal with upload interface
   - Show extracted data for review
   - Allow editing before generating quote

3. **API integration:**
   - Call `/api/v1/ocr/quote-from-document`
   - Display quote tiers
   - Handle errors gracefully

### **Testing:**

**Human Test:**

1. **Navigate to quote page:**
   - Go to `http://localhost:3000/app/quote`
   - Should see "Upload Document" button

2. **Upload document:**
   - Click "Upload Document"
   - Select a flight confirmation PDF/image
   - Wait for processing (show loading state)
   - Should display extracted information

3. **Review extracted data:**
   - Check destination is correct
   - Check dates are correct
   - Check travelers are correct
   - Edit if needed

4. **Generate quote:**
   - Click "Generate Quote"
   - Should show three quote tiers
   - Prices should match backend

5. **Test error handling:**
   - Upload invalid file (e.g., .txt file)
   - Should show error message
   - Upload corrupted image
   - Should handle gracefully

### **Success Criteria:**
- ✅ Upload button visible and functional
- ✅ Can upload documents (PDF, PNG, JPEG)
- ✅ Shows extracted data for review
- ✅ Can edit extracted data
- ✅ Generates quote successfully
- ✅ Error handling works

---

## 💰 Phase 8: Frontend Integration - Payments

### **Goal:** Add payment flow to frontend

### **Implementation Steps:**

1. **Add payment button to quote display:**
   - "Purchase" button for each tier
   - Shows price clearly
   - Calls payment endpoint

2. **Create payment flow:**
   - Click "Purchase" → Create checkout session
   - Redirect to Stripe checkout
   - Handle return from Stripe
   - Show success/failure message

3. **Payment status checking:**
   - After redirect, check payment status
   - Poll if pending
   - Show success message when complete
   - Display policy number

4. **Error handling:**
   - Handle payment failures
   - Show retry option
   - Handle expired sessions

### **Testing:**

**Human Test:**

1. **Start from quote:**
   - Generate quote (via chat or document upload)
   - Should see three tiers with "Purchase" buttons

2. **Initiate payment:**
   - Click "Purchase" on any tier
   - Should redirect to Stripe checkout
   - Checkout should show correct amount

3. **Complete payment:**
   - Use test card: `4242 4242 4242 4242`
   - Complete payment
   - Should redirect back to app
   - Should show success message
   - Should display policy number

4. **Test payment failure:**
   - Use declined card: `4000 0000 0000 0002`
   - Should show error message
   - Should allow retry

5. **Test payment status polling:**
   - Start payment but don't complete
   - Return to app
   - Should check status
   - Should update when payment completes

### **Success Criteria:**
- ✅ Purchase buttons visible and functional
- ✅ Redirects to Stripe checkout correctly
- ✅ Returns from Stripe successfully
- ✅ Shows success message after payment
- ✅ Displays policy information
- ✅ Handles failures gracefully

---

## 🔗 Phase 9: End-to-End Integration

### **Goal:** Complete flow from document upload to policy purchase

### **Implementation Steps:**

1. **Full workflow:**
   ```
   Upload Document → Extract Info → Generate Quote → 
   Select Tier → Create Payment → Complete Payment → 
   Receive Policy
   ```

2. **Conversation integration:**
   - Allow user to mention document upload in chat
   - Guide user through upload process
   - Show extracted data in chat
   - Continue conversation flow

3. **Policy delivery:**
   - After payment, generate policy PDF (optional)
   - Email policy to user (optional)
   - Display policy in dashboard

### **Testing:**

**Human Test - Complete Flow:**

1. **Start fresh:**
   - Clear browser cache
   - Log in as new user
   - Go to quote page

2. **Upload document:**
   - Click "Upload Document"
   - Upload real flight confirmation
   - Review extracted data
   - Click "Generate Quote"

3. **Review quotes:**
   - See three tiers
   - Compare coverage
   - Select a tier

4. **Complete purchase:**
   - Click "Purchase"
   - Complete Stripe checkout
   - Return to app
   - See success message
   - See policy details

5. **Verify in dashboard:**
   - Go to dashboard
   - Should see policy listed
   - Should see trip information
   - Should see payment status

6. **Test edge cases:**
   - Upload document with missing info
   - Upload low-quality image
   - Start payment but close browser
   - Return later and check status

### **Success Criteria:**
- ✅ Complete flow works end-to-end
- ✅ No crashes or errors
- ✅ Data persists correctly
- ✅ User experience is smooth
- ✅ All edge cases handled

---

## 📊 Phase 10: Performance & Polish

### **Goal:** Optimize and polish the implementation

### **Implementation Steps:**

1. **Performance optimization:**
   - Cache OCR results
   - Optimize image preprocessing
   - Async processing for large files
   - Add timeouts

2. **Error messages:**
   - User-friendly error messages
   - Helpful guidance for failures
   - Retry mechanisms

3. **Logging:**
   - Log OCR operations
   - Log payment events
   - Track performance metrics

4. **Documentation:**
   - API documentation
   - User guide
   - Developer notes

### **Testing:**

**Performance Test:**

1. **OCR performance:**
   - Upload 10MB PDF
   - Measure processing time
   - Should complete within 30 seconds

2. **Concurrent uploads:**
   - Upload multiple documents simultaneously
   - Should handle gracefully
   - No race conditions

3. **Payment flow:**
   - Test under load
   - Verify webhook handling
   - Check database consistency

**Human Test:**

1. **User experience:**
   - Walk through entire flow
   - Note any confusing steps
   - Check mobile responsiveness
   - Verify all messages are clear

2. **Error scenarios:**
   - Test all error cases
   - Verify error messages are helpful
   - Check retry mechanisms work

### **Success Criteria:**
- ✅ Performance meets requirements
- ✅ Error handling is robust
- ✅ User experience is polished
- ✅ Documentation is complete

---

## 🧪 Testing Checklist

### **Automated Tests to Create:**

- [ ] OCR service tests
- [ ] Trip extraction tests
- [ ] Payment service tests
- [ ] Webhook handler tests
- [ ] Payment status tests
- [ ] Integration tests

### **Human Testing Scenarios:**

1. **OCR Testing:**
   - [ ] Upload PNG image with flight confirmation
   - [ ] Upload JPEG image with itinerary
   - [ ] Upload PDF with booking details
   - [ ] Upload corrupted file (should error)
   - [ ] Upload unsupported format (should error)
   - [ ] Upload very large file (should handle or error)

2. **Extraction Testing:**
   - [ ] Document with all info present
   - [ ] Document with missing dates
   - [ ] Document with multiple travelers
   - [ ] Document with partial info
   - [ ] Low-quality scan (should still work)

3. **Payment Testing:**
   - [ ] Successful payment flow
   - [ ] Failed payment (declined card)
   - [ ] Expired checkout session
   - [ ] Payment cancellation
   - [ ] Webhook delay simulation
   - [ ] Concurrent payment attempts

4. **Integration Testing:**
   - [ ] Document → Quote → Purchase flow
   - [ ] Chat → Upload → Quote flow
   - [ ] Multiple quotes, select one
   - [ ] Payment → Policy creation
   - [ ] Dashboard shows policy

---

## 📝 Quick Reference: Test Commands

### **OCR Testing:**
```bash
# Test OCR endpoint
curl -X POST http://localhost:8000/api/v1/ocr/extract-trip-info \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@test_document.pdf"

# Test quote from document
curl -X POST http://localhost:8000/api/v1/ocr/quote-from-document \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@test_document.pdf"
```

### **Payment Testing:**
```bash
# Create checkout session
curl -X POST http://localhost:8000/api/v1/payments/create-checkout \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"quote_id": "QUOTE_ID"}'

# Check payment status
curl http://localhost:8000/api/v1/payments/payment-status/SESSION_ID \
  -H "Authorization: Bearer TOKEN"

# Forward Stripe webhooks
stripe listen --forward-to localhost:8000/api/v1/payments/webhook
```

### **Test Cards:**
- Success: `4242 4242 4242 4242`
- Decline: `4000 0000 0000 0002`
- 3D Secure: `4000 0025 0000 3155`

---

## 🎯 Success Metrics

### **OCR:**
- ✅ 90%+ extraction accuracy for clean documents
- ✅ Processing time < 10 seconds for typical documents
- ✅ Handles 5+ document formats

### **Payments:**
- ✅ 100% successful payment completion rate (test mode)
- ✅ Webhook processing < 2 seconds
- ✅ Payment status updates correctly
- ✅ Zero payment data loss

---

## 🚨 Common Issues & Solutions

### **OCR Issues:**

**Issue:** Tesseract not found
- **Solution:** Install system dependencies (tesseract-ocr)

**Issue:** Poor text extraction
- **Solution:** Add image preprocessing (contrast, denoising)

**Issue:** PDF conversion fails
- **Solution:** Install poppler-utils

### **Payment Issues:**

**Issue:** Webhook not received
- **Solution:** Check Stripe CLI forwarding, verify webhook secret

**Issue:** Payment status not updating
- **Solution:** Check webhook handler logs, verify database updates

**Issue:** Checkout session expired
- **Solution:** Increase session timeout or handle expiry gracefully

---

## 📚 Resources

- **Tesseract OCR:** https://github.com/tesseract-ocr/tesseract
- **Stripe Docs:** https://stripe.com/docs
- **Stripe Testing:** https://stripe.com/docs/testing
- **FastAPI File Uploads:** https://fastapi.tiangolo.com/tutorial/request-files/

---

**Last Updated:** January 2025
**Status:** Ready for Implementation

