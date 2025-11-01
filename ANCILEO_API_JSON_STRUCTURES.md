# Ancileo API JSON Structures

This document details the JSON request and response structures for the Ancileo MSIG Travel Insurance API.

---

## 📋 Table of Contents

1. [Quotation API](#quotation-api)
2. [Purchase API](#purchase-api)
3. [Field Requirements](#field-requirements)
4. [Response Structures](#response-structures)

---

## 🔍 Quotation API

**Endpoint:** `POST /v1/travel/front/pricing`  
**Purpose:** Get insurance quotes for a trip

### Request Structure

```json
{
  "market": "SG",
  "languageCode": "en",
  "channel": "white-label",
  "deviceType": "DESKTOP",
  "context": {
    "tripType": "RT",  // "RT" (round trip) or "ST" (single trip)
    "departureDate": "2025-03-15",  // YYYY-MM-DD format
    "departureCountry": "SG",  // ISO 2-letter country code (uppercase)
    "arrivalCountry": "JP",  // ISO 2-letter country code (uppercase)
    "adultsCount": 2,  // Must be >= 1
    "childrenCount": 0,  // Optional, default: 0
    "returnDate": "2025-03-22"  // YYYY-MM-DD format (REQUIRED for RT, OMIT for ST)
  }
}
```

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market` | string | ✅ Yes | Fixed: `"SG"` (Singapore market) |
| `languageCode` | string | ✅ Yes | Fixed: `"en"` (English) |
| `channel` | string | ✅ Yes | Fixed: `"white-label"` |
| `deviceType` | string | ✅ Yes | Fixed: `"DESKTOP"` |
| `context.tripType` | string | ✅ Yes | `"RT"` (round trip) or `"ST"` (single trip) |
| `context.departureDate` | string | ✅ Yes | Date in `YYYY-MM-DD` format (must be future date) |
| `context.departureCountry` | string | ✅ Yes | ISO 2-letter country code (e.g., `"SG"`) |
| `context.arrivalCountry` | string | ✅ Yes | ISO 2-letter country code (e.g., `"JP"`) |
| `context.adultsCount` | integer | ✅ Yes | Number of adult travelers (must be >= 1) |
| `context.childrenCount` | integer | ❌ No | Number of child travelers (default: 0) |
| `context.returnDate` | string | ⚠️ Conditional | Required for `RT`, omit for `ST` |

### Example: Round Trip Request

```json
{
  "market": "SG",
  "languageCode": "en",
  "channel": "white-label",
  "deviceType": "DESKTOP",
  "context": {
    "tripType": "RT",
    "departureDate": "2025-03-15",
    "departureCountry": "SG",
    "arrivalCountry": "JP",
    "adultsCount": 2,
    "childrenCount": 0,
    "returnDate": "2025-03-22"
  }
}
```

### Example: Single Trip Request

```json
{
  "market": "SG",
  "languageCode": "en",
  "channel": "white-label",
  "deviceType": "DESKTOP",
  "context": {
    "tripType": "ST",
    "departureDate": "2025-03-15",
    "departureCountry": "SG",
    "arrivalCountry": "JP",
    "adultsCount": 1,
    "childrenCount": 0
  }
}
```

**Note:** `returnDate` is **omitted** for single trip (`ST`).

---

## 💳 Purchase API

**Endpoint:** `POST /v1/travel/front/purchase`  
**Purpose:** Complete insurance policy purchase  
**⚠️ CRITICAL:** Only call this AFTER payment has been confirmed via Stripe webhook.

### Request Structure

```json
{
  "market": "SG",
  "languageCode": "en",
  "channel": "white-label",
  "quoteId": "f7562de0-b914-4f2c-8d5e-cb7a2519b869",
  "purchaseOffers": [
    {
      "productType": "travel-insurance",
      "offerId": "2b7e6ccb-67cd-49e6-880f-3d861c853945",
      "productCode": "SG_AXA_SCOOT_COMP",
      "unitPrice": 51.21,
      "currency": "SGD",
      "quantity": 1,
      "totalPrice": 51.21,
      "isSendEmail": true
    }
  ],
  "insureds": [
    {
      "id": "1",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com"
    }
  ],
  "mainContact": {
    "id": "1",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
  }
}
```

### Required Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `market` | string | ✅ Yes | Fixed: `"SG"` |
| `languageCode` | string | ✅ Yes | Fixed: `"en"` |
| `channel` | string | ✅ Yes | Fixed: `"white-label"` |
| `quoteId` | string | ✅ Yes | Quote ID from quotation response |
| `purchaseOffers` | array | ✅ Yes | Array with single offer object |
| `purchaseOffers[].productType` | string | ✅ Yes | Fixed: `"travel-insurance"` |
| `purchaseOffers[].offerId` | string | ✅ Yes | Offer ID from quotation response |
| `purchaseOffers[].productCode` | string | ✅ Yes | Product code from quotation response |
| `purchaseOffers[].unitPrice` | number | ✅ Yes | Exact unit price from quotation (do not modify) |
| `purchaseOffers[].currency` | string | ✅ Yes | Fixed: `"SGD"` |
| `purchaseOffers[].quantity` | integer | ✅ Yes | Usually `1` |
| `purchaseOffers[].totalPrice` | number | ✅ Yes | `unitPrice * quantity` |
| `purchaseOffers[].isSendEmail` | boolean | ✅ Yes | `true` to auto-send policy email |
| `insureds` | array | ✅ Yes | Array of traveler objects (at least 1) |
| `mainContact` | object | ✅ Yes | Main contact information |

---

## 👥 Traveler Data Structures

### Minimal Required Structure (Tested & Working ✅)

**Important Discovery:** Documentation claims many fields are required, but testing shows only 4 fields per traveler are actually required!

#### Minimal Insured (Traveler)

```json
{
  "id": "1",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com"
}
```

#### Minimal Main Contact

```json
{
  "id": "1",
  "firstName": "John",
  "lastName": "Doe",
  "email": "john@example.com"
}
```

**Tested Result:** ✅ Policy successfully issued with only these 4 fields!

---

### Full Structure (Optional Fields)

You can include additional fields for enhanced service, but they are **not required** for policy issuance.

#### Full Insured Object

```json
{
  "id": "1",  // ✅ REQUIRED - Unique identifier (e.g., "1", "2", "3")
  "title": "Mr",  // ❌ OPTIONAL - "Mr", "Ms", "Mrs", "Dr"
  "firstName": "John",  // ✅ REQUIRED - Given name
  "lastName": "Doe",  // ✅ REQUIRED - Family name
  "nationality": "SG",  // ❌ OPTIONAL - ISO 2-letter country code
  "dateOfBirth": "2000-01-01",  // ❌ OPTIONAL - YYYY-MM-DD format
  "passport": "E1234567",  // ❌ OPTIONAL - Passport number
  "email": "john@example.com",  // ✅ REQUIRED - Valid email address
  "phoneType": "mobile",  // ❌ OPTIONAL - "mobile", "home", "work"
  "phoneNumber": "6581234567",  // ❌ OPTIONAL - Phone number
  "relationship": "main"  // ❌ OPTIONAL - "main", "spouse", "child", etc.
}
```

#### Full Main Contact Object

```json
{
  "id": "1",  // ✅ REQUIRED
  "title": "Mr",  // ❌ OPTIONAL
  "firstName": "John",  // ✅ REQUIRED
  "lastName": "Doe",  // ✅ REQUIRED
  "nationality": "SG",  // ❌ OPTIONAL
  "dateOfBirth": "2000-01-01",  // ❌ OPTIONAL
  "passport": "E1234567",  // ❌ OPTIONAL
  "email": "john@example.com",  // ✅ REQUIRED
  "phoneType": "mobile",  // ❌ OPTIONAL
  "phoneNumber": "6581234567",  // ❌ OPTIONAL
  "relationship": "main",  // ❌ OPTIONAL
  "address": "123 Orchard Road",  // ❌ OPTIONAL - Street address
  "city": "Singapore",  // ❌ OPTIONAL - City name
  "zipCode": "238858",  // ❌ OPTIONAL - Postal/ZIP code
  "countryCode": "SG"  // ❌ OPTIONAL - ISO 2-letter country code
}
```

---

## 📊 Field Requirements Summary

### Insureds Array (Travelers)

| Field | Required | Notes |
|-------|----------|-------|
| `id` | ✅ **YES** | Unique identifier (string) |
| `firstName` | ✅ **YES** | Given name |
| `lastName` | ✅ **YES** | Family name |
| `email` | ✅ **YES** | Valid email address |
| `title` | ❌ No | Optional title (Mr/Ms/Mrs/Dr) |
| `nationality` | ❌ No | Optional ISO country code |
| `dateOfBirth` | ❌ No | Optional YYYY-MM-DD date |
| `passport` | ❌ No | Optional passport number |
| `phoneType` | ❌ No | Optional phone type |
| `phoneNumber` | ❌ No | Optional phone number |
| `relationship` | ❌ No | Optional relationship |

### Main Contact Object

| Field | Required | Notes |
|-------|----------|-------|
| `id` | ✅ **YES** | Unique identifier (must match an insured) |
| `firstName` | ✅ **YES** | Given name |
| `lastName` | ✅ **YES** | Family name |
| `email` | ✅ **YES** | Valid email address |
| `title` | ❌ No | Optional title |
| `nationality` | ❌ No | Optional ISO country code |
| `dateOfBirth` | ❌ No | Optional YYYY-MM-DD date |
| `passport` | ❌ No | Optional passport number |
| `phoneType` | ❌ No | Optional phone type |
| `phoneNumber` | ❌ No | Optional phone number |
| `relationship` | ❌ No | Optional relationship |
| `address` | ❌ No | Optional street address |
| `city` | ❌ No | Optional city name |
| `zipCode` | ❌ No | Optional postal code |
| `countryCode` | ❌ No | Optional ISO country code |

---

## 📥 Response Structures

### Quotation API Response

**Raw API Response:**
```json
{
  "id": "f7562de0-b914-4f2c-8d5e-cb7a2519b869",
  "offerCategories": [
    {
      "productType": "travel-insurance",
      "offers": [
        {
          "id": "2b7e6ccb-67cd-49e6-880f-3d861c853945",
          "productCode": "SG_AXA_SCOOT_COMP",
          "unitPrice": 51.21,
          "currency": "SGD",
          "coverageDetails": {
            "medicalExpenses": 1000000,
            "tripCancellation": 50000,
            "baggageLoss": 5000
          }
        }
      ]
    }
  ]
}
```

**Normalized Response (from client):**
```json
{
  "quoteId": "f7562de0-b914-4f2c-8d5e-cb7a2519b869",
  "offers": [
    {
      "offerId": "2b7e6ccb-67cd-49e6-880f-3d861c853945",
      "productCode": "SG_AXA_SCOOT_COMP",
      "productType": "travel-insurance",
      "unitPrice": 51.21,
      "currency": "SGD",
      "coverageDetails": {
        "medicalExpenses": 1000000,
        "tripCancellation": 50000,
        "baggageLoss": 5000
      }
    }
  ],
  "_raw_response": { ... }  // Original API response preserved
}
```

### Purchase API Response

```json
{
  "policyId": "7415638f-7821-44dd-aa90-26ab4f14026b",
  "policyNumber": "POL-2025-123456",
  "status": "active",
  "effectiveDate": "2025-03-15",
  "expiryDate": "2025-03-22",
  "premium": 51.21,
  "currency": "SGD",
  "coverage": {
    "medicalExpenses": 1000000,
    "tripCancellation": 50000,
    "baggageLoss": 5000
  }
}
```

---

## 💡 Implementation Examples

### Python: Get Quotation

```python
from datetime import date
from app.adapters.insurer.ancileo_client import AncileoClient

client = AncileoClient()

# Round trip example
response = client.get_quotation(
    trip_type="RT",
    departure_date=date(2025, 3, 15),
    return_date=date(2025, 3, 22),
    departure_country="SG",
    arrival_country="JP",
    adults_count=2,
    children_count=0
)

quote_id = response["quoteId"]
offers = response["offers"]
first_offer = offers[0]

# Store for purchase
offer_id = first_offer["offerId"]
product_code = first_offer["productCode"]
unit_price = first_offer["unitPrice"]
```

### Python: Create Purchase (Minimal Data)

```python
from app.adapters.insurer.ancileo_client import AncileoClient

client = AncileoClient()

# Minimal traveler data (only 4 required fields)
insureds = [{
    "id": "1",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
}]

main_contact = {
    "id": "1",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
}

# Create purchase
response = client.create_purchase(
    quote_id="f7562de0-b914-4f2c-8d5e-cb7a2519b869",
    offer_id="2b7e6ccb-67cd-49e6-880f-3d861c853945",
    product_code="SG_AXA_SCOOT_COMP",
    unit_price=51.21,
    insureds=insureds,
    main_contact=main_contact
)

policy_id = response["policyId"]
```

### Python: Create Purchase (Full Data)

```python
insureds = [{
    "id": "1",
    "title": "Mr",
    "firstName": "John",
    "lastName": "Doe",
    "nationality": "SG",
    "dateOfBirth": "2000-01-01",
    "passport": "E1234567",
    "email": "john@example.com",
    "phoneType": "mobile",
    "phoneNumber": "6581234567",
    "relationship": "main"
}]

main_contact = {
    "id": "1",
    "title": "Mr",
    "firstName": "John",
    "lastName": "Doe",
    "nationality": "SG",
    "dateOfBirth": "2000-01-01",
    "passport": "E1234567",
    "email": "john@example.com",
    "phoneType": "mobile",
    "phoneNumber": "6581234567",
    "relationship": "main",
    "address": "123 Orchard Road",
    "city": "Singapore",
    "zipCode": "238858",
    "countryCode": "SG"
}

response = client.create_purchase(
    quote_id=quote_id,
    offer_id=offer_id,
    product_code=product_code,
    unit_price=unit_price,
    insureds=insureds,
    main_contact=main_contact
)
```

### Multi-Traveler Example

```json
{
  "insureds": [
    {
      "id": "1",
      "firstName": "John",
      "lastName": "Doe",
      "email": "john@example.com"
    },
    {
      "id": "2",
      "firstName": "Jane",
      "lastName": "Doe",
      "email": "jane@example.com"
    },
    {
      "id": "3",
      "firstName": "Alice",
      "lastName": "Doe",
      "email": "john@example.com"  // Can reuse parent's email
    }
  ],
  "mainContact": {
    "id": "1",
    "firstName": "John",
    "lastName": "Doe",
    "email": "john@example.com"
  }
}
```

---

## ⚠️ Important Notes

### Quotation API

1. **Trip Type Handling:**
   - For `RT` (round trip): **MUST** include `returnDate` in context
   - For `ST` (single trip): **MUST NOT** include `returnDate` in context

2. **Date Validation:**
   - `departureDate` must be in the future
   - `returnDate` (if provided) must be after `departureDate`

3. **Country Codes:**
   - Use ISO 2-letter country codes (e.g., `"SG"`, `"JP"`)
   - Codes are automatically uppercased by the client

4. **Quote Expiration:**
   - Quotes expire after 24 hours
   - Use quote immediately or get a new one

### Purchase API

1. **Payment Timing:**
   - ⚠️ **CRITICAL:** Only call purchase API AFTER payment is confirmed via Stripe webhook
   - Do not call purchase API before payment completion

2. **Quote Usage:**
   - Use exact `quoteId`, `offerId`, `productCode`, and `unitPrice` from quotation response
   - Do not modify prices or IDs

3. **Minimal Data:**
   - Only 4 fields per traveler are actually required (tested):
     - `id`
     - `firstName`
     - `lastName`
     - `email`
   - All other fields are optional

4. **Main Contact:**
   - Must match one of the insureds (same `id`)
   - Can use same minimal structure as insureds

5. **Errors:**
   - Empty `insureds` array → HTTP 500 error
   - Expired quote → HTTP 404 error
   - Invalid API key → HTTP 401 error

---

## 🔗 Related Files

- **Client Implementation:** `apps/backend/app/adapters/insurer/ancileo_client.py`
- **Adapter:** `apps/backend/app/adapters/insurer/ancileo_adapter.py`
- **Schemas:** `apps/backend/app/schemas/traveler_details.py`
- **Test Results:** `apps/backend/ANCILEO_PURCHASE_API_FINDINGS.md`

---

## 📝 Summary

### Quotation Request (Minimal)
- 7 required fields in `context` object
- Fixed values for `market`, `languageCode`, `channel`, `deviceType`

### Purchase Request (Minimal)
- Only 4 fields per traveler: `id`, `firstName`, `lastName`, `email`
- Same 4 fields for `mainContact`
- Quote/offer data from quotation response

### Benefits of Minimal Approach
- ✅ No complex forms needed
- ✅ Can use logged-in user data
- ✅ Real policies issued immediately
- ✅ Better conversion rates
- ✅ Simplified user experience

