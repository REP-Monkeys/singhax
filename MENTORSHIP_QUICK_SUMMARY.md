# Quick Summary for MSIG Mentorship Session

## 🎯 What We Built

**ConvoTravelInsure** - AI-powered conversational travel insurance platform that:
- Guides customers through natural language conversations to get quotes
- Uses **real MSIG claims data** (72K+ claims) to recommend coverage tiers
- Extracts trip info from uploaded documents (OCR)
- Provides 3 insurance tiers (Standard/Elite/Premier) with geographic pricing

---

## 🔑 Key Innovation

**Claims Intelligence System:**
- Analyzes historical claims by destination
- Calculates risk scores (0-10) based on claim patterns
- **Automatically recommends tier upgrades** when data suggests higher risk
- Example: "4,188 Japan claims show $1,358 avg medical claims → Recommend Elite for skiing trip"

---

## 💬 3-Minute Demo Flow

1. **Conversation:** "I want to go skiing in Japan with my 8-year-old"
2. **Claims Analysis:** System queries 4,188 Japan claims → Risk score 7.5/10 (HIGH)
3. **Recommendation:** "Based on historical data, we recommend Elite tier ($378) vs Standard ($210)"
4. **Reasoning:** "95th percentile claims ($3,350) exceed Standard coverage, plus adventure sports risk"

---

## ❓ Top Questions to Ask

### Product Questions
- Are our 3 tiers aligned with MSIG's actual products?
- Coverage limits realistic? ($250K/$500K/$1M medical)
- Geographic pricing accurate? (Area A: $3/day, B: $5/day, C: $8/day)

### Claims Intelligence
- Is using historical claims for risk scoring valid/ethical?
- Should we recommend higher tiers aggressively or conservatively?
- What's typical conversion rate Standard → Elite/Premier?

### Business
- MAS regulatory requirements we need to consider?
- What makes customers choose MSIG over competitors?
- Biggest pain points in travel insurance distribution?

### Technical
- Does MSIG have real-time quote API we can integrate?
- How do we handle quote expiration?
- Privacy/compliance concerns with using claims data?

---

## 🎤 Opening Line

"I built a conversational AI platform that uses your own claims data to intelligently recommend coverage tiers to customers. Would love your feedback on whether our risk assessment approach aligns with how MSIG actually thinks about underwriting and sales."

---

**Full details:** See `MENTORSHIP_PREP.md`

