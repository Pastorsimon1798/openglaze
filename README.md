# OpenGlaze

<p align="center">
  <img src="frontend/icon-192.png" alt="OpenGlaze — open source ceramic glaze calculator and recipe manager" width="120">
</p>

<p align="center">
  <strong>Free ceramic glaze calculator, recipe manager, and UMF analyzer.<br>100% open source. Self-hosted. No paywalls.</strong>
</p>

<p align="center">
  <a href="https://github.com/Pastorsimon1798/openglaze/actions/workflows/ci.yml">
    <img src="https://github.com/Pastorsimon1798/openglaze/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/Pastorsimon1798/openglaze/releases">
    <img src="https://img.shields.io/github/v/release/Pastorsimon1798/openglaze?include_prereleases" alt="Latest Release">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.12+-blue.svg" alt="Python 3.12+">
  </a>
  <a href="https://www.docker.com/">
    <img src="https://img.shields.io/badge/Docker-Ready-blue" alt="Docker Ready">
  </a>
  <a href="https://github.com/Pastorsimon1798/openglaze/stargazers">
    <img src="https://img.shields.io/github/stars/Pastorsimon1798/openglaze" alt="GitHub Stars">
  </a>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#features">Features</a> •
  <a href="#documentation">Docs</a> •
  <a href="#self-hosting">Self-Host</a> •
  <a href="#contributing">Contribute</a>
</p>

---

## Overview

OpenGlaze is a **free, open-source ceramic glaze management system** for potters, ceramic artists, and studios. It combines a **UMF calculator**, **CTE analysis engine**, **computational recipe optimizer**, and **AI-powered glaze consulting** — all in one self-hosted application.

### 30-second example: diagnose a crazing glaze

1. Enter a glaze recipe such as feldspar/silica/whiting/kaolin.
2. OpenGlaze calculates UMF, oxide roles, SiO₂:Al₂O₃ ratio, and estimated CTE.
3. If the glaze fit looks risky, the optimizer suggests material adjustments for the next test tile.
4. You still fire a real test tile — but you waste less clay, material, and kiln space getting there.

**Popular starting points:** [Ceramic glaze calculator](https://openglaze.com/ceramic-glaze-calculator.html) · [UMF calculator](https://openglaze.com/umf-calculator.html) · [CTE calculator](https://openglaze.com/cte-glaze-calculator.html) · [Glazy companion](https://openglaze.com/glazy-alternative.html) · [Self-hosted glaze software](https://openglaze.com/self-hosted-glaze-software.html)

Built by potters, for potters. Your glaze recipes stay on your infrastructure. No subscriptions. No feature gates. MIT licensed.

**Why OpenGlaze?**

- 🏠 **Own your data** — Self-host on your own server. Recipes never leave your studio.
- 🔓 **Truly open** — MIT licensed, no proprietary lock-in, full source code available
- 🧮 **Computational chemistry** — UMF calculator, CTE prediction, and recipe optimizer using stoichiometric analysis — not guesswork
- 🧠 **AI-powered** — Kama assistant understands glaze chemistry and answers technical questions
- 🎨 **Studio-ready** — Multi-user collaboration, role-based access, shared glaze libraries
- ☕ **Free forever** — No paywalls, no subscriptions, no feature gates. Voluntary support only.

## What is OpenGlaze?

OpenGlaze is a **ceramic glaze calculator and recipe management tool** designed for anyone working with glazes:

- **Hobby potters** who want to understand their glazes at the molecular level
- **Studio ceramicists** managing dozens of recipes and test firings
- **Educators** teaching glaze chemistry with transparent, reproducible tools
- **Production potters** optimizing recipes for consistency and cost

At its core, OpenGlaze automates the chemistry that ceramicists have historically done by hand or with spreadsheets: calculating Unity Molecular Formula (UMF), estimating thermal expansion coefficient (CTE), and suggesting material adjustments to achieve target properties.

### How It Compares

| Tool | What It Does | How OpenGlaze Fits |
|------|-------------|-------------------|
| **Glazy** | Recipe database & community | Export from Glazy → analyze & optimize in OpenGlaze |
| **DigitalFire** | Ceramic chemistry education & reference | Deep educational content; OpenGlaze is the practical calculator |
| **INSIGHT** | Desktop glaze calculation software | Similar chemistry engine; OpenGlaze is web-based, open-source, and self-hosted |
| **HyperGlaze** | Recipe database | Import recipes into OpenGlaze for UMF analysis |

OpenGlaze is not a replacement for these tools — it complements them. Many users maintain their recipe libraries in Glazy and use OpenGlaze for computational analysis and optimization.

## Quick Start

### Docker (Recommended, 2 minutes)

The default Docker path is a single-user, self-hosted SQLite install with persistent Docker volumes. It does not require PostgreSQL or Ory Kratos.

```bash
# Clone the repository
git clone https://github.com/Pastorsimon1798/openglaze.git
cd openglaze

# Copy environment file and set a real SECRET_KEY before public use
cp .env.example .env

# Start OpenGlaze
docker compose up -d

# Access at http://localhost:8768
curl http://localhost:8768/health
```

### Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up database and seed with default studio glazes
python seed_data.py

# Run
python server.py
```

Open http://localhost:8768 in your browser.

## Features

<table>
<tr>
<td width="50%">

### 🎨 Glaze Management
- Store unlimited glazes with chemistry, recipes, and visual references
- Track family relationships and base types
- **UMF calculator** with automatic oxide analysis and SiO₂:Al₂O₃ ratio
- Recipe scaling and batch calculator with cost estimation
- Food safety and cone range annotations (cone 06 through 10)

</td>
<td width="50%">

### 🔬 Chemistry Engine
- **UMF calculator** — Unity Molecular Formula from any batch recipe
- **CTE analysis** — Thermal expansion coefficient prediction for crazing/shivering risk
- Glaze compatibility analysis and material substitution suggestions
- **Recipe optimizer** — Computational suggestions to hit target CTE, surface (matte/glossy), or durability
- Batch reporting with cost estimation
- Oxide analysis with automatic role classification (flux, stabilizer, glass former)

</td>
</tr>
<tr>
<td width="50%">

### 🧠 AI Assistant (Kama)
- Context-aware glaze consulting
- Streaming responses for real-time help
- Local LLM support (Ollama) or cloud (Claude)
- Chemistry-aware prompt injection
- Experiment suggestion engine

</td>
<td width="50%">

### 🧪 Experiment Pipeline
- 6-stage workflow: Ideation → Prediction → Application → Firing → Analysis → Documentation
- Photo documentation at each stage
- Structured firing log integration
- Result comparison and archiving
- Reproducibility tracking

</td>
</tr>
<tr>
<td width="50%">

### 👥 Studio Collaboration
- Studio groups and invite-code joining
- Lab assignment tracking
- Shared experiment views
- Simple local-token identity for lightweight collaboration
- Role-based authorization and comment threads are roadmap items

</td>
<td width="50%">

### 🎮 Gamification
- Points and streak tracking
- Achievement badges
- Activity leaderboards
- Experiment milestones
- Community challenges

</td>
</tr>
</table>

### More Features

- 🧮 **Recipe Optimizer** — Computational glaze recipe optimizer suggesting exact material adjustments to hit target CTE, surface, or durability without physical testing
- 📸 **Photo Documentation** — Gallery view across multiple firings
- 🔥 **Firing Logs** — Atmosphere, cone, and schedule tracking
- 🧮 **Layering Tracker** — Document and predict base/top combinations
- 💾 **Import/Export** — JSON/CSV export in the legacy dashboard; Glazy/INSIGHT import is a roadmap integration
- 📊 **Progress views** — Track experiments and prediction activity where auth is enabled
- 📱 **PWA** — Install as an app on mobile/desktop
- ⌨️ **Command Palette** — Quick navigation with ⌘K
- 🔐 **Auth** — simple local auth for studio features; Ory/Kratos support is experimental


## Learn by search intent

These pages are built to answer the exact questions potters and AI answer engines ask:

| Search intent | OpenGlaze page |
| --- | --- |
| Ceramic glaze calculator | <https://openglaze.com/ceramic-glaze-calculator.html> |
| UMF calculator for ceramics | <https://openglaze.com/umf-calculator.html> |
| Glaze recipe calculator | <https://openglaze.com/glaze-recipe-calculator.html> |
| Glaze CTE calculator | <https://openglaze.com/cte-glaze-calculator.html> |
| Glazy alternative / companion | <https://openglaze.com/glazy-alternative.html> |
| DigitalFire companion | <https://openglaze.com/digitalfire-companion.html> |
| Open-source pottery software | <https://openglaze.com/open-source-pottery-software.html> |
| Self-hosted glaze software | <https://openglaze.com/self-hosted-glaze-software.html> |

AI crawlers and answer engines can use [`docs/llms.txt`](docs/llms.txt), [`docs/llms-full.txt`](docs/llms-full.txt), and [`docs/ai.txt`](docs/ai.txt) for canonical project facts.

## Tech Stack

| Component | Technology | License |
|-----------|------------|---------|
| Backend | Flask 3.x (Python) | MIT |
| Frontend | Vanilla JS SPA | MIT |
| Database | SQLite | Public Domain |
| Auth | Simple local tokens; Ory hooks experimental | Apache 2.0 |
| AI | Ollama (local) / Anthropic Claude (cloud) | — |
| Import/Export | JSON/CSV export in legacy dashboard; broader Glazy/INSIGHT import is roadmap | MIT |
| Chemistry | Custom UMF Engine | MIT |
| Container | Docker + Compose | — |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Client Layer                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Browser    │  │   PWA App    │  │   API Clients│      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                     Flask Application                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  Glazes  │ │Chemistry │ │    AI    │ │ Templates│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Studios  │ │   Auth   │ │Analytics │ │  Uploads │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└────────────────────┬────────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────────┐
│                      Data Layer                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐  │
│  │SQLite/   │  │Ory       │  │Ceramics Foundation Data  │  │
│  │PostgreSQL│  │Kratos    │  │(Materials, Recipes, etc.)│  │
│  └──────────┘  └──────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](docs/installation.md) | Docker and manual setup guides |
| [Configuration](docs/configuration.md) | Environment variables and settings |
| [API Reference](docs/API.md) | REST API endpoints and examples |
| [Architecture](docs/architecture.md) | System design and data flow |
| [User Guide](docs/user-guide.md) | End-user feature walkthrough |
| [Development](docs/development.md) | Contributing and local dev setup |
| [Self-Hosting](docs/self-hosting.md) | Production deployment guide |
| [Support](docs/support.md) | Voluntary support for the project |
| [Changelog](CHANGELOG.md) | Version history and release notes |

## Self-Hosting

OpenGlaze is designed for self-hosting. All components are open source.

### Minimum Requirements

- 1 CPU core
- 1 GB RAM
- 10 GB storage
- Docker & Docker Compose

### Deployment Options

| Platform | Cost | Difficulty | Best For |
|----------|------|------------|----------|
| VPS (Hetzner, DO, Linode) | $5-20/mo | Medium | Full control |
| Render / Railway / Fly.io | $7-25/mo | Easy | Managed platforms |
| Raspberry Pi / Bare Metal | $0 | Hard | Offline/local use |

See [docs/self-hosting.md](docs/self-hosting.md) for detailed deployment instructions for each platform.

## Support the Project

OpenGlaze is free and open source. If it saves you materials, time, or a failed kiln load, consider supporting ongoing development:

- **[Buy me a coffee](https://ko-fi.com/yourname)** *(update with your link)*
- **[Patreon](https://patreon.com/yourname)** *(update with your link)*
- **[GitHub Sponsors](https://github.com/sponsors/yourname)** *(update with your link)*

No pressure — the tool is yours either way.

## Customizing Studio Profiles

Studio profiles live in `ceramics-foundation/studios/`. To add your own:

1. Copy `studios/default/` → `studios/your-studio/`
2. Edit `profile.json`, `clays.json`, `kilns.json`
3. Add glaze collections to `glazes/*.yaml`
4. Update `seed_data.py` or create your own seed script

No code changes required — everything is data-driven.

## Data

The `ceramics-foundation/` directory contains canonical ceramic reference data:

- **30+ materials** with oxide analyses and aliases
- **19 oxides** with molecular weights, roles, and safety ratings
- **Firing schedules** for cone 06 through 10
- **UMF target ranges** and surface prediction thresholds
- **Layering rules** and material substitutions
- **Studio recipes** in YAML format

All data is versioned, sourced, and cited. See [ceramics-foundation/](ceramics-foundation/) for the full dataset.

## Templates

Pre-built glaze collections:

- **Cone 10 Reduction (Community)** — 15 classic reduction glazes
- **Cone 6 Oxidation (Community)** — 12 electric kiln glazes
- **Default Studio** — Configurable template for any studio

See [templates/](templates/) and [ceramics-foundation/recipes/](ceramics-foundation/recipes/).

## Testing

```bash
# Run the full test suite
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=. --cov-report=html
```

111 tests covering:
- Kama AI context injection and streaming
- Chemistry context retrieval and UMF calculation
- Recipe optimizer (target CTE, surface, alkali, running risk)
- Flask route imports and response formats
- System prompt generation and database schema

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick start:

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/openglaze.git
cd openglaze

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Make changes and submit a PR
```

## Security

See [SECURITY.md](SECURITY.md) for our security policy and vulnerability reporting process.

## Support

Questions, bug reports, and feature requests:

- [GitHub Discussions](https://github.com/Pastorsimon1798/openglaze/discussions) — Community help
- [GitHub Issues](https://github.com/Pastorsimon1798/openglaze/issues) — Bug reports and feature requests

### Support the Project

OpenGlaze is free and open source under the MIT license. If this tool saved you materials, time, or a failed kiln load, consider supporting its continued development:

- [☕ Buy me a coffee on Ko-fi](https://ko-fi.com/yourname)
- [🎨 Support on Patreon](https://patreon.com/yourname)
- [⭐ Sponsor on GitHub](https://github.com/sponsors/yourname)

No pressure — the tool is yours either way.

## License

- **Code**: [MIT License](LICENSE) — Free to use, modify, distribute
- **Templates**: CC-BY-4.0 — Free with attribution
- **Documentation**: CC-BY-4.0

## Acknowledgments

- The ceramics community for sharing knowledge and recipes
- Contributors who have helped build OpenGlaze
- [Ceramic Arts Network](https://ceramicartsnetwork.org/) for glaze chemistry references
- [Digitalfire](https://digitalfire.com/) for oxide data and UMF methodology

---

<p align="center">
  <strong>Built with ❤️ for the ceramics community</strong>
</p>

<p align="center">
  <a href="https://github.com/Pastorsimon1798/openglaze">GitHub</a> •
  <a href="https://github.com/Pastorsimon1798/openglaze/discussions">Discussions</a> •
  <a href="https://openglaze.com">Website</a>
</p>
