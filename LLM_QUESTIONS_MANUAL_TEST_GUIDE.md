# LLM-Generated Questions - Manual Testing Guide

## Overview

This guide provides step-by-step manual testing scenarios to validate that the LLM-generated question system is working correctly and producing natural, context-aware conversations.

## Prerequisites

1. Backend server running (`START_BACKEND.bat` or `python apps/backend/app/main.py`)
2. Frontend running (`START_FRONTEND.bat` or `npm run dev` in apps/frontend)
3. Environment variable `USE_LLM_QUESTIONS=true` set in `.env` file (this is the default)
4. Valid `GROQ_API_KEY` configured for LLM access

## Testing Scenarios

### Scenario 1: Basic Flow - Natural Conversation

**Objective**: Verify that questions feel natural and reference previous responses.

**Steps**:
1. Open the chat interface
2. Type: "I need travel insurance"
3. **Expected**: AI asks about destination in a friendly way
4. Type: "Thailand"
5. **Expected**: AI asks about departure date and mentions "Thailand" in the question
6. Type: "2025-12-15"
7. **Expected**: AI asks about return date and may reference "Thailand" or the departure date
8. Type: "2025-12-22"
9. **Expected**: AI asks about travelers/ages
10. Type: "2 travelers, ages 30 and 8"
11. **Expected**: AI asks about adventure sports, may reference trip details
12. Type: "No"
13. **Expected**: AI shows quote with pricing

**Validation Checklist**:
- [ ] Each question feels natural (not robotic)
- [ ] Follow-up questions reference the destination name
- [ ] Questions are varied (not the same every time you restart)
- [ ] No errors or crashes
- [ ] All information correctly extracted despite natural language

---

### Scenario 2: Compare LLM vs Template Mode

**Objective**: Compare the difference between LLM-generated and template questions.

**Setup A - LLM Mode**:
1. Ensure `.env` has `USE_LLM_QUESTIONS=true`
2. Restart backend
3. Run through Scenario 1 and note the questions

**Setup B - Template Mode**:
1. Change `.env` to `USE_LLM_QUESTIONS=false`
2. Restart backend
3. Run through Scenario 1 again

**Validation**:
- [ ] LLM questions feel more conversational
- [ ] Template questions are more predictable/consistent
- [ ] Both modes successfully collect all information
- [ ] Both modes handle the conversation without errors

---

### Scenario 3: Context Awareness Test

**Objective**: Verify that questions adapt to conversation context.

**Test 3A - Enthusiastic User**:
1. Type: "I'm so excited! I'm going to Japan for cherry blossom season!"
2. **Expected**: AI should match enthusiasm and reference Japan
3. Continue providing information naturally
4. **Validation**: AI maintains conversational tone

**Test 3B - Business-like User**:
1. Type: "I need insurance. Destination: Singapore."
2. **Expected**: AI should be professional and efficient
3. Type: "2025-11-10 to 2025-11-15"
4. **Expected**: AI accepts date range format
5. **Validation**: AI adapts to user's communication style

**Test 3C - Uncertain User**:
1. Type: "I'm not sure, maybe Indonesia?"
2. **Expected**: AI handles uncertainty gracefully
3. Type: "Yes, Indonesia"
4. **Validation**: AI confirms and moves forward

---

### Scenario 4: Document Upload Integration

**Objective**: Verify LLM questions work with document extraction.

**Steps**:
1. Upload a flight booking confirmation (PDF/image)
2. **Expected**: AI extracts destination, dates from document
3. **Expected**: AI asks for missing information (travelers, adventure sports)
4. **Validation**: Questions reference the extracted information
5. Type answers to remaining questions
6. **Expected**: Complete quote flow succeeds

---

### Scenario 5: Error Handling & Fallback

**Objective**: Test that LLM failures don't break the conversation.

**Test 5A - Simulate LLM Failure** (requires code modification):
1. Temporarily modify `question_generator.py` to always raise exception
2. Start conversation
3. **Expected**: System uses fallback templates
4. **Validation**: Conversation continues without crashing

**Test 5B - Invalid API Key**:
1. Set invalid `GROQ_API_KEY` temporarily
2. Start conversation
3. **Expected**: System gracefully falls back to templates
4. **Validation**: User gets a response (even if template-based)

---

### Scenario 6: Multiple Destinations (Edge Case)

**Objective**: Test context with complex trip details.

**Steps**:
1. Type: "I'm visiting Thailand, then Japan, then back to Thailand"
2. **Expected**: AI handles the primary destination
3. Continue with dates and travelers
4. **Validation**: Questions remain coherent despite complex destination

---

### Scenario 7: Mid-Conversation Topic Changes

**Objective**: Verify questions adapt when user changes topics.

**Steps**:
1. Type: "I need travel insurance for Thailand"
2. AI asks for dates
3. Type: "Actually, I changed my mind. I'm going to Australia"
4. **Expected**: AI acknowledges change and adjusts questions
5. **Validation**: Questions reference Australia, not Thailand

---

### Scenario 8: Performance & Latency

**Objective**: Measure impact of LLM question generation on response time.

**Measurement Points**:
- Time from user message to AI response (with LLM questions)
- Time from user message to AI response (with templates)

**Acceptance Criteria**:
- [ ] LLM mode adds < 500ms latency per question
- [ ] No noticeable delay from user perspective
- [ ] System remains responsive

**Tools**: Browser DevTools Network tab, backend logs

---

### Scenario 9: Question Quality Assessment

**Objective**: Subjectively assess the quality and naturalness of questions.

**Criteria to Evaluate**:

1. **Personalization** (1-5 score):
   - [ ] Questions reference user's previous answers
   - [ ] Questions feel tailored to this specific trip
   - [ ] Questions acknowledge user's input

2. **Naturalness** (1-5 score):
   - [ ] Questions sound human-written
   - [ ] No awkward phrasing
   - [ ] Appropriate use of conversational markers

3. **Clarity** (1-5 score):
   - [ ] Questions are easy to understand
   - [ ] User knows exactly what information to provide
   - [ ] Examples provided when helpful (dates, format)

4. **Variety** (1-5 score):
   - [ ] Questions vary between sessions
   - [ ] Not overly repetitive
   - [ ] Creative phrasings

**Target**: Average score of 4+ across all criteria

---

### Scenario 10: Full Journey - Real User Perspective

**Objective**: Simulate a real user getting insurance from start to finish.

**Persona**: Sarah, 32, planning a family vacation

**Script**:
1. "Hi, I need travel insurance for a family trip"
2. Wait for destination question, respond: "We're going to Bali"
3. Wait for date question, respond: "We leave December 20, 2025"
4. Wait for return question, respond: "Coming back January 5, 2026"
5. Wait for travelers question, respond: "4 people - me (32), my husband (35), and our kids ages 7 and 4"
6. Wait for adventure question, respond: "We might do some snorkeling"
7. Review quote
8. Proceed to payment

**Validation**:
- [ ] Conversation felt natural throughout
- [ ] Sarah never felt confused about what to answer
- [ ] Questions acknowledged her family trip context
- [ ] Adventure sports question was appropriate
- [ ] Complete journey succeeded without issues

---

## Prompt Refinement Checklist

Based on test results, consider refining prompts if you observe:

- [ ] Questions are too long (>2 sentences)
- [ ] Questions don't reference collected context
- [ ] Questions are too generic
- [ ] Questions are repetitive across sessions
- [ ] Questions miss important formatting instructions (especially for dates)
- [ ] Questions sound robotic or templated despite using LLM
- [ ] Questions contain hallucinated information
- [ ] Questions are inconsistent in tone

## Test Results Documentation

**Date**: _________________

**Tester**: _________________

**LLM Model**: Groq Llama 3.1 70B

**USE_LLM_QUESTIONS**: ☐ True  ☐ False

### Overall Assessment

- **Naturalness**: ☐ Excellent  ☐ Good  ☐ Fair  ☐ Poor
- **Context Awareness**: ☐ Excellent  ☐ Good  ☐ Fair  ☐ Poor
- **Reliability**: ☐ Excellent  ☐ Good  ☐ Fair  ☐ Poor
- **Performance**: ☐ Excellent  ☐ Good  ☐ Fair  ☐ Poor

### Issues Found

| Issue | Severity | Description | Scenario |
|-------|----------|-------------|----------|
|       |          |             |          |

### Recommendations

1. _________________
2. _________________
3. _________________

### Example Conversation Samples

**Good Example** (natural, context-aware):
```
User: I'm going to Thailand
AI: [Record actual response here]
```

**Needs Improvement** (if any):
```
User: [Record input]
AI: [Record response that needs improvement]
Reason: [Why it needs improvement]
```

---

## Next Steps After Testing

1. **If tests pass**: Deploy to production with monitoring
2. **If issues found**: Refine prompts in `question_generator.py`
3. **If performance issues**: Consider caching or reducing temperature
4. **If quality issues**: Adjust system prompts for better instructions

## Monitoring in Production

After deployment, monitor:
- Conversation completion rates
- User satisfaction scores (if available)
- LLM API costs
- Response latency metrics
- Fallback usage frequency (indicates LLM failures)

---

## Troubleshooting

**Problem**: Questions are generic/not contextual
- **Solution**: Check that `collected_info` dict is properly populated
- **Solution**: Verify prompts have `{destination}` placeholders

**Problem**: LLM responses are too long
- **Solution**: Reduce `max_tokens` parameter (currently 150)
- **Solution**: Add stricter length instructions in prompts

**Problem**: Fallback templates always used
- **Solution**: Check `USE_LLM_QUESTIONS` setting
- **Solution**: Verify `GROQ_API_KEY` is valid
- **Solution**: Check backend logs for LLM errors

**Problem**: Questions don't vary between sessions
- **Solution**: Increase temperature (currently 0.7)
- **Solution**: Add more examples to prompts

---

## Conclusion

This testing guide ensures the LLM question generation system is:
- ✅ Natural and conversational
- ✅ Context-aware and personalized
- ✅ Reliable with proper fallbacks
- ✅ Performant for real-time chat
- ✅ Better than fixed templates

Complete all scenarios and document results before considering the feature production-ready.

