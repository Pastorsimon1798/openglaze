# Ceramics Foundation Workspace

Domain knowledge for ceramics vision pipeline, caption generation, and AI Glaze Lab. Cone 10 reduction.

---

## Folder Map

```
ceramics-foundation/
├── CLAUDE.md              # This file
├── CONTEXT.md             # Task routing
├── INDEX.md               # Quick reference
├── taxonomies/            # Classification for vision AI
│   ├── glazes.md          # 32 community glazes + surface quality
│   ├── vessel-anatomy.md  # Forms, parts, profiles
│   └── colors.md          # ~123 mineral/ceramic color terms
├── chemistry/             # Technical reference
│   ├── glaze-chemistry.md # UMF, substitutions
│   ├── firing-guide.md    # Cone temps, schedules
│   └── material-safety.md # OSHA, PPE, ventilation
├── recipes/               # Glaze recipes by source
│   ├── laguna/
│   ├── aardvark/
│   └── studio/
├── glaze-lab/             # AI Glaze Lab system
│   ├── reverse-engineering.md
│   ├── prediction-framework.md
│   ├── first-principles.md
│   └── experiment-design.md
├── content/               # Voice and brand
│   └── voice-rules.md     # Anti-robot writing rules
├── business/              # Market and pricing
│   ├── market-analysis.md
│   └── pricing-guide.md
└── _raw/                  # Archived intermediates
```

---

## Triggers

| Keyword | Action |
|---------|--------|
| `identify glaze` | Load `taxonomies/glazes.md` |
| `classify form` | Load `taxonomies/vessel-anatomy.md` |
| `generate caption` | Load `content/voice-rules.md` + taxonomies |
| `price piece` | Load `business/pricing-guide.md` |
| `safety check` | Load `chemistry/material-safety.md` |
| `reverse engineer` | Load `glaze-lab/reverse-engineering.md` |

---

## What to Load

| Task | Load | Skip |
|------|------|------|
| Vision pipeline | `taxonomies/*.md` | business, content |
| Caption generation | `content/voice-rules.md`, `taxonomies/*.md` | chemistry, lab |
| Business ops | `business/*.md` | taxonomies, lab |
| Technical ref | `chemistry/*.md` | business, content |
| Glaze lab | `glaze-lab/*.md`, `chemistry/glaze-chemistry.md` | business, content |

---

## Studio Context

**Firing:** Cone 10 reduction (gas kiln)
**Bisque:** Electric cone 06
**Inventory:** 44 community glazes (28 cone 10, 16 cone 6)

**Critical:** All color descriptions assume reduction atmosphere (muted vs bright oxidation).

---

## Sources

**Technical:** Digitalfire, Ceramic Materials Workshop, Glazy.org, Ceramic Arts Network, OSHA 29 CFR 1910.1053 | **Business:** ClayShare, Instagram (@cerafica_design), Old Forge Creations | **Taxonomy:** Laguna Clay, Aardvark Clay, myartlesson.com, Gotheborg.com
