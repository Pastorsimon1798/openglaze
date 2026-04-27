# Development Guide

Guide for developers contributing to OpenGlaze.

## Table of Contents

1. [Development Environment](#development-environment)
2. [Project Structure](#project-structure)
3. [Running Tests](#running-tests)
4. [Adding Features](#adding-features)
5. [Database Changes](#database-changes)
6. [Frontend Development](#frontend-development)
7. [AI Integration](#ai-integration)
8. [Release Process](#release-process)

## Development Environment

### Prerequisites

- Python 3.12+
- Docker & Docker Compose (for full stack testing)
- Node.js 20+ (optional, for frontend linting)

### Setup

```bash
# Clone repository
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install dev dependencies (if separate)
pip install pytest pytest-cov black ruff

# Set up pre-commit hooks (optional, requires .pre-commit-config.yaml)
# pre-commit install
```

### Running Locally

```bash
# Quick start (SQLite, no auth)
python seed_data.py
python server.py

# Full stack (PostgreSQL, Kratos)
docker-compose up -d
```

### Environment Variables for Development

Create `.env`:

```bash
FLASK_ENV=development
BASE_URL=http://localhost:8767
DATABASE_URL=sqlite:///glaze.db
SECRET_KEY=dev-secret-key-not-for-production
MODE=personal

# For AI testing
OLLAMA_HOST=http://localhost:11434
ANTHROPIC_API_KEY=sk-ant-your-key
```

## Project Structure

```
openglaze/
├── server.py              # Flask app factory and routes
├── auth.py                # Authentication wrappers
├── seed_data.py           # Database seeder
├── core/
│   ├── schema.sql         # Database schema (single source of truth)
│   ├── glazes/            # Glaze CRUD logic
│   ├── combinations/      # Layering logic
│   ├── experiments/       # Pipeline stage management
│   ├── chemistry/         # UMF, compatibility, batch calc
│   ├── ai/                # Kama assistant + context retrieval
│   ├── auth/              # JWT / Ory Kratos integration
│   ├── security/          # Rate limiting, CSP, validation
│   ├── studios/           # Studio and member management
│   ├── gamification/      # Points, badges, leaderboards
│   ├── predictions/       # Prediction market logic
│   └── simulation/        # Chemistry simulation
├── frontend/              # Vanilla JS SPA
│   ├── index.html         # App shell
│   ├── styles/            # CSS modules
│   ├── scripts/           # JS feature modules
│   └── sw.js              # Service worker
├── ceramics-foundation/   # Canonical ceramic data
│   ├── data/              # JSON reference data
│   ├── recipes/           # YAML recipe collections
│   ├── taxonomies/        # Classifications
│   └── studios/           # Studio profile templates
├── tests/                 # Test suite
│   ├── conftest.py        # Shared fixtures
│   ├── test_chemistry.py
│   ├── test_ai.py
│   ├── test_routes.py
│   └── ...
├── docs/                  # Documentation
├── templates/             # Shareable glaze collections
├── config/                # Environment and mode detection
├── docker-compose.yml     # Full stack orchestration
├── Dockerfile             # Application container
└── requirements.txt       # Python dependencies
```

## Running Tests

### Full Suite

```bash
pytest tests/ -v
```

### With Coverage

```bash
pytest tests/ --cov=. --cov-report=html --cov-report=term
open htmlcov/index.html  # View coverage report
```

### Specific Test Files

```bash
pytest tests/test_chemistry.py -v -k "umf"
pytest tests/test_ai.py -v
pytest tests/test_routes.py -v
```

### Test Database

Tests use an in-memory SQLite database created from `core/schema.sql`. The `conftest.py` fixture dynamically loads the canonical schema, ensuring tests always match production.

### Writing Tests

```python
# tests/test_feature.py
import pytest

def test_glaze_creation(client, auth_headers):
    """Test creating a new glaze."""
    response = client.post('/api/glazes',
        json={
            'name': 'Test Glaze',
            'recipe': 'Feldspar: 50%, Silica: 50%',
            'cone': '10',
            'atmosphere': 'reduction'
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    data = response.get_json()
    assert data['name'] == 'Test Glaze'
    assert 'umf' in data
```

### Test Fixtures (conftest.py)

Key fixtures:

- `client` — Flask test client with in-memory DB
- `auth_headers` — Valid JWT authorization headers
- `sample_glaze` — Pre-created glaze for testing
- `sample_user` — Authenticated test user

## Adding Features

### Backend Feature Pattern

1. **Define the data model** — Update `core/schema.sql` if needed
2. **Create the module** — Add to `core/<feature>/`
3. **Add routes** — Register in `server.py`
4. **Write tests** — Add to `tests/test_<feature>.py`
5. **Document** — Update API.md and user-guide.md

Example: Adding a "Favorite Glazes" feature

```python
# core/favorites.py
from flask import g

def add_favorite(glaze_id: int, user_id: int) -> dict:
    db = g.db
    cursor = db.cursor()
    cursor.execute('''
        INSERT INTO favorites (user_id, glaze_id, created_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT DO NOTHING
    ''', (user_id, glaze_id))
    db.commit()
    return {"status": "added"}

def get_favorites(user_id: int) -> list:
    db = g.db
    cursor = db.cursor()
    cursor.execute('''
        SELECT g.* FROM glazes g
        JOIN favorites f ON g.id = f.glaze_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
    ''', (user_id,))
    return [dict(row) for row in cursor.fetchall()]
```

```python
# In server.py
from core.favorites import add_favorite, get_favorites

@app.route('/api/favorites', methods=['GET'])
@require_auth
def list_favorites():
    return jsonify(get_favorites(g.user_id))

@app.route('/api/favorites/<int:glaze_id>', methods=['POST'])
@require_auth
def create_favorite(glaze_id):
    return jsonify(add_favorite(glaze_id, g.user_id)), 201
```

### Frontend Feature Pattern

1. **Add UI components** — Update `frontend/index.html` or create partial
2. **Add styles** — Update appropriate `frontend/styles/*.css`
3. **Add JavaScript** — Create `frontend/scripts/<feature>.js`
4. **Register in app** — Import in main script bundle

## Database Changes

### Schema Migrations

OpenGlaze uses a simple migration system in `server.py`:

```python
def _run_migrations(db):
    """Run any pending schema migrations."""
    cursor = db.cursor()
    
    # Check current schema version
    cursor.execute("PRAGMA user_version")
    version = cursor.fetchone()[0]
    
    if version < 2:
        # Migration: add favorites table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER REFERENCES users(id),
                glaze_id INTEGER REFERENCES glazes(id),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, glaze_id)
            )
        ''')
        cursor.execute("PRAGMA user_version = 2")
        db.commit()
```

### Adding a New Table

1. Add to `core/schema.sql` (for new installs)
2. Add migration to `_run_migrations()` (for existing installs)
3. Update test fixtures if needed
4. Document in architecture.md

## Frontend Development

### CSS Architecture

Modular CSS in `frontend/styles/`:

```
styles/
├── variables.css      # CSS custom properties (colors, spacing, typography)
├── reset.css          # Normalize/reset
├── typography.css     # Font rules
├── layout.css         # Grid, flexbox, sidebar, header
├── components.css     # Buttons, cards, inputs, badges
├── gamification.css   # Points, badges, leaderboards
├── prediction.css     # Prediction market UI
└── tips.css           # Tooltips and help text
```

### JavaScript Architecture

Feature-based modules:

```javascript
// frontend/scripts/glazes.js
export const GlazeManager = {
    async loadGlazes(filters = {}) {
        const params = new URLSearchParams(filters);
        const response = await fetch(`/api/glazes?${params}`);
        return response.json();
    },
    
    async createGlaze(data) {
        const response = await fetch('/api/glazes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return response.json();
    }
};
```

### Theme System

CSS variables support light/dark/system modes:

```css
:root {
  --color-bg: #faf8f5;
  --color-text: #1a1a1a;
  --color-primary: #5a9078;
}

[data-theme="dark"] {
  --color-bg: #1a1a1a;
  --color-text: #faf8f5;
  --color-primary: #7ab89a;
}
```

Toggle via JavaScript:

```javascript
document.documentElement.setAttribute('data-theme', 'dark');
```

## AI Integration

### Adding a New LLM Provider

1. Create adapter in `core/ai/providers/<provider>.py`
2. Implement standard interface:

```python
class BaseProvider:
    def chat(self, messages: list, stream: bool = False) -> str | Iterator[str]:
        raise NotImplementedError
    
    def is_available(self) -> bool:
        raise NotImplementedError
```

3. Register in `core/ai/manager.py`
4. Add config options to `.env.example`

### Context Injection

The context retriever fetches relevant data before sending to the LLM:

```python
def build_context(glaze_ids: list[int] = None, query: str = "") -> str:
    context_parts = []
    
    if glaze_ids:
        glazes = fetch_glazes(glaze_ids)
        context_parts.append(format_glazes_for_prompt(glazes))
    
    if is_chemistry_question(query):
        context_parts.append(fetch_chemistry_rules(query))
    
    return "\n\n".join(context_parts)
```

## Release Process

1. **Update version** — Update `__version__` in `server.py`
2. **Update CHANGELOG.md** — Document all changes
3. **Run tests** — `pytest tests/` must pass
4. **Update docs** — Ensure docs reflect new features
5. **Create git tag**:
   ```bash
   git tag -a v1.1.0 -m "Release v1.1.0"
   git push origin v1.1.0
   ```
6. **Create GitHub Release** — With release notes and binaries if applicable
7. **Update Docker image** — Build and push to registry

### Version Numbering

Follows [Semantic Versioning](https://semver.org/):

- `MAJOR` — Breaking changes
- `MINOR` — New features, backward compatible
- `PATCH` — Bug fixes

## Code Style

### Python

- PEP 8 compliant
- Black formatter: `black .`
- Ruff linter: `ruff check .`
- Type hints encouraged for new code
- Docstrings for public functions

### JavaScript

- ES6+ features
- 2-space indentation
- Semicolons required
- Single quotes for strings

### CSS

- CSS custom properties for theming
- BEM-like naming: `.component__element--modifier`
- Mobile-first responsive design
