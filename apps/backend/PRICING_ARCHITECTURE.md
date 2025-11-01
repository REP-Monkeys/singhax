# Pricing Architecture - Ancileo-Only Mode

**Last Updated**: November 1, 2025  
**Status**: Production (Ancileo-only)

---

## Overview

The pricing system uses **Ancileo MSIG API exclusively** for all insurance quote calculations. Claims intelligence database is available for analytics and insights, but not for pricing.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     User Request (Agent)                     │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ├─→ Collect Trip Details
                      │   • Destination
                      │   • Dates
                      │   • Travelers
                      │   • Adventure Sports?
                      │
                      ▼
         ┌────────────────────────────┐
         │   PricingService.          │
         │   calculate_step1_quote()  │
         │   (pricing_mode="ancileo") │
         └────────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │  _calculate_ancileo_quote() │
         └────────────┬───────────────┘
                      │
                      ├─→ Validate destination
                      ├─→ Get country ISO code
                      ├─→ Call Ancileo API
                      │   (POST /v1/travel/front/pricing)
                      │
                      ▼
         ┌────────────────────────────┐
         │   Ancileo API Response     │
         │   {"id": "...",            │
         │    "offerCategories": [...]}│
         └────────────┬───────────────┘
                      │
                      ├─→ Normalize response
                      │   (id → quoteId)
                      │
                      ▼
         ┌────────────────────────────┐
         │  Calculate 3-Tier Pricing  │
         │  • Elite (from API)        │
         │  • Standard (Elite ÷ 1.8)  │
         │  • Premier (Elite × 1.39)  │
         └────────────┬───────────────┘
                      │
                      ├─→ If adventure_sports=True:
                      │   Exclude Standard tier
                      │
                      ▼
         ┌────────────────────────────┐
         │  Return Quote Result       │
         │  • 3 tiers (or 2)          │
         │  • Prices in SGD           │
         │  • ancileo_reference       │
         │  • Recommended tier        │
         └────────────┬───────────────┘
                      │
                      ▼
         ┌────────────────────────────┐
         │  (Optional) Add Claims     │
         │  Intelligence Insights     │
         │  • Based on X claims       │
         │  • Risk factors            │
         │  • Recommendations         │
         └────────────────────────────┘
```

---

## Component Details

### 1. PricingService

**Location**: `apps/backend/app/services/pricing.py`

**Main Method**:
```python
def calculate_step1_quote(
    destination: str,
    departure_date: date,
    return_date: date,
    travelers_ages: List[int],
    adventure_sports: bool = False,
    pricing_mode: str = "ancileo"  # Default
) -> Dict[str, Any]
```

**Flow**:
1. Validate inputs (dates, ages, destination)
2. Route to `_calculate_ancileo_quote()`
3. Return normalized quote result

### 2. AncileoAdapter

**Location**: `apps/backend/app/adapters/insurer/ancileo_adapter.py`

**Strategy**:
- Calls Ancileo API to get Elite tier price
- Uses Elite as baseline (1.0x)
- Calculates Standard = Elite ÷ 1.8 (0.556x)
- Calculates Premier = Elite × 1.39

**Why This Works**:
- Elite is market-tested baseline from Ancileo
- Tier ratios maintain consistent coverage differences
- All 3 tiers are proportional to same market data

### 3. AncileoClient

**Location**: `apps/backend/app/adapters/insurer/ancileo_client.py`

**API Integration**:
```python
POST https://dev.api.ancileo.com/v1/travel/front/pricing

Body:
{
    "market": "SG",
    "languageCode": "en",
    "channel": "white-label",
    "deviceType": "DESKTOP",
    "context": {
        "tripType": "RT",
        "departureDate": "2025-11-16",
        "returnDate": "2025-11-23",
        "departureCountry": "SG",
        "arrivalCountry": "TH",
        "adultsCount": 1,
        "childrenCount": 0
    }
}
```

**Response Normalization**:
```python
# API returns:
{"id": "...", "offerCategories": [...]}

# Client normalizes to:
{"quoteId": "...", "offers": [...]}
```

### 4. ClaimsIntelligenceService (Analytics Only)

**Location**: `apps/backend/app/services/claims_intelligence.py`

**Used For**:
- ✅ Show destination insights ("Based on 13,281 claims")
- ✅ Risk factor analysis
- ✅ Adventure sports coverage explanations
- ❌ **NOT** used for pricing calculations

**Example Usage**:
```python
# Get insights to show user
stats = claims_intelligence.get_destination_stats("Thailand")

quote_response = {
    "pricing": ancileo_quotes,  # Actual pricing from Ancileo
    "insights": {
        "based_on_claims": stats["total_claims"],  # 13,281
        "avg_claim": stats["avg_claim"],           # $259.98
        "risk_level": "medium"
    }
}
```

---

## Quote Response Structure

### Successful Quote (Conventional Trip)

```python
{
    "success": True,
    "destination": "Thailand",
    "area": "ASIA",
    "departure_date": "2025-11-16",
    "return_date": "2025-11-23",
    "duration_days": 8,
    "travelers_count": 1,
    "adventure_sports": False,
    
    "quotes": {
        "standard": {
            "tier": "standard",
            "price": 28.45,
            "currency": "SGD",
            "coverage": {
                "medical_coverage": 250000,
                "trip_cancellation": 5000,
                "baggage_loss": 3000,
                "personal_accident": 100000,
                "adventure_sports": False
            },
            "breakdown": {
                "duration_days": 8,
                "travelers_count": 1,
                "area": "ASIA",
                "source": "ancileo_api",
                "multiplier": 0.556
            }
        },
        "elite": {
            "tier": "elite",
            "price": 51.21,  # From Ancileo API
            "currency": "SGD",
            "coverage": {
                "medical_coverage": 500000,
                "trip_cancellation": 12500,
                "baggage_loss": 5000,
                "personal_accident": 250000,
                "adventure_sports": True
            },
            "breakdown": {
                "duration_days": 8,
                "travelers_count": 1,
                "area": "ASIA",
                "source": "ancileo_api",
                "multiplier": 1.0
            }
        },
        "premier": {
            "tier": "premier",
            "price": 71.18,
            "currency": "SGD",
            "coverage": {
                "medical_coverage": 1000000,
                "trip_cancellation": 15000,
                "baggage_loss": 7500,
                "personal_accident": 500000,
                "adventure_sports": True,
                "emergency_evacuation": 1000000
            },
            "breakdown": {
                "duration_days": 8,
                "travelers_count": 1,
                "area": "ASIA",
                "source": "ancileo_api",
                "multiplier": 1.39
            }
        }
    },
    
    "ancileo_reference": {
        "quoteId": "70209df4-f1f4-47eb-9eb5-eae71126e096",
        "offerId": "179ab9e5-c1b2-4b58-8dd6-e4c08342b9f2",
        "productCode": "SG_AXA_SCOOT_COMP",
        "unitPrice": 51.21,
        "currency": "SGD"
    },
    
    "recommended_tier": "standard",
    "pricing_source": "ancileo"
}
```

### Adventure Sports Quote

```python
{
    "success": True,
    "adventure_sports": True,
    
    "quotes": {
        # Standard tier EXCLUDED
        "elite": {
            "price": 102.42,
            ...
        },
        "premier": {
            "price": 142.36,
            ...
        }
    },
    
    "recommended_tier": "elite",  # Recommend lowest tier with adventure coverage
    "pricing_source": "ancileo"
}
```

---

## Business Rules

### 1. Tier Ratios (Fixed)

| Tier | Multiplier | Calculation |
|------|-----------|-------------|
| Standard | 0.556 | Elite ÷ 1.8 |
| Elite | 1.0 | Baseline from API |
| Premier | 1.39 | Elite × 1.39 |

### 2. Adventure Sports Exclusions

```python
if adventure_sports == True:
    # Exclude Standard tier (no adventure coverage)
    quotes = {
        "elite": {...},
        "premier": {...}
    }
    recommended_tier = "elite"
```

### 3. ancileo_reference Preservation

**Critical for Purchase API**:
```python
# Quote response includes:
"ancileo_reference": {
    "quoteId": "...",     # Required for Purchase API
    "offerId": "...",     # Required for Purchase API
    "productCode": "...", # Required for Purchase API
    "unitPrice": 51.21    # Must match exactly
}

# Later in Purchase API:
POST /v1/travel/front/purchase
{
    "quoteId": "...",  # From ancileo_reference
    "purchaseOffers": [{
        "offerId": "...",      # From ancileo_reference
        "productCode": "...",  # From ancileo_reference
        "unitPrice": 51.21     # Must match exactly
    }]
}
```

---

## Integration Points

### 1. Agent Graph

**File**: `apps/backend/app/agents/graph.py`

```python
def pricing(state: ConversationState) -> ConversationState:
    # Extract trip details from state
    destination = trip["destination"]
    departure_date = trip["departure_date"]
    return_date = trip["return_date"]
    travelers_ages = travelers["ages"]
    adventure_sports = prefs.get("adventure_sports", False)
    
    # Call pricing service (defaults to Ancileo mode)
    quote_result = pricing_service.calculate_step1_quote(
        destination=destination,
        departure_date=departure_date,
        return_date=return_date,
        travelers_ages=travelers_ages,
        adventure_sports=adventure_sports
        # pricing_mode="ancileo" (default)
    )
    
    # Store quote in state
    state["quote_data"] = quote_result
    
    # (Optional) Add claims insights
    if claims_analyzer:
        insights = analyze_destination_risk(
            destination, travelers_ages, adventure_sports
        )
        state["risk_insights"] = insights
```

### 2. Frontend API

Future integration:
```typescript
// Frontend calls quote endpoint
const response = await fetch('/api/v1/quotes/calculate', {
    method: 'POST',
    body: JSON.stringify({
        destination: 'Thailand',
        departure_date: '2025-11-16',
        return_date: '2025-11-23',
        travelers_ages: [32],
        adventure_sports: false
        // pricing_mode defaults to "ancileo"
    })
});

const quote = await response.json();
// Display 3 tiers with prices
```

---

## Error Handling

### Ancileo API Errors

```python
try:
    response = self.adapter.price_firm(adapter_input)
except AncileoAPIError as e:
    return {
        "success": False,
        "error": "Failed to get pricing from Ancileo API"
    }
```

### Common Error Scenarios

| Error | Cause | Solution |
|-------|-------|----------|
| "No offers returned" | Response parsing issue | ✅ Fixed with normalization |
| "Invalid destination" | Country not in mapping | Add to GeoMapper |
| "Trip duration exceeds 182 days" | User input > max | Validation message |
| "Quote expired" | quoteId > 24 hours old | Generate new quote |

---

## Performance

### Typical Response Times

- **Ancileo API call**: 200-400ms
- **Response normalization**: <1ms
- **Tier calculation**: <1ms
- **Total quote time**: ~250-450ms

### Caching Strategy

Currently: No caching (real-time pricing)

Future consideration:
- Cache quotes for 30 minutes (reduce API calls)
- Invalidate on user changes
- Still generate fresh quote before purchase

---

## Testing

### Unit Tests

```bash
# Test Ancileo mode
pytest apps/backend/tests/test_pricing.py::test_ancileo_pricing -v

# Test adventure sports logic
pytest apps/backend/tests/test_pricing.py::test_adventure_sports_exclusion -v
```

### Manual Testing

```python
from app.services.pricing import PricingService
from datetime import date, timedelta

s = PricingService()

# Conventional trip
result = s.calculate_step1_quote(
    'Thailand',
    date.today() + timedelta(15),
    date.today() + timedelta(22),
    [32],
    False  # No adventure sports
)
print(result['quotes'].keys())  # ['standard', 'elite', 'premier']

# Adventure trip
result = s.calculate_step1_quote(
    'Thailand',
    date.today() + timedelta(15),
    date.today() + timedelta(22),
    [32, 32],
    True  # Adventure sports
)
print(result['quotes'].keys())  # ['elite', 'premier']  (Standard excluded)
```

---

## Monitoring & Observability

### Key Metrics to Track

1. **Ancileo API Success Rate**
   - Target: >99%
   - Alert: <95%

2. **Quote Response Time**
   - Target: <500ms
   - Alert: >1000ms

3. **Quote-to-Purchase Conversion**
   - Track: How many quotes lead to purchase
   - Optimize: Pricing display, tier recommendations

4. **Adventure Sports Quote Rate**
   - Track: % of quotes with adventure_sports=True
   - Validate: Standard tier exclusion working

---

## Deployment Notes

### Environment Variables Required

```bash
# .env file
ANCILEO_MSIG_API_KEY=98608e5b-****
ANCILEO_API_BASE_URL=https://dev.api.ancileo.com

# Optional (for claims insights)
CLAIMS_DATABASE_URL=postgresql://...
ENABLE_CLAIMS_INTELLIGENCE=true
```

### Health Check

```python
# Check if Ancileo API is accessible
from app.adapters.insurer.ancileo_client import AncileoClient
from datetime import date, timedelta

client = AncileoClient()
try:
    response = client.get_quotation(
        trip_type="RT",
        departure_date=date.today() + timedelta(30),
        return_date=date.today() + timedelta(37),
        departure_country="SG",
        arrival_country="TH",
        adults_count=1,
        children_count=0
    )
    print("✅ Ancileo API healthy")
except Exception as e:
    print(f"❌ Ancileo API error: {e}")
```

---

## Future Enhancements

### Potential Improvements

1. **Quote Caching**
   - Cache valid for 30 minutes
   - Reduce API calls
   - Faster response times

2. **Multi-Currency Support**
   - Currently: SGD only
   - Future: USD, EUR, etc.

3. **Dynamic Tier Ratios**
   - Currently: Fixed (0.556, 1.0, 1.39)
   - Future: Adjust based on destination/season

4. **A/B Testing**
   - Test different tier recommendations
   - Optimize conversion rates

---

## Summary

- ✅ **Single Source of Truth**: Ancileo API for all pricing
- ✅ **Reliable**: No variance issues, consistent results
- ✅ **Simple**: One code path, easy to maintain
- ✅ **Complete**: Supports conventional & adventure sports
- ✅ **Integrated**: Works with Purchase API flow
- ✅ **Observable**: Claims insights for analytics

**Status**: Production Ready ✅

---

**Last Updated**: November 1, 2025  
**Maintained By**: Backend Team  
**Related Docs**:
- `PRICING_MODE_CHANGE.md` - Change history
- `VALIDATION_COMPLETE.md` - Testing results
- `ANCILEO_API_FIX_SUMMARY.md` - API fix details

