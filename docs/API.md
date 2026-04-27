# OpenGlaze API Reference

Current REST API for the Flask app in this repository.

**Base URL:** `http://localhost:8768/api` for Docker, `http://localhost:8767/api` for manual local runs unless `FLASK_PORT` is set.

**Authentication model:** default personal mode is single-user and mostly unauthenticated. Studio collaboration uses the lightweight simple-auth token returned by `/api/auth/simple-login`. Cloud/Ory auth exists in code, but PostgreSQL/cloud mode is not the default launch path.

## Health

```http
GET /health
GET /api/health
```

`/health` returns a basic status/version payload. `/api/health` also reports mode, feature flags, and rate-limit stats.

## Auth

### Simple login

```http
POST /api/auth/simple-login
Content-Type: application/json

{
  "display_name": "Jane Potter"
}
```

Response:

```json
{
  "user_id": "u_...",
  "display_name": "Jane Potter",
  "token": "..."
}
```

Send the token as:

```http
Authorization: Bearer <token>
```

### Current user

```http
GET /api/auth/me
Authorization: Bearer <token>
```

## Glazes

```http
GET /api/glazes
GET /api/glazes/<glaze_id>
POST /api/glazes
PUT /api/glazes/<glaze_id>
DELETE /api/glazes/<glaze_id>
GET /api/glazes/<glaze_id>/umf?cone=10
```

Create/update payloads use the glaze fields accepted by `Glaze.from_dict`, including `id`, `name`, `family`, `hex`, `chemistry`, `behavior`, `layering`, `warning`, `recipe`, `catalog_code`, `food_safe`, and `notes`.

## Combinations

```http
GET /api/combinations
GET /api/combinations?type=research-backed
GET /api/combinations?type=user-prediction
GET /api/combinations/grouped
GET /api/combinations/<combo_id>
POST /api/combinations
PUT /api/combinations/<combo_id>
POST /api/combinations/<combo_id>/promote
POST /api/combinations/<combo_id>/simulate
POST /api/combinations/simulate-all
GET /api/combinations/<combo_id>/compatibility?cone=10
```

## Chemistry

```http
POST /api/chemistry/batch
POST /api/chemistry/scale
POST /api/chemistry/compare
POST /api/chemistry/optimize
POST /api/chemistry/substitutions
POST /api/chemistry/defects
```

Examples:

```http
POST /api/chemistry/optimize
Content-Type: application/json

{
  "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
  "target": "reduce_cte",
  "max_suggestions": 5
}
```

```http
POST /api/chemistry/scale
Content-Type: application/json

{
  "recipe": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
  "batch_size_grams": 1000,
  "unit": "grams"
}
```

```http
POST /api/chemistry/compare
Content-Type: application/json

{
  "recipe_a": "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12",
  "recipe_b": "Custer Feldspar 40, Silica 30, Whiting 18, EPK 12",
  "name_a": "Original",
  "name_b": "Revision",
  "cone": 10
}
```

## Experiments

```http
GET /api/experiments
GET /api/experiments?stage=ideation
GET /api/experiments/active
GET /api/experiments/stats
GET /api/experiments/<exp_id>
POST /api/experiments
POST /api/experiments/<exp_id>/advance
POST /api/experiments/<exp_id>/result
POST /api/experiments/<exp_id>/archive
POST /api/experiments/<exp_id>/firing-log
POST /api/experiments/<exp_id>/share
```

## Uploads and photos

```http
POST /api/upload
GET /api/photos
```

Upload expects multipart form-data with a `photo` field. Supported extensions are JPG, JPEG, PNG, and WebP; max size is 5 MB.

## Studio collaboration

Studio endpoints require simple-auth or Ory user context.

```http
POST /api/studios
GET /api/studios
POST /api/studios/join
GET /api/studios/<studio_id>
DELETE /api/studios/<studio_id>
POST /api/studios/<studio_id>/regenerate-code
GET /api/studios/<studio_id>/lab-queue
POST /api/studios/<studio_id>/lab-queue/<combo_id>/claim
POST /api/studios/<studio_id>/lab-queue/<combo_id>/release
GET /api/studios/<studio_id>/my-claims
GET /api/studios/<studio_id>/experiments
```

## Progress, stats, and predictions

These endpoints require authenticated user context and may return `401` in default unauthenticated personal mode.

```http
GET /api/stats
GET /api/progress
POST /api/predictions
GET /api/predictions/leaderboard
```

## Templates

```http
GET /api/templates
GET /api/templates/<template_id>
POST /api/templates/<template_id>/apply
```

Applying a template requires authenticated user context.

## Demo endpoints

```http
GET /api/demo/glazes
POST /api/demo/compatibility
```

These are public demo/reference endpoints backed by curated demo glaze data when available.

## Error format

Most errors are returned as JSON:

```json
{
  "error": "Human-readable message"
}
```

Rate limits return HTTP `429` with a `Retry-After` header.
