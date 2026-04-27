# SEO and AI Discovery Implementation Plan

**Goal:** Build the public discovery layer for OpenGlaze so GitHub, Google, and AI answer engines can understand and cite the project accurately.

**Architecture:** Add dependency-free static docs/pages under `docs/`, lightweight repository metadata files, and regression tests that lock key SEO/GEO claims. Avoid runtime changes except links from the docs landing page.

**Tech Stack:** Static HTML/Markdown/text, Python pytest contract tests, GitHub repository metadata via `gh`.

---

### Task 1: Lock SEO contract expectations

**Files:**
- Create: `tests/test_seo_contracts.py`

**Steps:**
1. Add tests for required SEO pages, canonical URLs, page titles, meta descriptions, JSON-LD, sitemap inclusion, and AI text truth.
2. Run `python3 -m pytest tests/test_seo_contracts.py -q` and confirm failure before page creation.

### Task 2: Create static SEO landing pages

**Files:**
- Create: `docs/ceramic-glaze-calculator.html`
- Create: `docs/umf-calculator.html`
- Create: `docs/glaze-recipe-calculator.html`
- Create: `docs/cte-glaze-calculator.html`
- Create: `docs/glazy-alternative.html`
- Create: `docs/digitalfire-companion.html`
- Create: `docs/open-source-pottery-software.html`
- Create: `docs/self-hosted-glaze-software.html`
- Modify: `docs/index.html`

**Steps:**
1. Generate unique pages with visible answers, FAQ schema, SoftwareApplication/WebPage JSON-LD, internal links, and GitHub/self-host CTAs.
2. Add cards/links from the homepage.
3. Run the SEO tests.

### Task 3: Refresh AI and crawler files

**Files:**
- Modify: `docs/ai.txt`
- Modify: `docs/llms.txt`
- Create: `docs/llms-full.txt`
- Modify: `docs/robots.txt`
- Modify: `docs/sitemap.xml`

**Steps:**
1. Correct test count and storage/deployment claims.
2. Add answer-engine snippets and canonical page map.
3. Add sitemap entries for all pages with `2026-04-26` lastmod.
4. Run the SEO tests.

### Task 4: Add GitHub growth metadata

**Files:**
- Create: `CITATION.cff`
- Create: `.github/dependabot.yml`
- Create: `docs/social-preview.svg`
- Modify: `docs/index.html` OpenGraph image if needed.

**Steps:**
1. Add citation metadata, dependency update monitoring, and a social preview asset.
2. Set repository topics with `gh repo edit`.
3. Verify repo metadata via `gh repo view`.

### Task 5: Full verification and publish

**Commands:**
- `ruff check .`
- latest Black `--check .`
- `python3 -m pytest tests/ -q`
- Docker build/run smoke
- Push branch and update PR #3
