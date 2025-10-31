# Hackathon Requirements Analysis

## 🎯 Overview

This document compares your current **ConvoTravelInsure** project with the **SingHacks 2025 - Ancileo × MSIG** hackathon requirements.

---

## 🔴 CRITICAL DIFFERENCES

### 1. **MCP (Model Context Protocol) Requirement** ⚠️ **MAJOR GAP**

**Hackathon Requirement:**
- **MUST use MCP (Model Context Protocol) servers** as the core architecture
- Tools should be exposed as MCP servers
- The hackathon emphasizes MCP as the primary innovation framework
- Reference: `https://modelcontextprotocol.io/`

**Your Current Implementation:**
- ✅ Uses **LangGraph** for conversation orchestration
- ✅ Uses **LangChain** for LLM abstractions
- ❌ **NO MCP servers** - you're using LangGraph state machines directly
- ✅ Has tools (`app/agents/tools.py`) but they're LangGraph tools, not MCP servers

**What You Need:**
- Convert your tools to MCP servers
- Expose functionality via MCP protocol
- Structure your system to use MCP as the communication layer

---

### 2. **Missing Hackathon Resources** 📦

The hackathon repository provides essential resources that you need to download:

**Required Resources (not in your project):**
1. **`Payments/` folder** - Complete Stripe payment integration with webhook callback server
   - Contains Docker setup for payment flow
   - Has Stripe webhook handler
   - Includes payment status polling mechanism
   
2. **`Policy_Wordings/` folder** - Insurance policy documents
   - Used for Block 1 (Policy Intelligence)
   - Need to ingest and normalize these documents
   
3. **`Taxonomy/` folder** - Insurance taxonomy/classification system
   - Used for policy normalization and comparison
   - Critical for Block 1 requirements
   
4. **`Claims_Data_DB.pdf`** - Historical claims data
   - Required for Block 5 (Predictive Intelligence)
   - Used to build predictive models and insights

**Action Required:**
- Clone or download these folders from: `https://github.com/SingHacks-2025/ancileo-msig`
- Integrate them into your project structure

---

## 📋 Feature Block Comparison

### **Block 1: Policy Intelligence** 🧠

**Hackathon Requirements:**
- Understand and normalize insurance policy documents
- Compare policies using taxonomy
- Extract coverage details and present comparisons
- Handle policy wordings from `Policy_Wordings/` folder
- Use taxonomy from `Taxonomy/` folder

**Your Current Implementation:**
- ✅ Has RAG system (`app/services/rag.py`)
- ✅ Document ingestion and chunking
- ✅ Policy search functionality
- ⚠️ Text-based search (vector search pending)
- ❌ **Missing**: Policy normalization using taxonomy
- ❌ **Missing**: Policy comparison capabilities
- ❌ **Missing**: Integration with provided policy wordings
- ❌ **Missing**: Taxonomy-based classification

**Gap Analysis:**
- You have the foundation (RAG) but need taxonomy integration
- Need to download and use `Policy_Wordings/` and `Taxonomy/` folders
- Need to build policy comparison logic

---

### **Block 2: Conversational Magic** 💬

**Hackathon Requirements:**
- Natural, engaging conversation flow
- Personality and trust-building
- Citation of policy documents
- Smooth multi-turn conversations

**Your Current Implementation:**
- ✅ LangGraph conversation state machine
- ✅ Multi-turn conversation support
- ✅ LLM-based intent detection
- ✅ Policy citations in RAG responses
- ✅ Natural language information extraction
- ✅ 6-step structured flow

**Gap Analysis:**
- ✅ **Mostly Complete** - You have a solid conversational system
- Could enhance personality/trust-building aspects
- Consider adding more engaging conversation patterns

---

### **Block 3: Document Intelligence** 📄

**Hackathon Requirements:**
- OCR extraction from travel documents
- Upload flight confirmations, itineraries, hotel bookings
- Extract trip information automatically
- Generate instant quotes from documents

**Your Current Implementation:**
- ✅ Planned feature (documented in `CODEBASE_SUMMARY_FOR_CLAUDE.md`)
- ✅ Technical approach identified (Tesseract OCR)
- ❌ **NOT IMPLEMENTED** - Still in planning phase
- ❌ No document upload endpoint
- ❌ No OCR service

**Gap Analysis:**
- This is a **critical missing feature**
- Need to implement OCR service
- Need document upload endpoint
- Need LLM-assisted extraction from OCR text

---

### **Block 4: Commerce (Payments)** 💳

**Hackathon Requirements:**
- Stripe payment integration
- In-chat payment experience
- Payment status updates
- Policy delivery after purchase
- Use provided `Payments/` folder with callback server

**Your Current Implementation:**
- ✅ Stripe configured in environment variables
- ✅ Policy creation endpoint exists (`app/routers/policies.py`)
- ❌ **Payment processing NOT implemented**
- ❌ No Stripe checkout session creation
- ❌ No payment status tracking
- ❌ **Missing**: `Payments/` folder integration
- ❌ No MCP purchase tool

**Gap Analysis:**
- **Critical Missing Feature**
- Need to download `Payments/` folder from hackathon repo
- Need to integrate Stripe checkout
- Need to create MCP purchase tool
- Need payment status polling (as suggested in hackathon)

---

### **Block 5: Predictive Intelligence** 🎯

**Hackathon Requirements:**
- Use historical claims data (`Claims_Data_DB.pdf`)
- Build predictive models
- Provide risk insights based on patterns
- Recommend coverage based on historical data
- Analyze seasonal patterns, demographic insights

**Your Current Implementation:**
- ✅ Risk assessment logic (`app/services/pricing.py`)
- ✅ Age-based, activity-based, destination-based risk factors
- ❌ **NO historical claims data integration**
- ❌ **Missing**: `Claims_Data_DB.pdf` file
- ❌ No predictive models
- ❌ No data-driven insights

**Gap Analysis:**
- **Critical Missing Feature**
- Need to download `Claims_Data_DB.pdf`
- Need to analyze and integrate claims data
- Need to build predictive models
- Need to add data-driven recommendations

---

## 🏗️ Architecture Differences

### **Hackathon Architecture (Expected):**
```
User → AI Chat Interface
         ↓
    MCP Client
         ↓
    MCP Servers (Tools)
    ├── Policy Intelligence MCP Server
    ├── Document Intelligence MCP Server
    ├── Payment MCP Server
    ├── Predictive Intelligence MCP Server
    └── Conversational Tools MCP Server
```

### **Your Current Architecture:**
```
User → Next.js Frontend
         ↓
    FastAPI Backend
         ↓
    LangGraph State Machine
         ↓
    LangGraph Tools (not MCP)
    ├── Pricing Service
    ├── RAG Service
    ├── Claims Service
    └── Handoff Service
```

**Key Difference:**
- Hackathon expects **MCP servers** as the primary integration pattern
- You're using **LangGraph directly** without MCP abstraction layer

---

## ✅ What You Have That's Good

1. **Solid Foundation:**
   - ✅ Working conversational AI system
   - ✅ LangGraph state machine for conversation flow
   - ✅ Database models and persistence
   - ✅ Frontend chat interface
   - ✅ Authentication system

2. **Block 2 Implementation:**
   - ✅ Good conversational flow
   - ✅ Multi-turn conversations
   - ✅ Natural language extraction

3. **Infrastructure:**
   - ✅ FastAPI backend
   - ✅ PostgreSQL database
   - ✅ Docker setup
   - ✅ Testing framework

---

## ❌ Critical Missing Components

### **1. MCP Server Implementation** 🔴 **HIGHEST PRIORITY**
- Convert LangGraph tools to MCP servers
- Implement MCP protocol endpoints
- Structure system around MCP architecture

### **2. Missing Resources** 🔴 **HIGH PRIORITY**
- Download `Payments/` folder
- Download `Policy_Wordings/` folder
- Download `Taxonomy/` folder
- Download `Claims_Data_DB.pdf`

### **3. Feature Gaps** 🔴 **HIGH PRIORITY**
- **Block 3**: OCR/Document Intelligence (not implemented)
- **Block 4**: Payment processing (not implemented)
- **Block 5**: Predictive Intelligence (not implemented)
- **Block 1**: Policy normalization/comparison (partial)

---

## 🎯 Recommended Action Plan

### **Phase 1: Download Resources** (30 minutes)
1. Clone/download hackathon repository
2. Copy `Payments/`, `Policy_Wordings/`, `Taxonomy/` folders
3. Copy `Claims_Data_DB.pdf`
4. Study the provided payment integration architecture

### **Phase 2: MCP Conversion** (2-4 hours)
1. Research MCP protocol: `https://modelcontextprotocol.io/`
2. Convert existing tools to MCP servers
3. Implement MCP endpoints
4. Test MCP integration

### **Phase 3: Implement Missing Features** (4-8 hours)
1. **Block 3**: Implement OCR service
   - Add Tesseract OCR
   - Create document upload endpoint
   - Extract trip info from documents
   
2. **Block 4**: Integrate payment system
   - Integrate `Payments/` folder
   - Create MCP purchase tool
   - Implement payment status tracking
   
3. **Block 5**: Add predictive intelligence
   - Analyze `Claims_Data_DB.pdf`
   - Build predictive models
   - Add data-driven recommendations

4. **Block 1**: Enhance policy intelligence
   - Integrate taxonomy
   - Add policy comparison
   - Normalize policy documents

### **Phase 4: Innovation & Polish** (2-4 hours)
1. Add unique features beyond requirements
2. Enhance UX and conversation flow
3. Add citations and trust-building elements
4. Test end-to-end flows

---

## 📊 Scoring Implications

Based on hackathon judging criteria:

| Criteria | Weight | Your Status | Impact |
|----------|--------|-------------|--------|
| **Innovation & Creativity** | 30% | ⚠️ Partial | Need MCP innovation |
| **Technical Excellence** | 25% | ⚠️ Partial | Need MCP implementation |
| **User Experience** | 20% | ✅ Good | Solid conversational flow |
| **Business Impact** | 15% | ⚠️ Partial | Need predictive insights |
| **Feasibility** | 10% | ✅ Good | Well-structured codebase |

**Key Risks:**
- **MCP requirement not met** → Could significantly impact scoring
- **Missing 3 of 5 feature blocks** → Incomplete submission
- **Missing provided resources** → Not using hackathon assets

---

## 🚀 Quick Wins

1. **Download resources immediately** - No coding required
2. **Study MCP protocol** - Understand the architecture pattern
3. **Integrate Payments folder** - Already has working code
4. **Add OCR service** - You have the plan, just need implementation

---

## 📝 Next Steps

1. **Download hackathon resources:**
   ```bash
   git clone https://github.com/SingHacks-2025/ancileo-msig.git
   # Copy Payments/, Policy_Wordings/, Taxonomy/ folders
   # Copy Claims_Data_DB.pdf
   ```

2. **Research MCP:**
   - Visit: https://modelcontextprotocol.io/
   - Understand MCP server architecture
   - Plan conversion strategy

3. **Prioritize implementation:**
   - Start with MCP conversion (most critical)
   - Then add missing features
   - Finally, enhance with innovation

---

## 💡 Innovation Opportunities

Even though you're missing some requirements, you have opportunities to innovate:

1. **Better MCP Integration:**
   - Create innovative MCP server patterns
   - Build seamless tool orchestration

2. **Enhanced Conversational Flow:**
   - Add personality and emotional intelligence
   - Build trust through transparency

3. **Predictive Intelligence:**
   - Use claims data creatively
   - Build novel recommendation engines

4. **Payment Innovation:**
   - In-chat payment experience
   - Real-time status updates

---

**Remember:** The hackathon emphasizes **innovation first**. While you need to meet requirements, creativity and novel approaches can still win even with gaps in implementation.

