# ConvoTravelInsure API Documentation

## Overview

The ConvoTravelInsure API provides endpoints for travel insurance quoting, policy management, claims processing, and conversational AI interactions.

## Base URL

- Development: `http://localhost:8000`
- Production: `https://api.convotravelinsure.com`

## Authentication

All API endpoints require authentication except for public endpoints. Use JWT tokens in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Endpoints

### Authentication

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "name": "John Doe",
  "password": "password123"
}
```

**Response:**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

#### Get Current User
```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

### Trips

#### Create Trip
```http
POST /api/v1/trips/
Authorization: Bearer <token>
Content-Type: application/json

{
  "start_date": "2024-03-15",
  "end_date": "2024-03-22",
  "destinations": ["France", "Italy"],
  "flight_refs": [{"airline": "AF", "flight_number": "123"}],
  "accommodation_refs": [{"hotel": "Hotel Paris", "booking_ref": "ABC123"}],
  "total_cost": "2500.00"
}
```

#### Get Trips
```http
GET /api/v1/trips/
Authorization: Bearer <token>
```

#### Get Trip
```http
GET /api/v1/trips/{trip_id}
Authorization: Bearer <token>
```

#### Create Trip Event
```http
POST /api/v1/trips/{trip_id}/events
Authorization: Bearer <token>
Content-Type: application/json

{
  "type": "delay",
  "description": "Flight delayed by 2 hours",
  "timestamp": "2024-03-15T10:00:00Z"
}
```

### Quotes

#### Create Quote
```http
POST /api/v1/quotes/
Authorization: Bearer <token>
Content-Type: application/json

{
  "trip_id": "uuid",
  "product_type": "single",
  "travelers": [
    {
      "name": "John Doe",
      "age": 35,
      "is_primary": true,
      "preexisting_conditions": []
    }
  ],
  "activities": [
    {"type": "sightseeing", "description": "City tours"},
    {"type": "hiking", "description": "Mountain hiking"}
  ]
}
```

#### Get Quotes
```http
GET /api/v1/quotes/
Authorization: Bearer <token>
```

#### Get Quote
```http
GET /api/v1/quotes/{quote_id}
Authorization: Bearer <token>
```

#### Update Quote
```http
PUT /api/v1/quotes/{quote_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "travelers": [...],
  "activities": [...],
  "risk_breakdown": {...}
}
```

#### Calculate Firm Price
```http
POST /api/v1/quotes/{quote_id}/price
Authorization: Bearer <token>
Content-Type: application/json

{
  "quote_id": "uuid"
}
```

**Response:**
```json
{
  "quote_id": "uuid",
  "price": 125.50,
  "breakdown": {
    "base_rate": 75.00,
    "trip_duration": 7,
    "age_loading": 0.0,
    "activity_loading": 0.2,
    "destination_loading": 0.1,
    "fees": 5.00,
    "tax": 10.05,
    "subtotal": 90.00
  },
  "currency": "USD",
  "explanation": "Base rate: $75.00 | Activity risk loading: +20.0% | Destination risk loading: +10.0% | Fees: $5.00 | Tax: $10.05"
}
```

### Policies

#### Create Policy
```http
POST /api/v1/policies/
Authorization: Bearer <token>
Content-Type: application/json

{
  "quote_id": "uuid",
  "coverage": {
    "medical": 100000,
    "trip_cancellation": 5000,
    "baggage": 2500
  },
  "named_insureds": [
    {
      "name": "John Doe",
      "age": 35,
      "is_primary": true
    }
  ],
  "effective_date": "2024-03-15",
  "expiry_date": "2024-03-22",
  "cooling_off_days": 14
}
```

#### Get Policies
```http
GET /api/v1/policies/
Authorization: Bearer <token>
```

#### Get Policy
```http
GET /api/v1/policies/{policy_id}
Authorization: Bearer <token>
```

### Claims

#### Create Claim
```http
POST /api/v1/claims/
Authorization: Bearer <token>
Content-Type: application/json

{
  "policy_id": "uuid",
  "claim_type": "trip_delay",
  "amount": 500.00,
  "currency": "USD",
  "requirements": {
    "required_documents": ["Flight confirmation", "Delay certificate"],
    "required_info": ["Delay duration", "Reason for delay"]
  }
}
```

#### Get Claims
```http
GET /api/v1/claims/
Authorization: Bearer <token>
```

#### Get Claim
```http
GET /api/v1/claims/{claim_id}
Authorization: Bearer <token>
```

#### Update Claim
```http
PUT /api/v1/claims/{claim_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "claim_type": "trip_delay",
  "amount": 500.00,
  "documents": [
    {
      "filename": "delay_certificate.pdf",
      "content_type": "application/pdf",
      "size": 1024000
    }
  ]
}
```

#### Upload Document
```http
POST /api/v1/claims/{claim_id}/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <file>
```

#### Submit Claim
```http
POST /api/v1/claims/{claim_id}/submit
Authorization: Bearer <token>
```

### RAG (Policy Search)

#### Search Documents
```http
GET /api/v1/rag/search?q=medical coverage&limit=5&product_type=COMP_TRAVEL
Authorization: Bearer <token>
```

**Response:**
```json
{
  "query": "medical coverage",
  "documents": [
    {
      "id": "uuid",
      "title": "Comprehensive Travel Insurance",
      "insurer_name": "Demo Insurer",
      "product_code": "COMP_TRAVEL",
      "section_id": "2.1",
      "heading": "Medical Coverage",
      "text": "Medical expenses are covered up to $100,000 for emergency treatment during your trip.",
      "citations": {"section": "2.1", "page": 5},
      "similarity_score": 0.95
    }
  ],
  "total_results": 1
}
```

#### Ingest Document
```http
POST /api/v1/rag/ingest
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Policy Document",
  "insurer_name": "Demo Insurer",
  "product_code": "COMP_TRAVEL",
  "content": "Full document content...",
  "split_by_sections": true
}
```

### Human Handoff

#### Create Handoff Request
```http
POST /api/v1/handoff/
Authorization: Bearer <token>
Content-Type: application/json

{
  "reason": "complex_query"
}
```

**Response:**
```json
{
  "message": "Handoff request created successfully",
  "handoff_request": {
    "id": "uuid",
    "user_id": "uuid",
    "user_email": "user@example.com",
    "reason": "complex_query",
    "conversation_summary": "User asked about complex coverage scenarios...",
    "priority": "normal",
    "status": "pending",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

#### Get Handoff Reasons
```http
GET /api/v1/handoff/reasons
Authorization: Bearer <token>
```

### Voice

#### Process Voice Input
```http
POST /api/v1/voice/
Authorization: Bearer <token>
Content-Type: application/json

{
  "audio_data": "base64-encoded-audio",
  "transcript": "I need help with my claim"
}
```

**Response:**
```json
{
  "transcript": "I need help with my claim",
  "response": "I'd be happy to help you with your claim. What type of claim are you looking to file?",
  "success": true
}
```

## Error Responses

All endpoints return consistent error responses:

```json
{
  "detail": "Error message",
  "status_code": 400
}
```

### Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

## Rate Limiting

- 100 requests per minute per user
- 1000 requests per hour per user

## Pagination

List endpoints support pagination:

```http
GET /api/v1/quotes/?page=1&limit=20
```

**Response:**
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "limit": 20,
  "pages": 5
}
```

## Webhooks

The API supports webhooks for real-time updates:

- `quote.created` - New quote created
- `quote.priced` - Quote price calculated
- `policy.created` - Policy created
- `claim.submitted` - Claim submitted
- `claim.approved` - Claim approved
- `claim.rejected` - Claim rejected

## SDKs

Official SDKs are available for:

- JavaScript/TypeScript
- Python
- Go
- Java

## Support

For API support:

- Email: api-support@convotravelinsure.com
- Documentation: https://docs.convotravelinsure.com
- Status Page: https://status.convotravelinsure.com
