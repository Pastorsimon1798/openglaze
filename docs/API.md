# OpenGlaze API Reference

Complete reference for the OpenGlaze REST API.

**Base URL**: `https://your-instance.com/api`

**Authentication**: Bearer token (JWT) or session cookie

## Authentication

### Login

```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password"
}
```

**Response:**

```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Jane Potter"
  }
}
```

### Register

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure-password",
  "name": "Jane Potter"
}
```

## Glazes

### List Glazes

```http
GET /api/glazes?page=1&per_page=20&search=celadon&cone=10&atmosphere=reduction
Authorization: Bearer <token>
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `per_page` | integer | Items per page (default: 20, max: 100) |
| `search` | string | Search by name, family, or description |
| `cone` | string | Filter by cone (e.g., "10", "6", "06") |
| `atmosphere` | string | Filter by atmosphere (oxidation, reduction, neutral) |
| `base_type` | string | Filter by base type |
| `surface` | string | Filter by surface finish |

**Response:**

```json
{
  "glazes": [
    {
      "id": 1,
      "name": "Celadon",
      "family": "celadon",
      "hex": "#8FBC8F",
      "chemistry": "SiO2: 2.8, Al2O3: 0.4, CaO: 0.6...",
      "recipe": "Feldspar: 45%, Silica: 30%, Whiting: 15%...",
      "cone": "10",
      "atmosphere": "reduction",
      "food_safe": true,
      "base_type": "stoneware",
      "surface": "glossy",
      "transparency": "semi-transparent",
      "created_at": "2026-04-01T12:00:00Z"
    }
  ],
  "total": 45,
  "page": 1,
  "per_page": 20
}
```

### Get Glaze by ID

```http
GET /api/glazes/<id>
Authorization: Bearer <token>
```

### Create Glaze

```http
POST /api/glazes
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "My Custom Glaze",
  "family": "ash",
  "recipe": "Feldspar: 50%, Silica: 30%, Ash: 20%",
  "chemistry": "SiO2: 3.0, Al2O3: 0.5, CaO: 0.5",
  "cone": "10",
  "atmosphere": "reduction",
  "food_safe": false,
  "base_type": "stoneware",
  "surface": "matte",
  "transparency": "opaque"
}
```

### Update Glaze

```http
PUT /api/glazes/<id>
Content-Type: application/json
Authorization: Bearer <token>
```

### Delete Glaze

```http
DELETE /api/glazes/<id>
Authorization: Bearer <token>
```

## Combinations

### List Combinations

```http
GET /api/combinations?base=Tenmoku&top=Chun+Blue
Authorization: Bearer <token>
```

### Create Combination

```http
POST /api/combinations
Content-Type: application/json
Authorization: Bearer <token>

{
  "base": "Tenmoko",
  "top": "Chun Blue",
  "type": "user-prediction",
  "source": "user",
  "result": "Predicted: subtle breaking at edges",
  "risk": "low",
  "effect": "subtle"
}
```

**Types:** `research-backed`, `user-prediction`, `confirmed`, `surprise`

## Experiments

### List Experiments

```http
GET /api/experiments?stage=firing&status=active
Authorization: Bearer <token>
```

### Create Experiment

```http
POST /api/experiments
Content-Type: application/json
Authorization: Bearer <token>

{
  "title": "Copper Red Test Series",
  "glaze_id": 5,
  "stage": "ideation",
  "notes": "Testing copper carbonate percentages from 0.5% to 2%",
  "hypothesis": "1% copper will produce the best red with minimal pinholing"
}
```

### Update Experiment Stage

```http
PATCH /api/experiments/<id>
Content-Type: application/json
Authorization: Bearer <token>

{
  "stage": "firing",
  "firing_log": {
    "cone": "10",
    "atmosphere": "reduction",
    "schedule": "slow-cool",
    "temperature": 1285,
    "duration": 12
  }
}
```

## Chemistry

### Calculate UMF

```http
POST /api/chemistry/umf
Content-Type: application/json
Authorization: Bearer <token>

{
  "recipe": {
    "Feldspar": 45,
    "Silica": 30,
    "Whiting": 15,
    "Kaolin": 10
  }
}
```

**Response:**

```json
{
  "umf": {
    "SiO2": 3.2,
    "Al2O3": 0.45,
    "CaO": 0.55
  },
  "analysis": {
    "silica_alumina_ratio": 7.11,
    "predicted_surface": "glossy",
    "thermal_expansion": 6.2
  }
}
```

### Check Compatibility

```http
POST /api/chemistry/compatibility
Content-Type: application/json
Authorization: Bearer <token>

{
  "base_id": 1,
  "top_id": 2
}
```

**Response:**

```json
{
  "compatible": true,
  "risk_level": "low",
  "predicted_effect": "subtle breaking at edges",
  "thermal_expansion_delta": 0.3,
  "warnings": ["Ensure both glazes are at the same maturity at target cone"]
}
```

### Batch Calculator

```http
POST /api/chemistry/batch
Content-Type: application/json
Authorization: Bearer <token>

{
  "glaze_id": 1,
  "batch_size_grams": 5000,
  "unit": "grams"
}
```

**Response:**

```json
{
  "batch": {
    "Feldspar": 2250,
    "Silica": 1500,
    "Whiting": 750,
    "Kaolin": 500
  },
  "total_grams": 5000,
  "cost_estimate": {
    "currency": "USD",
    "total": 12.50
  }
}
```

## AI (Kama)

### Ask Kama

```http
POST /api/ask
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "What would happen if I add 2% rutile to this celadon?",
  "glaze_context": [1, 2, 3],
  "stream": false
}
```

**Response:**

```json
{
  "response": "Adding 2% rutile to a celadon base would likely...",
  "sources": ["glaze_id:1", "chemistry_rules:7"],
  "confidence": "high"
}
```

### Streaming Response

```http
POST /api/ask/stream
Content-Type: application/json
Authorization: Bearer <token>

{
  "message": "Explain UMF calculation",
  "stream": true
}
```

**Response:** Server-sent events (SSE) stream.

## Studios

### List Studios

```http
GET /api/studios
Authorization: Bearer <token>
```

### Create Studio

```http
POST /api/studios
Content-Type: application/json
Authorization: Bearer <token>

{
  "name": "My Studio",
  "description": "Cone 10 gas reduction studio",
  "profile": {
    "cone": "10",
    "atmosphere": "reduction",
    "kiln_type": "gas"
  }
}
```

### Add Member

```http
POST /api/studios/<id>/members
Content-Type: application/json
Authorization: Bearer <token>

{
  "user_email": "member@example.com",
  "role": "member"
}
```

**Roles:** `owner`, `admin`, `member`, `viewer`

## Billing

### Get Subscription

```http
GET /api/billing/subscription
Authorization: Bearer <token>
```

### Create Checkout Session

```http
POST /api/billing/checkout
Content-Type: application/json
Authorization: Bearer <token>

{
  "tier": "pro",
  "interval": "monthly",
  "provider": "stripe"
}
```

**Tiers:** `free`, `pro`, `studio`, `education`
**Intervals:** `monthly`, `yearly`
**Providers:** `stripe`, `paypal`, `btcpay`, `manual`

### Webhooks

Payment providers send webhook events to:

- Stripe: `POST /api/billing/webhook/stripe`
- PayPal: `POST /api/billing/webhook/paypal`
- BTCPay: `POST /api/billing/webhook/btcpay`

## Uploads

### Upload Photo

```http
POST /api/uploads
Content-Type: multipart/form-data
Authorization: Bearer <token>

file: <binary>
glaze_id: 1
firing_id: 5
caption: "Cone 10 reduction, April 2026"
```

## Gamification

### Get User Stats

```http
GET /api/gamification/stats
Authorization: Bearer <token>
```

**Response:**

```json
{
  "points": 1250,
  "streak_days": 7,
  "total_experiments": 23,
  "badges": ["first_glaze", "ten_experiments", "streak_week"],
  "rank": "Journeyman Potter"
}
```

### Get Leaderboard

```http
GET /api/gamification/leaderboard?studio_id=1&period=month
```

## Predictions

### Create Prediction

```http
POST /api/predictions
Content-Type: application/json
Authorization: Bearer <token>

{
  "combination_id": 5,
  "prediction": "The result will be a deep blue with iron breaking",
  "confidence": 0.8
}
```

## Health

```http
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-04-24T11:00:00Z"
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid cone value",
    "details": {
      "cone": "Must be one of: 06, 04, 02, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14"
    }
  }
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Missing or invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |

## Rate Limits

- Authenticated: 60 requests/minute
- Unauthenticated: 20 requests/minute
- AI endpoints: 10 requests/minute

## Pagination

List endpoints use cursor-based pagination:

```http
GET /api/glazes?page=2&per_page=50
```

**Response includes:**

```json
{
  "items": [...],
  "total": 200,
  "page": 2,
  "per_page": 50,
  "total_pages": 4,
  "has_next": true,
  "has_prev": true
}
```
