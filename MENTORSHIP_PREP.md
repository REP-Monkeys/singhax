# Mentorship Session Preparation - MSIG Insurance Specialist

## 📋 Project Summary

### **ConvoTravelInsure** - Conversational Travel Insurance Platform

**What We Built:**
A next-generation travel insurance distribution platform that uses AI-powered conversational interfaces to guide customers through insurance quotes, policy explanations, and claims guidance. Built for the SingHacks 2025 hackathon in partnership with Ancileo × MSIG.

---

## 🎯 Core Features

### 1. **Conversational Quote Generation**
- **6-step structured conversation flow** collecting:
  - Destination (country)
  - Travel dates (departure & return)
  - Traveler ages
  - Adventure sports activities
- Uses **LangGraph** for state management and multi-turn conversations
- **Natural language processing** via Groq LLM (Llama3/Mixtral)
- Persistent conversation state via PostgreSQL checkpointing

### 2. **Three-Tier Insurance Product**
- **Standard Tier** ($250K medical, $5K cancellation, $3K baggage, no adventure sports)
- **Elite Tier** ($500K medical, $12.5K cancellation, $5K baggage, adventure sports included)
- **Premier Tier** ($1M medical, $15K cancellation, $7.5K baggage, full adventure + $1M evacuation)

### 3. **Geographic Pricing Model**
- **Area A (ASEAN):** $3/day base rate (Brunei, Cambodia, Indonesia, Laos, Malaysia, Myanmar, Philippines, Thailand, Vietnam)
- **Area B (Asia-Pacific):** $5/day base rate (Australia, China, Hong Kong, India, Japan, Korea, Macau, New Zealand, Sri Lanka, Taiwan)
- **Area C (Worldwide):** $8/day base rate (all other countries)
- **Age multipliers:** Children (<18): 0.7x, Adults (18-64): 1.0x, Seniors (65-69): 1.3x, Seniors (70+): 1.5x
- **Tier multipliers:** Standard: 1.0x, Elite: 1.8x, Premier: 2.5x

### 4. **Claims Intelligence System** ⭐ **Key Innovation**
- **Real-time risk assessment** using MSIG's historical claims database (72,592 claims)
- **Data-driven tier recommendations** based on:
  - Average claim amounts by destination
  - Medical claim frequency
  - Adventure sports risk patterns
  - 95th percentile claim amounts
- **Risk scoring algorithm** (0-10 scale) considering multiple factors
- **LLM-powered narratives** explaining risk factors and recommendations
- Example: "Based on 4,188 historical claims to Japan, average medical claims are $1,358 with 95th percentile reaching $3,350. For skiing (adventure activity), we recommend Elite tier."

### 5. **Document Intelligence (OCR)**
- **Upload travel documents:** Flight confirmations, hotel bookings, itineraries, visa applications
- **Automatic information extraction** using Tesseract OCR + LLM
- **Structured data extraction** (dates, destinations, traveler info)
- **Instant quote generation** from uploaded documents

### 6. **Policy Document Search (RAG)**
- **Semantic search** across insurance policy documents
- **Citation support** for policy questions
- **Multi-document support** (Scootsurance, TravelEasy Standard, TravelEasy Pre-Ex)

### 7. **Claims Guidance**
- **Interactive claims wizard** guiding users through claim requirements
- **Document upload support** for claim evidence
- **Claim type detection** (medical, trip delay, baggage loss, etc.)

---

## 🏗️ Technical Architecture

**Backend:**
- FastAPI (Python 3.11)
- LangGraph for conversation orchestration
- PostgreSQL (Supabase) for data persistence
- Groq LLM for natural language understanding
- Tesseract OCR for document processing

**Frontend:**
- Next.js 14 (TypeScript)
- Modern chat interface with voice input support

**Key Innovation:**
- **SQL-based claims analytics** (not vector RAG) due to AWS RDS permissions
- **Hybrid approach:** SQL queries for statistical insights + LLM for narrative generation
- **30ms query performance** for real-time risk assessment

---

## 📊 Current Implementation Status

### ✅ **Completed**
- Conversational quote flow (6 questions)
- Three-tier pricing model with geographic areas
- Claims intelligence integration (MSIG claims DB)
- Document OCR and extraction
- Policy document RAG search
- Claims guidance wizard
- Risk assessment and tier recommendations

### ⚠️ **Partial / Mock**
- Payment processing (Stripe configured but not fully integrated)
- Real insurer API integration (using MockInsurerAdapter)
- Policy normalization using taxonomy (RAG search works, but taxonomy comparison not implemented)

### ❌ **Not Yet Implemented**
- MCP (Model Context Protocol) server architecture (hackathon requirement)
- Payment webhook integration
- Policy comparison using taxonomy structure
- Predictive modeling beyond risk scoring

---

## 🎯 Key Differentiators

1. **Data-Driven Recommendations:** Uses real MSIG claims data to recommend coverage tiers
2. **Conversational UX:** Natural language interaction vs. traditional form-filling
3. **Intelligent Risk Assessment:** Combines statistical analysis with LLM narratives
4. **Document Automation:** Upload documents → instant quotes
5. **Multi-Product Support:** Handles multiple MSIG products (Scootsurance, TravelEasy variants)

---

## 💡 Questions for MSIG Insurance Specialist

### **Product & Coverage Questions**

1. **Tier Recommendations:**
   - Are our three tiers (Standard/Elite/Premier) aligned with MSIG's actual product structure?
   - Should we recommend tier upgrades more conservatively, or is aggressive upselling acceptable?
   - What's the typical conversion rate from Standard → Elite/Premier in real sales?

2. **Coverage Limits:**
   - Are our coverage amounts ($250K/$500K/$1M medical) realistic for MSIG products?
   - For adventure sports, should coverage be automatically included in Elite/Premier, or is it an add-on?
   - How do pre-existing conditions affect tier eligibility in practice?

3. **Geographic Pricing:**
   - Our Area A/B/C pricing model - does this align with MSIG's actual pricing structure?
   - Are there specific high-risk destinations that should have higher multipliers?
   - How do we handle multi-country trips (e.g., Japan + Thailand)?

4. **Age-Based Pricing:**
   - Our age multipliers (children 0.7x, seniors 1.3-1.5x) - are these accurate?
   - What's the maximum age for coverage eligibility?
   - Are there different rules for children vs. adults regarding adventure sports?

### **Claims Intelligence Questions**

5. **Risk Assessment Accuracy:**
   - We're using historical claims data to score risk (0-10 scale). Is this approach valid?
   - Should we weight certain claim types more heavily (e.g., medical vs. baggage)?
   - How do you typically communicate risk to customers without scaring them away?

6. **Claims Data Interpretation:**
   - What's a "normal" average claim amount vs. concerning?
   - Should we focus on 95th percentile (worst-case) or median (typical case) for recommendations?
   - Are there seasonal patterns we should highlight (e.g., winter sports in Japan)?

7. **Tier Recommendation Logic:**
   - When should we recommend Premier vs. Elite? What's the threshold?
   - Is it ethical to recommend higher tiers based on claims data, or should we present options neutrally?
   - How do you balance customer protection vs. premium revenue?

### **Claims Process Questions**

8. **Claims Guidance:**
   - What are the most common mistakes customers make when filing claims?
   - Should we proactively guide users on claim documentation requirements during quote process?
   - How can we reduce claim rejection rates through better upfront education?

9. **Document Requirements:**
   - For medical claims, what documentation is absolutely required vs. nice-to-have?
   - How do we handle edge cases (e.g., claims for pre-existing conditions that weren't declared)?
   - Are there time limits (e.g., must file within 30 days) we should emphasize?

### **Business & Compliance Questions**

10. **Regulatory Compliance:**
    - Are there MAS (Monetary Authority of Singapore) regulations we need to comply with?
    - Do we need to provide policy summaries or cooling-off periods?
    - What disclosures are legally required during the quote process?

11. **Underwriting Considerations:**
    - Should we be checking certain risk factors before offering quotes (e.g., high-risk destinations, certain activities)?
    - Are there "uninsurable" scenarios we should detect and reject early?
    - How do we handle customers with significant pre-existing conditions?

12. **Sales & Conversion:**
    - What's the typical drop-off rate in travel insurance sales funnels?
    - At what point do customers most commonly abandon the process?
    - How can conversational AI improve conversion vs. traditional forms?

### **Technical Implementation Questions**

13. **API Integration:**
    - Does MSIG have a real-time quote API we can integrate with?
    - How do we handle quote expiration (e.g., prices valid for 7 days)?
    - Can we get real-time availability for adventure sports coverage?

14. **Policy Documents:**
    - We have 3 policy PDFs (Scootsurance, TravelEasy Standard, TravelEasy Pre-Ex). Are there other MSIG products we should support?
    - Should we normalize policies using the taxonomy structure provided, or is RAG search sufficient?
    - How often do policy wordings change, and how do we keep our system updated?

15. **Claims Database:**
    - Is the claims database we're accessing (72K claims) representative and up-to-date?
    - Should we be filtering claims differently (e.g., only closed claims, only certain claim types)?
    - Are there privacy/compliance concerns with using historical claims data for recommendations?

### **Innovation & Future Questions**

16. **AI & Automation:**
    - What manual processes in insurance could benefit most from AI automation?
    - Are there opportunities for predictive claims prevention (e.g., warning users about high-risk activities)?
    - How can we use AI to improve claim processing speed and accuracy?

17. **Customer Experience:**
    - What pain points do customers experience most with travel insurance?
    - How can conversational AI improve trust and transparency?
    - What makes customers choose one insurer over another?

18. **Competitive Landscape:**
    - How does MSIG differentiate from competitors (e.g., AIG, AXA)?
    - What features would make this platform truly innovative vs. existing solutions?
    - Are there partnerships (e.g., airlines, travel agencies) we should consider?

### **Hackathon-Specific Questions**

19. **Judging Criteria:**
    - What would impress judges most: technical innovation, business impact, or user experience?
    - Should we focus on one feature deeply or demonstrate breadth?
    - How important is it to have a fully working payment flow vs. demonstrating the concept?

20. **MSIG Priorities:**
    - What are MSIG's key business objectives for this hackathon?
    - Are they looking for solutions they can actually implement, or proof-of-concepts?
    - What would make this solution valuable to MSIG beyond the hackathon?

---

## 🎤 Talking Points / Demo Script

### **Opening (30 seconds)**
"Hi! I'm building ConvoTravelInsure, a conversational AI platform for travel insurance distribution. The key innovation is using real MSIG claims data to provide data-driven risk assessments and tier recommendations."

### **Key Demo Points (2-3 minutes)**
1. **Show conversational flow:** "User says 'I want to go skiing in Japan' → system collects trip details naturally"
2. **Show claims intelligence:** "System analyzes 4,188 historical Japan claims → identifies high medical risk → recommends Elite tier"
3. **Show document upload:** "User uploads flight confirmation → system extracts dates/destination → generates quote instantly"

### **Closing Questions (1 minute)**
"Based on your experience, what are the biggest challenges in travel insurance distribution that AI could solve? And what would make this solution truly valuable to MSIG?"

---

## 📝 Notes to Take During Session

- [ ] MSIG's actual product structure and pricing
- [ ] Regulatory requirements we need to consider
- [ ] Common customer pain points
- [ ] Claims process improvements needed
- [ ] Real-world conversion rates and drop-off points
- [ ] Technical integration possibilities
- [ ] Feedback on our risk assessment approach
- [ ] Suggestions for hackathon demo

---

**Last Updated:** Before mentorship session
**Project Status:** MVP complete, ready for feedback and refinement

