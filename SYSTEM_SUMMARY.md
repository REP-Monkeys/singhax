# Travel Insurance Chatbot System - Comprehensive Summary

## System Overview

This is a travel insurance quote chatbot system built with **LangGraph**, **FastAPI**, and **PostgreSQL**. The system uses an LLM-powered conversation graph to collect trip information through a structured 6-question flow, then generates insurance quotes.

**Tech Stack:**
- Backend: FastAPI (Python), LangGraph, Groq LLM, SQLAlchemy, PostgreSQL (Supabase)
- Frontend: Next.js (TypeScript) - not covered in this summary
- State Persistence: PostgreSQL checkpointing via LangGraph

## Architecture

### Core Components

1. **Chat Router** (`apps/backend/app/routers/chat.py`)
   - Main endpoint: `POST /api/v1/chat/message`
   - Handles user messages and session management
   - Invokes LangGraph conversation graph with session-based checkpointing

2. **LangGraph Conversation Graph** (`apps/backend/app/agents/graph.py`)
   - State machine with conditional routing
   - 8 nodes: orchestrator, needs_assessment, risk_assessment, pricing, policy_explainer, claims_guidance, compliance, customer_service
   - PostgreSQL-backed checkpointing for conversation persistence

3. **LLM Client** (`apps/backend/app/agents/llm_client.py`)
   - Uses Groq LLM for intent classification and information extraction
   - Function calling for structured data extraction

4. **Pricing Service** (`apps/backend/app/services/pricing.py`)
   - Calculates insurance quotes based on trip details
   - Multiple tiers: Standard, Elite, Premier

## Conversation Flow - Quote Generation Path

### Step-by-Step Flow

1. **Initial Message** → Orchestrator classifies intent as "quote"

2. **Needs Assessment** → Collects 4 required fields:
   - Destination (country name)
   - Departure date (YYYY-MM-DD or flexible formats)
   - Return date (YYYY-MM-DD or flexible formats)
   - Travelers (ages as integers)

3. **Adventure Sports Question** → Asked AFTER all 4 required fields are collected:
   - Question: "Are you planning any adventure activities like skiing, scuba diving, trekking, or bungee jumping?"
   - Accepts: yes/no or various affirmative/negative phrases

4. **Confirmation** → Shows summary and asks user to confirm:
   ```
   Let me confirm your trip details:
   📍 Destination: France
   📅 Travel dates: December 20, 2025 to January 03, 2026 (15 days)
   👥 Travelers: 1 traveler(s) (ages: 20)
   🏔️ Adventure activities: Yes/No
   Is this information correct? (yes/no)
   ```

5. **Risk Assessment** → Maps destination to geographic area for pricing

6. **Pricing** → Generates quotes (Standard, Elite, Premier)

### Question Order

The system asks questions in this order:
1. Destination (if missing)
2. Departure date (if missing)
3. Return date (if missing)
4. Travelers/ages (if missing)
5. **Adventure sports** (asked AFTER all required fields are present)
6. Confirmation (asked AFTER adventure sports is answered)

**Key Point:** Adventure sports question is asked BEFORE confirmation, but only after all 4 required fields are collected.

## State Management

### ConversationState Structure

```python
{
    "messages": List[BaseMessage],           # Conversation history
    "user_id": str,                          # UUID of user
    "session_id": str,                       # UUID of chat session
    "current_intent": str,                   # "quote", "policy_explanation", etc.
    "trip_details": {                        # Required fields
        "destination": str,
        "departure_date": date,
        "return_date": date,
        "area": str,                         # Set in risk_assessment
        "base_rate": float                   # Set in risk_assessment
    },
    "travelers_data": {
        "ages": List[int],                   # e.g., [30, 32]
        "count": int                         # Length of ages
    },
    "preferences": {
        "adventure_sports": bool | None      # True, False, or None (not asked yet)
    },
    "current_question": str,                  # "destination", "departure_date", "return_date", "travelers", "adventure_sports", "confirmation", or ""
    "awaiting_confirmation": bool,            # True when showing confirmation
    "confirmation_received": bool,            # True when user confirms
    "quote_data": Dict[str, Any],             # Generated quotes
    "trip_id": str,                          # Database trip ID
    # Internal flags
    "_loop_count": int,                      # Prevents infinite loops
    "_ready_for_pricing": bool,              # Flag for pricing flow
    "_pricing_complete": bool                # Flag when quote is generated
}
```

### State Persistence

- Uses **PostgreSQL checkpointing** via LangGraph's PostgresSaver
- Each session has a unique `thread_id` (UUID)
- State is automatically saved after each node execution
- Supports multi-turn conversations with full history

## Information Extraction Logic

### How Extraction Works

1. **LLM Extraction** (`llm_client.extract_trip_info()`)
   - Uses Groq LLM with function calling
   - Extracts: destination, departure_date, return_date, travelers_ages, adventure_sports
   - Returns dictionary with extracted fields (empty if nothing extracted)

2. **Field Updates** (in `needs_assessment` function)
   - Updates state only if field is in extracted dictionary
   - Validates dates, ages, etc.
   - Creates/updates database Trip record when destination is extracted

3. **Special Handling for Adventure Sports**

   The adventure sports field has **complex logic** to prevent premature extraction:

   **Lines 369-407:** Adventure Sports Extraction Logic
   
   ```python
   if "adventure_sports" in extracted:
       # Only accept if:
       # 1. We're asking the adventure question (current_q == "adventure_sports"), OR
       # 2. User explicitly mentions adventure keywords
       
       if current_q == "adventure_sports":
           # Validate extraction against user's yes/no input
           # If LLM extracts opposite of what user said, reject extraction
           # (e.g., user says "yes" but LLM extracts False → reject)
   ```

   **Lines 414-439:** Fallback Keyword Parsing
   
   ```python
   # If LLM didn't extract or we rejected extraction, parse keywords
   if current_q == "adventure_sports" and not extracted_info:
       # Check for positive keywords: "yes", "i am", "i will", "absolutely", etc.
       # Check for negative keywords: "no", "i'm not", "absolutely not", etc.
   ```

   **Key Rules:**
   - Adventure sports is **only extracted** when we're asking that question OR user mentions adventure keywords
   - This prevents LLM from inferring `False` when user provides other info
   - Supports expanded keyword matching for natural responses like "i am", "i will", "i'm planning"

### Positive Keywords (for "yes" to adventure)

```python
["yes", "yeah", "yep", "sure", "probably", "i am", "i'm", "i will", "i'll", 
 "i do", "absolutely", "definitely", "i plan", "i'm planning", "i will be",
 "i am planning", "i do plan", "of course", "certainly", "definitely yes",
 "i would", "i'd like", "i want", "planning to", "going to"]
```

### Negative Keywords (for "no" to adventure)

```python
["no", "nope", "not", "none", "nah", "i'm not", "i am not", "i won't", 
 "i will not", "i don't", "i do not", "absolutely not", "definitely not", 
 "no way", "nothing"]
```

## Flow Control Logic

### Decision Tree (in `needs_assessment` function)

After extraction, the system determines what to do next:

**Lines 521-590:** Response Generation Logic

```python
# Priority 1: If adventure answered AND all required present → Confirmation
if all_required_present and adventure_answered:
    → Show confirmation summary

# Priority 2: If all required present but adventure NOT answered → Ask adventure
elif all_required_present and adventure_sports is None:
    → Ask adventure sports question

# Priority 3: If required fields missing → Ask for missing field
elif missing:
    → Ask for destination/departure_date/return_date/travelers (in order)

# Priority 4: Fallback confirmation (shouldn't happen)
elif all_required_present:
    → Show confirmation (sets adventure_sports = False if None)
```

**Critical Flow:**
1. User provides all 4 required fields → `all_required_present = True`, `adventure_sports = None`
2. System asks adventure question → `current_question = "adventure_sports"`
3. User answers "yes" or "i am" → System extracts/parses → `adventure_sports = True/False`, `extracted_info = True`
4. Next iteration: `adventure_answered = True` → Goes directly to confirmation (Priority 1)
5. User confirms → `confirmation_received = True`, `_ready_for_pricing = True`
6. System routes to risk_assessment → pricing → END

## Recent Fixes (Adventure Sports Question)

### Problem 1: Question Not Being Asked
**Issue:** Adventure sports question was skipped and system went straight to confirmation.

**Root Cause:** LLM was extracting `adventure_sports: False` prematurely from messages that didn't mention adventure activities (e.g., when user provided destination, dates, travelers).

**Fix:** 
- Lines 369-407: Only accept `adventure_sports` extraction when:
  1. We're currently asking the adventure question (`current_q == "adventure_sports"`), OR
  2. User explicitly mentions adventure keywords
- This prevents premature extraction that pollutes state

### Problem 2: Answer Not Being Captured
**Issue:** When user said "yes" or "i am", the answer wasn't captured correctly.

**Root Causes:**
1. "i am" wasn't recognized as affirmative response
2. Special handling block only ran when `extracted == {}`, but if LLM extracted other things, it wouldn't catch yes/no

**Fixes:**
- Lines 382-384, 424-427: Expanded positive/negative keyword lists to include "i am", "i'm", "i will", "i'm planning", etc.
- Line 418: Changed condition from `extracted == {}` to just `not extracted_info`, so special handling runs even if LLM extracted other fields
- Lines 379-401: Added validation to check if LLM extraction conflicts with user's explicit yes/no

### Problem 3: Wrong Flow After Answering
**Issue:** After answering adventure question, system asked "Where are you traveling to?" instead of going to confirmation.

**Root Cause:** Flow control didn't prioritize "adventure answered" case.

**Fix:**
- Lines 525-555: Added Priority 1 check that goes directly to confirmation if `adventure_answered` and `all_required_present`

## Database Integration

### Trip Model
- Created when user provides destination
- Updated with dates, travelers_count as they're collected
- Linked via `session_id` to chat session
- Status: "draft" during quote flow

### Chat History
- Stored via LangGraph checkpointing in PostgreSQL
- Each message (user + AI) preserved in `messages` array
- Full conversation state persisted per session

## Error Handling

### Loop Protection
- `_loop_count` prevents infinite loops (>20 iterations → human handoff)
- Clear exit conditions for each node
- State flags (`_ready_for_pricing`, `_pricing_complete`) prevent re-entry

### Extraction Failures
- Date parsing has fallback (`parse_date_safe()`)
- Age validation (0.08 to 110 years)
- If extraction fails, system asks clarifying questions

### LLM Failures
- If LLM extraction returns empty, system falls back to keyword matching (for yes/no)
- Special handling for adventure sports ensures answers are captured even if LLM fails

## Current Status

✅ **Working:**
- Conversation flow with all 6 questions
- Adventure sports question asked at correct time
- Keyword parsing for natural yes/no responses ("i am", "i will", etc.)
- Confirmation flow with correct adventure activities value
- State persistence across turns
- Quote generation after confirmation

⚠️ **Known Limitations:**
- Intent classification uses keyword matching (TODO: proper NLP)
- Some edge cases in date parsing may need improvement
- No explicit handling for users who skip adventure question entirely

## Key Files

- `apps/backend/app/agents/graph.py` - Main conversation graph (1283 lines)
- `apps/backend/app/agents/llm_client.py` - LLM extraction logic
- `apps/backend/app/routers/chat.py` - API endpoint
- `apps/backend/app/services/pricing.py` - Quote calculation
- `apps/backend/app/models/trip.py` - Database Trip model

## Testing

Test flow:
1. Start conversation with session_id (UUID)
2. Provide destination, dates, travelers (can be all at once or one by one)
3. System asks adventure question
4. Answer "yes", "i am", "no", etc.
5. System shows confirmation with correct adventure value
6. Confirm → System generates quotes

**Example Session:**
```
User: "I want to go to France from December 20 to January 3 with 1 traveler age 20"
Bot: "Are you planning any adventure activities...?"
User: "i am"
Bot: [Shows confirmation with Adventure activities: Yes]
User: "yes"
Bot: [Generates quotes]
```

---

**Last Updated:** After adventure sports question fixes (recognition of "i am", flow control improvements, extraction validation)

