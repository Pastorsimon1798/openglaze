# OpenGlaze Architecture

System design, data flow, and component interactions.

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Client Layer                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │   Browser   │  │  PWA (Mobile│  │  API Client │  │  CLI Tool  │ │
│  │   (SPA)     │  │   /Desktop) │  │  (External) │  │  (Future)  │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │
└─────────┼────────────────┼────────────────┼───────────────┼────────┘
          │                │                │               │
          └────────────────┴────────────────┴───────────────┘
                              │
                    ┌─────────▼─────────┐
                    │   Reverse Proxy   │  (nginx / Caddy / Traefik)
                    │   HTTPS / HTTP2   │
                    └─────────┬─────────┘
                              │
┌─────────────────────────────▼──────────────────────────────────────┐
│                      Flask Application                              │
│                                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐ │
│  │   Routes    │  │   Auth      │  │   Billing   │  │   Upload  │ │
│  │   (REST)    │  │  (JWT/      │  │  (Stripe/   │  │  (Local/  │ │
│  │             │  │  Kratos)    │  │  PayPal)    │  │  S3)      │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬─────┘ │
│         │                │                │               │       │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌────▼────┐  │
│  │   Glazes    │  │ Chemistry   │  │    AI       │  │  Studio │  │
│  │   Engine    │  │   Engine    │  │  (Kama)     │  │ Manager │  │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └────┬────┘  │
│         │                │                │              │       │
│  ┌──────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐  ┌────▼────┐  │
│  │ Experiment  │  │ Prediction  │  │   Gamifi-   │  │Analytics│  │
│  │  Pipeline   │  │   Market    │  │   cation    │  │ Engine  │  │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────┘  │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                     Core Services                            │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │  │
│  │  │ Config   │  │ Database │  │  Cache   │  │  Logger  │   │  │
│  │  │ Manager  │  │  (SQLA)  │  │  (Mem)   │  │          │   │  │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │  │
│  └─────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
┌─────────▼─────────┐ ┌───────▼───────┐ ┌────────▼────────┐
│   SQLite /        │ │  Ory Kratos   │ │ Ceramics        │
│   PostgreSQL      │ │  (Identity)   │ │ Foundation      │
│                   │ │               │ │ (JSON/YAML)     │
│  - glazes         │ │  - users      │ │                 │
│  - experiments    │ │  - sessions   │ │  - materials    │
│  - subscriptions  │ │  - schemas    │ │  - recipes      │
│  - firings        │ │               │ │  - schedules    │
└───────────────────┘ └───────────────┘ └─────────────────┘
```

## Application Layers

### 1. Presentation Layer

**Frontend (Vanilla JS SPA)**
- No build step required — pure HTML/CSS/JS
- Progressive Web App (PWA) with service worker
- Command palette for quick navigation (⌘K)
- Theme switching (light/dark/system)
- Responsive design for mobile and desktop

**Key Files:**
- `frontend/index.html` — Main application shell
- `frontend/styles/*.css` — Modular CSS (variables, components, layout)
- `frontend/scripts/*.js` — Feature modules (glazes, studio, AI, etc.)

### 2. API Layer

**Flask Routes** (`server.py`)

| Route Prefix | Module | Description |
|-------------|--------|-------------|
| `/api/glazes` | Glaze CRUD | Create, read, update, delete glazes |
| `/api/combinations` | Layering | Base/top combination tracking |
| `/api/experiments` | Pipeline | 6-stage experiment workflow |
| `/api/chemistry` | Chemistry | UMF, compatibility, batch calc |
| `/api/ask` | AI | Kama assistant endpoints |
| `/api/studios` | Collaboration | Multi-user studio management |
| `/api/billing` | Payments | Subscription and checkout |
| `/api/uploads` | Media | Photo and file uploads |
| `/api/gamification` | Engagement | Points, badges, leaderboards |
| `/api/predictions` | Prediction | Human vs AI prediction market |
| `/health` | Health | Service health check |

### 3. Business Logic Layer

**Chemistry Engine**
- UMF (Unity Molecular Formula) calculation from batch recipes
- Thermal expansion coefficient estimation
- Glaze compatibility analysis
- Oxide role classification and substitution suggestions

**AI Context System**
- Glaze-aware prompt injection for LLMs
- Streaming response handling
- Context retrieval from glaze database
- Multi-provider support (Ollama, Claude)

**Experiment Pipeline**
- Stage transitions: ideation → prediction → application → firing → analysis → documentation
- Photo documentation at each stage
- Result comparison and reproducibility tracking

**Gamification Engine**
- Point calculation based on activity types
- Streak tracking with daily/weekly milestones
- Badge awarding system
- Studio-wide leaderboards

### 4. Data Access Layer

**Database Abstraction**
- SQLAlchemy ORM for both SQLite and PostgreSQL
- Connection pooling for PostgreSQL
- SQLite with WAL mode for development
- Automatic schema migration on startup

**Ceramics Foundation Data**
- JSON/YAML files for static reference data
- Loaded at startup and cached in memory
- Versioned alongside application code
- Replaceable per-studio via `studios/<name>/`

## Data Flow Examples

### Creating a New Glaze

```
User → POST /api/glazes
  → Auth middleware validates JWT
  → Request validation (name, recipe, cone required)
  → Chemistry engine parses recipe → calculates UMF
  → Database insert with computed chemistry
  → Activity log entry (gamification points)
  → Response with full glaze object + UMF analysis
```

### Running an Experiment

```
User → POST /api/experiments
  → Validate glaze_id exists
  → Create experiment record (stage: ideation)
  → User documents hypothesis
  → PATCH /api/experiments/<id> (stage: application)
    → Record application method, layer thickness
  → PATCH /api/experiments/<id> (stage: firing)
    → Record firing log (cone, atmosphere, schedule)
  → PATCH /api/experiments/<id> (stage: analysis)
    → Upload photos, record observations
  → PATCH /api/experiments/<id> (stage: documentation)
    → Mark as complete, archive result
  → Gamification: award "First Experiment" badge, add points
```

### Asking Kama (AI Assistant)

```
User → POST /api/ask
  → Auth validation
  → Extract glaze IDs from message (optional)
  → Context retriever fetches relevant glaze data
  → Chemistry engine adds UMF context if applicable
  → Build system prompt with ceramic domain knowledge
  → Send to LLM (Ollama local or Claude cloud)
  → Stream response back to client (SSE)
  → Log interaction for analytics
```

## Database Schema

### Core Tables

```sql
-- Users and authentication
users (id, email, name, created_at, studio_id)
subscriptions (id, user_id, tier, status, provider, expires_at)

-- Glaze data
glazes (id, name, family, hex, chemistry, recipe, catalog_code,
        food_safe, cone, atmosphere, base_type, surface, transparency,
        behavior, layering, warning, created_by, created_at)

-- Layering combinations
combinations (id, base, top, type, source, result, risk, effect,
              stage, prediction_grade, created_at)

-- Experiment pipeline
experiments (id, title, glaze_id, stage, status, notes, hypothesis,
             application_method, layer_thickness, firing_log,
             analysis_notes, photos, created_at, completed_at)

-- Studio collaboration
studios (id, name, description, profile, created_at)
studio_members (id, studio_id, user_id, role, joined_at)
lab_assignments (id, studio_id, experiment_id, assigned_to, status)

-- Gamification
user_stats (id, user_id, points, streak_days, total_experiments,
            rank, last_activity)
badges (id, name, description, icon, criteria)
activity_log (id, user_id, action, entity_type, entity_id, points, created_at)

-- Predictions
predictions (id, user_id, combination_id, prediction, confidence,
             actual_result, accuracy, created_at)

-- Firing logs
firings (id, user_id, cone, atmosphere, kiln_type, schedule,
         max_temperature, duration, notes, created_at)

-- Ingredients/materials
ingredients (id, name, oxide_analysis, aliases, safety_rating, source)

-- Chemistry rules
chemistry_rules (id, rule_type, condition, consequence, confidence, source)
```

## Configuration Architecture

OpenGlaze supports multiple runtime modes:

```python
# config/modes.py
MODES = {
    "personal": {
        "database": "sqlite",
        "auth": "local_jwt",
        "billing": "none",
        "ai": "ollama_local",
    },
    "cloud": {
        "database": "postgresql",
        "auth": "ory_kratos",
        "billing": "stripe",
        "ai": "anthropic_claude",
    },
    "docker": {
        "database": "postgresql",
        "auth": "ory_kratos",
        "billing": "stripe",
        "ai": "ollama_local",
    }
}
```

Mode is detected from:
1. `MODE` environment variable
2. Presence of Docker environment markers
3. Database URL scheme (sqlite:// vs postgresql://)

## Security Model

### Authentication

- **Personal mode**: JWT tokens with local user table
- **Cloud/Docker mode**: Ory Kratos identity server with session cookies

### Authorization

- Role-based access control (RBAC) for studios
- Resource ownership checks on all mutations
- API rate limiting per user/IP

### Data Protection

- Passwords hashed with bcrypt (local auth)
- SQL injection protection via parameterized queries (SQLAlchemy)
- XSS protection via Content Security Policy headers
- CSRF tokens for state-changing operations

## Scalability Considerations

### Current Design (Single Instance)

- Single Flask process handles all requests
- In-memory caching for Ceramics Foundation data
- SQLite for personal mode, PostgreSQL for cloud
- File uploads stored locally (configurable S3)

### Future Scaling Path

1. **Horizontal scaling**: Add Gunicorn workers behind load balancer
2. **Caching layer**: Redis for session storage and query caching
3. **Background jobs**: Celery for AI inference and batch processing
4. **CDN**: CloudFront/Cloudflare for static assets and uploads
5. **Read replicas**: PostgreSQL read replicas for analytics queries

## Deployment Patterns

### Personal (Development)

```
[User Browser] ←→ [Flask Dev Server :8767] ←→ [SQLite file]
```

### Docker (Small Studio)

```
[User Browser] ←→ [nginx :443] ←→ [Flask :8768]
                           ↓
                    [PostgreSQL :5432]
                    [Ory Kratos :4433]
                    [Mailhog :8025]
```

### Cloud (SaaS)

```
[Users] ←→ [Cloudflare CDN] ←→ [Load Balancer]
                                      ↓
                              [Flask Instance × N]
                                      ↓
                              [PostgreSQL Primary]
                                      ↓
                              [PostgreSQL Replicas]
```

## Technology Decisions

| Decision | Rationale |
|----------|-----------|
| Flask over Django/FastAPI | Simplicity, explicit control, large ecosystem |
| Vanilla JS over React/Vue | Zero build step, fast load, easy to self-host |
| SQLite option | Zero-config personal use, file-based portability |
| Ory Kratos | Open-source identity, self-hostable, standards-compliant |
| SQLAlchemy 2.0 | Modern ORM, SQLite + PostgreSQL support |
| Docker Compose | One-command full stack, reproducible deployments |
| YAML for recipes | Human-readable, version-controllable, no DB needed |

## Monitoring and Observability

### Health Checks

- `/health` — Application and database connectivity
- `/health/db` — Database-specific health
- `/health/ai` — LLM provider connectivity

### Logging

- Structured JSON logging in production
- Request/response logging with correlation IDs
- Error tracking with stack traces

### Metrics (Future)

- Prometheus metrics endpoint
- Request latency histograms
- Database query performance
- Active user counts
