# Changelog

All notable changes to OpenGlaze will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Unified GlazeLab + OpenGlaze codebase — merged R&D features into production infrastructure
- Chemistry engine with UMF calculation, compatibility analysis, and thermal expansion
- Kama AI assistant with streaming responses and context-aware glaze consulting
- 6-stage experiment pipeline (Ideation → Prediction → Application → Firing → Analysis → Documentation)
- Gamification system with points, streaks, badges, and leaderboards
- Studio collaboration with member management and lab assignments
- Prediction market for human vs AI glaze outcome predictions
- Simulation engine for glaze chemistry modeling
- Flexible billing with Stripe, PayPal, BTCPay, and manual invoicing
- Generic studio profiles — replaceable templates for any ceramics studio
- Community glaze templates (Cone 10 Reduction, Cone 6 Oxidation)
- Ceramics Foundation data inlined (30+ materials, 19 oxides, firing schedules)
- Docker Compose stack with PostgreSQL, Kratos auth, and Mailhog
- PWA support with service worker and manifest
- Command palette (⌘K) for quick navigation
- 38 test suite covering AI, chemistry, and Flask routes

### Changed
- Merged from two separate repositories into unified codebase
- Eliminated git submodules — all ceramic data now inlined
- Renamed all "Clay on First" references to "Default Studio"
- Updated schema to support combined GlazeLab + OpenGlaze features
- Lazy app factory pattern to eliminate import-time side effects

### Fixed
- Schema drift in test suite resolved by dynamically loading canonical schema
- Import-time side effects eliminated for testability
- Docker networking updated for unified service names

### Removed
- GlazeLab repository (all data and features preserved in merge)
- `_deprecated/human-door/` stale documentation
- Empty folders and unused configuration files

## [1.0.0] - 2026-04-24

### Added
- Initial release of unified OpenGlaze
- Flask backend with REST API
- Vanilla JS frontend SPA
- SQLite/PostgreSQL dual database support
- Ory Kratos authentication integration
- Basic glaze CRUD operations
- Firing log tracking
- Photo documentation with gallery
- Recipe calculator with batch sizing
- Layering combination tracker
- User management and subscriptions
- MIT license

[Unreleased]: https://github.com/Pastorsimon1798/openglaze/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/Pastorsimon1798/openglaze/releases/tag/v1.0.0
