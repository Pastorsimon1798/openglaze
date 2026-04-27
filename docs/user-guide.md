# OpenGlaze User Guide

Complete guide to using OpenGlaze for glaze management, experimentation, and studio collaboration.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Managing Glazes](#managing-glazes)
3. [The Chemistry Engine](#the-chemistry-engine)
4. [Layering and Combinations](#layering-and-combinations)
5. [The Experiment Pipeline](#the-experiment-pipeline)
6. [Working with Kama (AI)](#working-with-kama-ai)
7. [Studio Collaboration](#studio-collaboration)
8. [Firing Logs](#firing-logs)
9. [Photo Documentation](#photo-documentation)
10. [Gamification](#gamification)
11. [Tips and Best Practices](#tips-and-best-practices)

## Getting Started

### First Login

When you first access OpenGlaze:

1. Create an account or log in
2. Your studio profile is automatically created with default settings
3. The database is seeded with the community glaze collection
4. You're ready to start managing glazes!

### Navigation Overview

The interface consists of:

- **Header** — Search (⌘K), AI assistant toggle, PWA install button
- **Sidebar** — Main views: Combinations, All Glazes, Photos, Studio, Experiments
- **Main Content** — Context-aware based on selected view
- **Command Palette** — Press ⌘K (or Ctrl+K) for quick navigation

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘K` / `Ctrl+K` | Open command palette |
| `⌘/` / `Ctrl+/` | Toggle sidebar |
| `Esc` | Close modals/panels |
| `G` then `G` | Go to Glazes |
| `G` then `C` | Go to Combinations |
| `G` then `E` | Go to Experiments |

## Managing Glazes

### Adding a Glaze

1. Navigate to **All Glazes**
2. Click **Add Glaze**
3. Fill in the required fields:
   - **Name** — e.g., "Ash Glaze #3"
   - **Recipe** — Batch percentages or gram amounts
   - **Cone** — Firing temperature (e.g., 10)
   - **Atmosphere** — Oxidation, reduction, or neutral
4. Optional fields add richness:
   - **Family** — celadon, tenmoku, shino, etc.
   - **Base Type** — porcelain, stoneware, earthenware
   - **Surface** — glossy, matte, satin, textured
   - **Food Safe** — Mark if tested food-safe
   - **Behavior** — Running, breaking, pooling notes

### Recipe Formats

OpenGlaze accepts recipes in multiple formats:

**Percentage format:**
```
Feldspar: 45%
Silica: 30%
Whiting: 15%
Kaolin: 10%
```

**Gram format:**
```
Feldspar: 450g
Silica: 300g
Whiting: 150g
Kaolin: 100g
```

**UMF format:**
```
SiO2: 3.2
Al2O3: 0.45
CaO: 0.55
```

### Editing and Organizing

- Click any glaze card to view details
- Edit recipes, update photos, add notes
- Use tags and families to organize collections
- Filter by cone, atmosphere, surface, or food safety

### Importing Recipes

Import from common formats:

- **Glazy CSV** — Export from glazy.com
- **Digitalfire INSIGHT** — .dfd files
- **YAML** — OpenGlaze native format

## The Chemistry Engine

### UMF Calculation

The Unity Molecular Formula (UMF) normalizes glaze recipes to compare them on equal footing.

**How to calculate:**
1. Open a glaze detail view
2. Click **Calculate UMF**
3. The system analyzes your recipe and displays:
   - Silica:Alumina ratio
   - Predicted surface (glossy/matte/satin)
   - Thermal expansion coefficient

**Interpreting UMF:**

| SiO₂:Al₂O₃ Ratio | Typical Surface |
|-------------------|-----------------|
| < 5 | Matte to satin |
| 5–8 | Satin to glossy |
| > 8 | Very glossy, may run |

| RO Group | Typical Behavior |
|----------|-----------------|
| High CaO (0.5+) | Hard, durable, may crawl |
| High KNaO (0.3+) | Glossy, softer, more fluid |
| High MgO (0.3+) | Matte, opaque, lower expansion |
| High BaO | Toxic in raw form, unique surfaces |

### Compatibility Analysis

Before layering two glazes:

1. Go to **Combinations** view
2. Select a **Base glaze** and **Top glaze**
3. Click **Analyze Compatibility**
4. Review the report:
   - Thermal expansion match
   - Maturity overlap at target cone
   - Predicted interaction effects
   - Risk level (low/medium/high)

**Warning signs:**
- Thermal expansion difference > 1.0 → shivering or crazing risk
- Maturing temperatures differ by > 1 cone → poor fit
- Both glazes are runners → pooling/dripping risk

### Batch Calculator

Scale recipes for any batch size:

1. Open a glaze
2. Click **Batch Calculator**
3. Enter desired batch size (grams or pounds)
4. View scaled amounts and optional cost estimate

### Recipe Optimizer

The optimizer computationally suggests exact material adjustments to hit target glaze properties — reducing the number of physical test firings needed.

**When to use it:**
- Your glaze crazes and you need to lower CTE to match your clay body
- You want to shift a glossy glaze toward satin or matte
- You're worried about excessive running at your firing temperature
- You need to reduce alkali content for better durability

**How to use it:**
1. Open a glaze detail view
2. Click **Optimize Recipe**
3. Select your target:
   - **Target CTE** — Enter the exact CTE of your clay body (e.g., 6.5)
   - **Reduce CTE** — Lower thermal expansion to reduce crazing risk
   - **Increase CTE** — Raise thermal expansion to reduce shivering risk
   - **More Matte** — Increase alumina relative to silica
   - **More Glossy** — Increase silica relative to alumina
   - **Reduce Alkali** — Lower KNaO for better durability
   - **Reduce Running** — Reduce fluidity to prevent pooling
4. Review ranked suggestions with predicted outcomes
5. Choose a suggestion and fire a test tile to confirm

**Understanding the results:**

| Column | Meaning |
|--------|---------|
| Recipe | The reformulated recipe with adjusted percentages |
| Change | What was modified (e.g., "Replace silica with kaolin (50% swap)") |
| Predicted CTE | Thermal expansion of the reformulated glaze |
| Predicted Surface | Expected surface finish (matte/satin/glossy) |
| Score | Higher = closer to target (threshold-crossing bonuses applied) |

**Important:** The optimizer predicts chemistry, not firing behavior. Always fire a test tile before committing to a reformulated recipe. Surface prediction depends on firing schedule, cooling rate, and application thickness.

## Layering and Combinations

### Documenting a Combination

1. In **Combinations** view, click **New Combination**
2. Select base and top glazes
3. Document your prediction:
   - What effect do you expect?
   - Risk level assessment
4. After firing, update with actual results

### Combination Types

| Type | Description |
|------|-------------|
| Research-backed | Confirmed by published sources or extensive testing |
| User-prediction | Your hypothesis before firing |
| Confirmed | You've fired it and documented results |
| Surprise | Unexpected result worth noting |

### Layering Tips

- **Thin base, thick top** — Most combinations work best with a thin base coat
- **Test tiles first** — Always test on small tiles before full pieces
- **Note application method** — Dipping, brushing, spraying affect results
- **Document everything** — Thickness, temperature, atmosphere all matter

## The Experiment Pipeline

### The 6 Stages

OpenGlaze structures glaze development into a repeatable pipeline:

```
Ideation → Prediction → Application → Firing → Analysis → Documentation
```

### Stage 1: Ideation

**What to document:**
- What are you trying to achieve?
- Reference glazes or photos
- Hypothesis about the outcome

**Example:**
> "I want to create a deep copper red by starting with a celadon base and adding 1.5% copper carbonate. Hypothesis: Reduction at cone 10 will produce a rich red with minimal pinholing."

### Stage 2: Prediction

**What to document:**
- Expected color, texture, and surface
- Potential problems
- Comparison to similar glazes in your library

**Use Kama:** Ask the AI for predictions based on your recipe.

### Stage 3: Application

**What to document:**
- Application method (dip, brush, spray)
- Number of coats
- Layer thickness
- Clay body used
- Bisque temperature

### Stage 4: Firing

**What to document:**
- Cone reached
- Atmosphere (oxidation/reduction)
- Kiln type
- Firing schedule (ramp rates, holds, cooling)
- Total firing time
- Any issues (power outages, early shutdowns)

### Stage 5: Analysis

**What to document:**
- Photos (multiple angles, close-ups)
- Color accuracy notes
- Surface quality (smooth, pinholed, crawling)
- Comparison to prediction
- Adjustments needed

### Stage 6: Documentation

**What to document:**
- Final recipe with any modifications
- Firing notes for replication
- Lessons learned
- Archive or share with studio

### Experiment Best Practices

- **One variable at a time** — Change only one thing between tests
- **Label everything** — Tiles, test pieces, photos
- **Take photos in consistent lighting** — Natural daylight, neutral background
- **Keep a physical notebook too** — Technology fails; paper doesn't

## Working with Kama (AI)

### What Kama Knows

Kama has access to:
- Your glaze library (if you provide glaze IDs)
- Ceramics Foundation reference data (materials, oxides, schedules)
- Chemistry rules and compatibility guidelines
- General ceramic glaze chemistry knowledge

### Effective Questions

**Good questions:**
- "What would 2% rutile do to this celadon?" (with glaze selected)
- "Why is my glaze crawling at cone 6?"
- "Compare the UMF of these two glazes and predict how they'd layer"
- "Suggest a substitute for gerstley borate in this recipe"

**Less effective questions:**
- "Make me a good glaze" (too vague)
- "What is clay?" (too basic, use a search engine)

### Understanding Kama's Limitations

- Kama provides guidance, not guarantees
- Always test predictions on tiles before full pieces
- Kama doesn't know your specific materials' impurities
- Local geology and water chemistry affect results

### Privacy Note

- With **local Ollama**: All queries stay on your machine
- With **cloud Claude**: Queries are sent to Anthropic's API (see their privacy policy)

## Studio Collaboration

### Creating a Studio

1. Go to **Studio** view
2. Click **Create Studio**
3. Enter studio name and description
4. Configure profile (cone, atmosphere, kiln type)

### Inviting Members

1. In Studio settings, click **Invite Member**
2. Enter their email address
3. Assign a role:
   - **Owner** — Full control, member management
   - **Admin** — Manage members, experiments, glazes
   - **Member** — Create and edit glazes and experiments
   - **Viewer** — Read-only access

### Shared Resources

Studio members share:
- Glaze library (with edit permissions based on role)
- Experiment history
- Firing logs
- Photo galleries
- Leaderboards

### Lab Assignments

Assign experiments to specific members:
1. Create an experiment
2. Click **Assign to Member**
3. Select member and set deadline
4. Member receives notification

## Firing Logs

### Creating a Firing Log

1. Go to **Firing Logs** (from Studio view)
2. Click **New Firing**
3. Enter details:
   - Date and kiln
   - Cone and atmosphere
   - Loading notes
   - Schedule (or select from presets)

### Firing Schedules

Ceramics Foundation includes preset schedules:

| Schedule | Use Case |
|----------|----------|
| Fast Bisque | Earthenware, single fire |
| Slow Bisque | Large pieces, prone to cracking |
| Cone 6 Oxidation | Standard electric firing |
| Cone 10 Reduction | Gas kiln reduction |
| Crystalline Slow Cool | Zinc-silicate crystal growth |

### Attaching Results

Link firing logs to experiments and glazes:
- Tag which glazes were in the firing
- Attach photos of the kiln opening
- Note any kiln-related issues (hot spots, element wear)

## Photo Documentation

### Uploading Photos

1. Open a glaze or experiment
2. Click **Add Photo**
3. Upload image (JPG, PNG, WebP supported)
4. Add caption and metadata:
   - Firing it relates to
   - Clay body
   - Application notes

### Photo Organization

- Photos are organized by glaze, experiment, or firing
- Filter by date, cone, or atmosphere
- Compare side-by-side (select multiple photos)

### Best Practices for Glaze Photos

- **Lighting**: Natural daylight or 5000K LED
- **Background**: Neutral gray or white
- **Angle**: 45° to show surface texture
- **Close-ups**: Macro for detail shots
- **Consistency**: Same setup for comparison shots

## Gamification

### Earning Points

| Activity | Points |
|----------|--------|
| Add a glaze | 10 |
| Create an experiment | 25 |
| Complete an experiment (all 6 stages) | 100 |
| Document a firing | 15 |
| Upload a photo | 5 |
| Correctly predict a combination | 50 |
| Daily login | 5 |

### Streaks

- Log in and perform an activity daily to build streaks
- Streak milestones: 7 days, 30 days, 100 days
- Streaks multiply point earnings

### Badges

Unlock badges for achievements:

| Badge | Requirement |
|-------|-------------|
| First Glaze | Add your first glaze |
| Experimenter | Complete 10 experiments |
| Chemist | Calculate UMF for 50 glazes |
| Photographer | Upload 100 photos |
| Streak Master | 30-day activity streak |
| Prediction Pro | 10 correct combination predictions |
| Studio Founder | Create a studio with 3+ members |

### Leaderboards

- Studio-wide leaderboards (monthly and all-time)
- Rank titles: Novice Potter → Apprentice → Journeyman → Master → Glaze Wizard

## Tips and Best Practices

### For Beginners

1. **Start with known recipes** — Use community templates as baselines
2. **Document everything** — The most valuable data is the data you have
3. **Test on tiles** — Never experiment on finished work
4. **Learn UMF basics** — Understanding chemistry helps predict results
5. **Join a studio** — Collaboration accelerates learning

### For Advanced Users

1. **Build a test matrix** — Systematically vary one oxide at a time
2. **Use the prediction market** — Challenge yourself and others
3. **Contribute to Ceramics Foundation** — Submit verified data
4. **Automate with API** — Build tools on top of OpenGlaze
5. **Host for your community** — Set up instances for local guilds

### For Studio Managers

1. **Standardize naming** — Consistent glaze names prevent confusion
2. **Archive old recipes** — Keep history without cluttering active library
3. **Set up firing schedules** — Preset schedules ensure consistency
4. **Review analytics** — Track which glazes are used most
5. **Backup regularly** — Export data periodically

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Glaze not showing in list | Check filter settings, verify permissions |
| UMF calculation seems wrong | Verify recipe format and material names |
| Kama not responding | Check AI provider settings in config |
| Photos not uploading | Check file size (max 10MB) and format |
| Can't invite studio member | Verify they have an OpenGlaze account |
| Database errors on startup | Delete `glaze.db` and re-run `seed_data.py` |

---

**Need more help?** Visit [GitHub Discussions](https://github.com/Pastorsimon1798/openglaze/discussions) or check the [API Reference](API.md) for developers.
