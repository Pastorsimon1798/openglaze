# SEO and AI Discovery Design

## Goal
Make OpenGlaze easier to discover, cite, understand, and share across GitHub, Google, and AI answer engines without overstating current product capabilities.

## Recommended approach
Use a static-content growth layer that sits on top of the verified app: dedicated search-intent landing pages, machine-readable/citation-friendly metadata, repo hygiene files, and tests that prevent truth drift. This keeps the implementation low-risk and dependency-free while improving the public surface dramatically.

## Components
- GitHub trust surface: `CITATION.cff`, Dependabot config, repo topics, and a reusable social preview asset.
- SEO pages: static HTML pages for the main ceramicist search intents: ceramic glaze calculator, UMF calculator, glaze recipe calculator, CTE calculator, Glazy companion, DigitalFire companion, open-source pottery software, and self-hosted glaze software.
- AI/GEO surface: refresh `llms.txt`, add `llms-full.txt`, correct `ai.txt`, and make claims match the runnable product.
- Discovery wiring: index page cards, sitemap entries, canonical URLs, structured data, and robots references.
- Regression coverage: tests for canonical pages, metadata, sitemap inclusion, AI files, and stale claim prevention.

## Acceptance criteria
- Search pages exist with unique title/description/canonical/schema and visible GitHub/Docker CTAs.
- `ai.txt` and `llms.txt` no longer claim PostgreSQL as supported default or stale test counts.
- Sitemap includes all new pages with current lastmod.
- Repo has citation/dependabot/social-preview assets.
- Tests, formatting, lint, and Docker smoke still pass.
