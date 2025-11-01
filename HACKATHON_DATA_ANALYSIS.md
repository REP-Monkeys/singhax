# Hackathon Resources Data Analysis

## 📊 Overview

This document provides a comprehensive analysis of all data and resources provided in the `hackathon-resources/` folder from the Ancileo × MSIG hackathon repository.

---

## 📁 Resource Structure

```
hackathon-resources/
├── README.md (Main hackathon guide)
├── Next-Generation Conversational Travel Insurance Distribution Hackathon.pdf
├── Claims_Data_DB.pdf (Historical claims data)
│
├── Payments/ (Complete payment integration system)
│   ├── docker-compose.yaml
│   ├── webhook/stripe_webhook.py
│   ├── payment_pages/app.py
│   ├── test_payment_flow.py
│   └── scripts/init_payments_table.py
│
├── Policy_Wordings/ (Insurance policy documents)
│   ├── Scootsurance QSR022206_updated.pdf
│   ├── TravelEasy Policy QTD032212.pdf
│   └── TravelEasy Pre-Ex Policy QTD032212-PX.pdf
│
├── Taxonomy/ (Policy normalization schema)
│   ├── Taxonomy_Hackathon.json (Large JSON structure)
│   └── Travel Insurance Product Taxonomy - Documentation.pdf
│
└── Hackathon_Documentation/
    ├── Travel Insurance API Documentation.pdf
    └── Scoot_SG_destination_list.xlsx
```

---

## 💳 Payments System Analysis

### **Architecture**

The payments system uses **DynamoDB Local** (not PostgreSQL) for payment record storage, with Stripe integration:

```
Stripe Checkout → Webhook Handler → DynamoDB Local → Status Updates
```

### **Key Components**

#### 1. **DynamoDB Table Schema** (`lea-payments-local`)

| Field | Type | Description |
|-------|------|-------------|
| `payment_intent_id` | String (PK) | Unique payment identifier |
| `user_id` | String | User identifier |
| `quote_id` | String | Insurance quote identifier |
| `stripe_session_id` | String | Stripe checkout session ID |
| `stripe_payment_intent` | String | Stripe payment intent ID |
| `payment_status` | String | `pending`, `completed`, `failed`, `expired` |
| `amount` | Number | Payment amount in cents |
| `currency` | String | Currency code (e.g., SGD) |
| `product_name` | String | Product description |
| `created_at` | String (ISO) | Record creation timestamp |
| `updated_at` | String (ISO) | Last update timestamp |
| `webhook_processed_at` | String (ISO) | Webhook processing timestamp |

**Indexes:**
- `user_id-index` - Query payments by user
- `quote_id-index` - Query payments by quote
- `stripe_session_id-index` - Query by Stripe session

### **2. Services Provided**

#### **Stripe Webhook Service** (Port 8086)
- **File**: `webhook/stripe_webhook.py`
- **Function**: Receives Stripe webhook events and updates DynamoDB
- **Handled Events**:
  - `checkout.session.completed` → Status: `completed`
  - `checkout.session.expired` → Status: `expired`
  - `payment_intent.payment_failed` → Status: `failed`
- **Features**:
  - Webhook signature verification
  - Error handling and logging
  - Database updates via `client_reference_id` linking

#### **Payment Pages Service** (Port 8085)
- **File**: `payment_pages/app.py`
- **Function**: Success/cancel pages after Stripe checkout
- **Endpoints**:
  - `GET /success?session_id={id}` - Success page
  - `GET /cancel` - Cancel page
- **Features**:
  - Beautiful HTML pages with animations
  - Auto-close functionality for popup windows
  - Session ID display

#### **Docker Compose Stack**
- **DynamoDB Local**: Port 8000
- **DynamoDB Admin UI**: Port 8010 (web interface)
- **Stripe Webhook**: Port 8086
- **Payment Pages**: Port 8085

### **3. Payment Flow**

```
1. Create payment record in DynamoDB (status: 'pending')
2. Create Stripe checkout session
3. Link via client_reference_id = payment_intent_id
4. User completes payment on Stripe
5. Stripe sends webhook to /webhook/stripe
6. Webhook handler updates DynamoDB (status: 'completed')
7. User redirected to success page
```

### **4. Key Differences from Your System**

⚠️ **Important**: The hackathon uses **DynamoDB** instead of PostgreSQL:
- You'll need to either:
  - **Option A**: Adapt to use DynamoDB Local (easier integration)
  - **Option B**: Port the logic to PostgreSQL (more work, but consistent with your stack)

### **5. Test Payment Flow**

The `test_payment_flow.py` provides:
- Interactive payment testing
- Creates test payment records
- Generates real Stripe checkout links
- Polls for payment completion
- Verifies webhook processing

**Test Card**: `4242 4242 4242 4242` (any future expiry, any CVC)

---

## 📄 Policy Wordings Analysis

### **Available Documents**

1. **Scootsurance QSR022206_updated.pdf**
   - Scoot airline insurance product
   - Updated version

2. **TravelEasy Policy QTD032212.pdf**
   - Standard travel insurance policy
   - General terms and conditions

3. **TravelEasy Pre-Ex Policy QTD032212-PX.pdf**
   - Pre-existing conditions policy variant
   - Specific coverage for medical pre-existing conditions

### **Usage for Block 1 (Policy Intelligence)**

These PDFs are:
- **Source documents** for extraction
- **Real insurance policies** from MSIG
- **Different products** to compare (Scootsurance vs TravelEasy)
- **Variants** (standard vs pre-existing conditions)

**Your Task**: Extract and normalize these into the taxonomy structure.

---

## 🗂️ Taxonomy Structure Analysis

### **File**: `Taxonomy_Hackathon.json`

**Structure**: Massive JSON file (5000+ lines) with normalized policy structure.

### **Top-Level Structure**

```json
{
  "taxonomy_name": "Travel Insurance Product Taxonomy",
  "products": ["Product A", "Product B", "Product C"],
  "layers": {
    "layer_1_general_conditions": [...],
    "layer_2_benefits": [...],
    "layer_3_benefit_conditions": [...],
    "layer_4_operational": [...]
  }
}
```

### **Four Layers**

#### **Layer 1: General Conditions**
- **Purpose**: Eligibility and general exclusions
- **Conditions Include**:
  - `trip_start_singapore` - Must start trip from Singapore
  - `age_eligibility` - Age restrictions
  - `good_health` - Health declaration requirements
  - `child_accompaniment_requirement` - Children must be accompanied
  - `pre_existing_conditions` - Pre-existing condition exclusions
  - `travel_advisory_exclusion` - Travel advisory restrictions
  - `awareness_of_circumstances` - Must be aware of circumstances
  - `pre_trip_purchased` - Must purchase before trip
  - `declaration_of_previous_insurance` - Previous insurance declarations

#### **Layer 2: Benefits**
- **Purpose**: Coverage details and limits
- **Benefits Include**:
  - Medical expenses
  - Trip cancellation
  - Baggage loss/theft
  - Personal accident
  - Travel delay
  - Emergency evacuation
  - And many more...

#### **Layer 3: Benefit-Specific Conditions**
- **Purpose**: Conditions specific to each benefit
- **Examples**:
  - When medical coverage applies
  - Exclusions under trip cancellation
  - Waiting periods
  - Documentation requirements

#### **Layer 4: Operational Details**
- **Purpose**: Claims procedures, deductibles, provider networks
- **Includes**:
  - Deductibles and co-pays
  - Approved provider networks
  - Claims procedures
  - Time limits

### **Product Comparison Structure**

Each condition/benefit has a structure like:

```json
{
  "condition": "age_eligibility",
  "condition_type": "eligibility",
  "products": {
    "Product A": {
      "condition_exist": true/false,
      "original_text": "Actual text from policy PDF",
      "parameters": {
        "min_age": 18,
        "max_age": 75
      }
    },
    "Product B": {...},
    "Product C": {...}
  }
}
```

### **Your Task**: 
- Extract data from Policy_Wordings PDFs
- Map to this taxonomy structure
- Compare products side-by-side
- Use for conversational Q&A

---

## 📊 Claims Data Analysis

### **File**: `Claims_Data_DB.pdf`

**Purpose**: Historical claims data for Block 5 (Predictive Intelligence)

**Contains** (based on hackathon description):
- Real claims patterns by destination
- Claim amounts for different scenarios
- Risk factors and correlations
- Seasonal trends
- Coverage gaps
- Demographic insights

**Your Task**:
- Analyze patterns in the data
- Build predictive models
- Create risk scoring
- Provide data-driven recommendations

**Example Use Case**:
```
User: "I'm going skiing in Japan"
System: "Based on historical data, 80% of medical claims for 
         Japan ski trips exceed $30,000. We recommend the 
         Silver plan with $50,000 medical coverage."
```

---

## 📚 Documentation Files

### **1. Travel Insurance API Documentation.pdf**

**Likely Contains**:
- API endpoints for insurance products
- Integration guide
- Authentication details
- Request/response formats

**Note**: The README mentions an API key available at:
```
https://pwpush.com/p/y9hg-pkgeg-bzeik/r
```

### **2. Scoot_SG_destination_list.xlsx**

**Purpose**: Destination data for quote generation
- Likely contains:
  - List of destinations
  - Geographic area classifications
  - Risk ratings by destination
  - Pricing multipliers

**Usage**: Use this for accurate destination-based pricing.

### **3. Next-Generation Conversational Travel Insurance Distribution Hackathon.pdf**

**Purpose**: Main hackathon background document
- Problem statement
- Business context
- Industry insights
- Evaluation criteria

---

## 🔑 Key Insights

### **1. Payment System Architecture**

**Hackathon Approach**:
- Uses DynamoDB Local (NoSQL)
- Separate microservices for webhook and pages
- Stateless webhook pattern

**Your Current System**:
- Uses PostgreSQL (SQL)
- Monolithic FastAPI backend
- Session-based state management

**Integration Options**:
1. **Adapt DynamoDB**: Run DynamoDB Local alongside PostgreSQL
2. **Port to PostgreSQL**: Rewrite payment logic to use your existing database
3. **Hybrid**: Use DynamoDB for payments, PostgreSQL for everything else

### **2. Policy Normalization**

**Hackathon Expectation**:
- Extract from 3 PDFs
- Normalize into taxonomy JSON structure
- Compare 3 products (Product A, B, C = Scootsurance, TravelEasy Standard, TravelEasy Pre-Ex)

**Your Current System**:
- Has RAG system (text-based search)
- No taxonomy normalization
- No policy comparison

**Gap**: Need to build taxonomy-based extraction and comparison.

### **3. Data Sources**

**Available Data**:
- ✅ 3 Policy PDFs (source documents)
- ✅ Taxonomy JSON (target structure)
- ✅ Claims data PDF (predictive intelligence)
- ✅ Destination list Excel (pricing)
- ✅ API documentation (integration guide)

**What You Need to Build**:
- OCR extraction from documents
- Taxonomy mapping logic
- Claims data analysis
- API integration (if using external API)

---

## 🎯 Action Items

### **For OCR Implementation**:
1. ✅ Study payment flow architecture
2. ✅ Understand DynamoDB schema
3. ⚠️ Decide: DynamoDB or PostgreSQL for payments?
4. ⚠️ Port webhook handler to your system

### **For Payments Implementation**:
1. ✅ Review Stripe webhook handler code
2. ✅ Understand payment status flow
3. ⚠️ Integrate with your PostgreSQL database
4. ⚠️ Create payment endpoints in FastAPI

### **For Policy Intelligence**:
1. ✅ Review taxonomy structure
2. ✅ Study policy PDFs (need to extract)
3. ⚠️ Build PDF extraction and normalization
4. ⚠️ Create comparison logic

### **For Predictive Intelligence**:
1. ✅ Identify Claims_Data_DB.pdf
2. ⚠️ Extract and analyze claims data
3. ⚠️ Build predictive models
4. ⚠️ Integrate recommendations into conversation

---

## 📝 Technical Notes

### **DynamoDB vs PostgreSQL**

**DynamoDB Advantages** (hackathon approach):
- Fast NoSQL queries
- Serverless-ready
- Built-in webhook pattern

**PostgreSQL Advantages** (your current stack):
- Consistent with existing system
- ACID transactions
- SQL queries and joins
- Already set up

**Recommendation**: Port to PostgreSQL for consistency, but study the DynamoDB schema for payment record structure.

### **Webhook Pattern**

The hackathon uses a **callback server workaround** because:
- MCP servers are stateless
- Can't receive webhooks directly
- Polling pattern needed

**Your System**: Since you're using FastAPI (not MCP), you can receive webhooks directly, making it simpler!

---

## 🚀 Next Steps

1. **Review Payment Code**: Study `stripe_webhook.py` and `test_payment_flow.py`
2. **Decide Database**: DynamoDB or PostgreSQL for payments?
3. **Start OCR**: Begin Phase 1 of OCR implementation plan
4. **Study Taxonomy**: Understand the JSON structure thoroughly
5. **Plan Integration**: How to connect payments with your existing quote system

---

**Last Updated**: January 2025
**Status**: Ready for implementation planning

