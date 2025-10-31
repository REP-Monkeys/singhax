# Quick Start: OCR & Payments Implementation

## 🚀 Getting Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd apps/backend

# Install Python packages
pip install pytesseract Pillow pdf2image stripe

# macOS - Install system dependencies
brew install tesseract poppler

# Linux/Docker - Add to Dockerfile or install:
# apt-get update && apt-get install -y tesseract-ocr poppler-utils

# Update requirements.txt
echo "pytesseract>=0.3.10" >> requirements.txt
echo "Pillow>=10.0.0" >> requirements.txt
echo "pdf2image>=1.16.3" >> requirements.txt
echo "stripe>=7.0.0" >> requirements.txt
```

### Step 2: Set Up Stripe Test Account

1. Go to https://dashboard.stripe.com/test/apikeys
2. Copy your test keys
3. Add to `.env`:
   ```bash
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   STRIPE_WEBHOOK_SECRET=whsec_...  # Will get this later
   ```

### Step 3: Create Directory Structure

```bash
mkdir -p apps/backend/app/services/ocr
mkdir -p apps/backend/app/services/payments
mkdir -p apps/backend/app/routers/ocr
mkdir -p apps/backend/uploads/documents
mkdir -p apps/backend/uploads/temp
```

### Step 4: Verify Installation

```bash
python -c "import pytesseract; print('✓ OCR ready')"
python -c "import stripe; print('✓ Stripe ready')"
tesseract --version  # Should show version
```

---

## 📋 Implementation Order

Follow this order for smooth progress:

1. **Phase 0**: Setup & Dependencies ✅ (You just did this)
2. **Phase 1**: OCR Service Foundation
3. **Phase 2**: Trip Information Extraction
4. **Phase 3**: Instant Quote from Document
5. **Phase 4**: Stripe Payment Setup
6. **Phase 5**: Payment Webhook Handler
7. **Phase 6**: Payment Status Polling
8. **Phase 7**: Frontend Integration - OCR
9. **Phase 8**: Frontend Integration - Payments
10. **Phase 9**: End-to-End Integration
11. **Phase 10**: Performance & Polish

---

## 🧪 Quick Test Commands

### Test OCR Locally:
```python
# Save as test_ocr.py
from PIL import Image
import pytesseract

# Create a simple test image or use an existing one
img = Image.open('test_image.png')
text = pytesseract.image_to_string(img)
print(text)
```

### Test Stripe Connection:
```python
# Save as test_stripe.py
import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Test connection
customers = stripe.Customer.list(limit=1)
print("✓ Stripe connected successfully")
```

---

## 📝 Next Steps

1. Open `OCR_PAYMENTS_IMPLEMENTATION_PLAN.md` for detailed phase-by-phase instructions
2. Start with Phase 1: OCR Service Foundation
3. Test each phase before moving to the next
4. Use the testing instructions in each phase

---

## 🆘 Need Help?

- Check `OCR_PAYMENTS_IMPLEMENTATION_PLAN.md` for detailed instructions
- Each phase has automated tests and human testing steps
- Common issues section at the end of the plan

**Good luck! 🚀**

