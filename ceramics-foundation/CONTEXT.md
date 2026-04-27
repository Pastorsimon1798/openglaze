# Ceramics Foundation - Task Routing

> **DIRECTION NOTE (2026-04-27):** OpenGlaze is now a generic, studio-agnostic project.
> All studio-specific data (Default Studio / Clay on First / Long Beach) has been removed
> from user-facing files. The app ships 44 traditional/published glazes across cone 6 and
> cone 10 with no proprietary or commercial formulas. Do NOT reference any specific studio,
> manufacturer product codes, or studio-invented glaze names in new work.
> See `frontend/scripts/data.js` and `core/templates/community-glazes.yaml` for current data.

**Type:** Foundation workspace (Layer 3 domain knowledge)
**Used by:** Pipeline workspaces (Instagram, Glaze Experiments, etc.)

This workspace has no `stages/` - it's reference material. Pipelines load relevant sections as context.

---

## Task Routing

| Task | Load File | Purpose |
|------|-----------|---------|
| Identify glaze | `taxonomies/glazes.md` | Match visual to 32 studio glazes |
| Describe surface | `taxonomies/glazes.md` (section 4) | Surface sheen, variation, movement |
| Classify vessel | `taxonomies/vessel-anatomy.md` | Form classification + decision trees |
| Identify color | `taxonomies/colors.md` | ~123 mineral/ceramic color terms |
| Generate caption | `content/voice-rules.md` + taxonomies | Anti-robot rules + terminology |
| Price piece | `business/pricing-guide.md` | Cost formulas, wholesale/retail |
| Research market | `business/market-analysis.md` | Competition, hashtags, strategy |
| Understand firing | `chemistry/firing-guide.md` | Cone temps, schedules, atmosphere |
| Substitute materials | `chemistry/glaze-chemistry.md` | One-to-one ratios + calculations |
| Safety check | `chemistry/material-safety.md` | PPE, ventilation, toxic materials |
| Reverse engineer glaze | `glaze-lab/reverse-engineering.md` | Visual clues to recipe |
| Predict outcome | `glaze-lab/prediction-framework.md` | Forecast recipe changes |
| Learn glaze theory | `glaze-lab/first-principles.md` | Glass formation, UMF, expansion |
| Design experiments | `glaze-lab/experiment-design.md` | Ranked test suggestions |
| Find recipe | `recipes/` subdirectories | By source (laguna/aardvark/studio) |

## Domain Areas

| Area | Files | Contains |
|------|-------|----------|
| Vision AI | `taxonomies/*.md` | Glazes, anatomy, colors |
| Technical | `chemistry/*.md` | UMF, firing, safety |
| Business | `business/*.md` | Pricing, market |
| Content | `content/*.md` | Voice rules |
| Lab | `glaze-lab/*.md` | Experiments, theory |

## Studio Context

Cone 10 reduction, Default Studio (Long Beach). All color descriptions assume reduction atmosphere. Glaze effects specific to reduction: carbon trapping, copper flashing, luster development.

## File Dependencies

| File | References |
|------|-----------|
| `taxonomies/glazes.md` | `chemistry/glaze-chemistry.md` |
| `taxonomies/colors.md` | `taxonomies/glazes.md` |
| `content/voice-rules.md` | All taxonomy files |
| `business/market-analysis.md` | `content/voice-rules.md` |

---

## Expansion Guide

**Adding new domain areas:**
- New taxonomy? → `taxonomies/`
- New chemistry topic? → `chemistry/`
- New glaze tests? → Create `glaze-experiments` pipeline workspace (don't add stages here)
- New market data? → `business/`

**When to create a pipeline workspace instead:**
- Has workflow with inputs → processing → outputs
- Needs stages/ directory
- Transforms data (e.g., test results → conclusions)

**This workspace grows by adding reference files, not stages.**
