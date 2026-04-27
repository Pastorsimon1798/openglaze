# Test Tile Visual Analysis

> **DEPRECATION NOTICE (2026-04-27):** This document references studio-specific glaze names
> (Long Beach Black, etc.) that have been removed from the project. The visual analysis
> methodology remains valid. For current glaze names, see `frontend/scripts/data.js`.

**Firing:** Cone 10 Reduction (Gas)
**Analysis Date:** 2026-03-19
**Test Tile Photo:** [33 tiles on white tile board]

---

## Methodology

**Multi-Model Vision AI Analysis:**
- **Kimi K2.5** (`moonshotai/kimi-k2.5`) - Detailed color analysis, surface effects, material identification
- **Gemini 3 Flash** (`google/gemini-3-flash-preview`) - Ceramic-specific terminology, glaze family identification

**Synthesis Framework:** Ceramic Glaze Reverse-Engineering systematic analysis

**Model Comparison:**
| Aspect | Kimi K2.5 | Gemini 3 Flash |
|--------|-----------|----------------|
| Ceramic Terminology | Good | Excellent (reduction atmosphere, carbon trapping, Rayleigh scattering) |
| Color Precision | Detailed descriptions | Munsell-like precision |
| Surface Analysis | Gloss/matt identified | Satin/semi-matt/orange peel distinctions |
| Special Effects | Oil spots, crystallization noted | Micro-crystallization, teadust crystals explained |
| Token Usage | Hit 4000 limit (cut off) | Complete response (2041 tokens) |

---

## Visual Reference Data - All 33 Glazes

### Row 1: Clears, Whites, Blacks

#### 1. Lucid Clear (Laguna LG-27)
```yaml
visual_reference:
  primary_color: Crystal clear with no color cast
  color_family: Clear/Transparent
  surface:
    sheen: High gloss
    texture: Smooth glass
    depth: Transparent, shows clay body clearly
  application_effects:
    pooling: Minimal - maintains clarity
    breaking: None - consistent transparency
  special_effects: None - pure clear base
  firing_atmosphere: Neutral - does not interact with reduction
  notes: Standard transparent base, exact Laguna match
```

#### 2. Tom Coleman Clear (Aardvark TC-103)
```yaml
visual_reference:
  primary_color: Clear with faint blue-green cast on porcelain
  color_family: Clear with celadon undertones
  surface:
    sheen: Glossy
    texture: Smooth
    depth: Translucent with subtle color
  application_effects:
    pooling: Slight green intensification where thick
    breaking: Minimal color shift
  special_effects: Faint celadon-like green on white clay
  firing_atmosphere: Sensitive to reduction (slight green from iron)
  notes: Stiffer melt than Lucid, great response to stains/oxides
```

#### 3. Choinard White
```yaml
visual_reference:
  primary_color: Opaque milky white
  color_family: White/Matte
  surface:
    sheen: Satin-matte
    texture: Smooth, velvety
    depth: Opaque, flat
  application_effects:
    pooling: No visible variation
    breaking: None - consistent coverage
  special_effects: None
  firing_atmosphere: Neutral
  notes: Likely Zircopax or tin-based opacifier
```

#### 4. Long Beach Black
```yaml
visual_reference:
  primary_color: Jet black, saturated
  color_family: Black
  surface:
    sheen: High gloss
    texture: Smooth glass
    depth: Opaque, deep
  application_effects:
    pooling: No variation - fully saturated
    breaking: None
  special_effects: None
  firing_atmosphere: Neutral - fully saturated colorants mask atmosphere
  notes: Iron/manganese/cobalt combination for depth
```

#### 5. Larry's Grey
```yaml
visual_reference:
  primary_color: Cool dove grey to gunmetal
  color_family: Grey/Neutral
  surface:
    sheen: Semi-matt
    texture: Smooth
    depth: Semi-opaque, breaks translucent on edges
  application_effects:
    pooling: Darkens where thick
    breaking: Translucent at edges reveals warm undertones
  special_effects: Subtle color variation with thickness
  firing_atmosphere: Reduction-sensitive (iron/manganese interaction)
  notes: Community recipe, iron + manganese combination
```

#### 6. White Crawl
```yaml
visual_reference:
  primary_color: White to off-white
  color_family: White/Texture
  surface:
    sheen: Variable - glossy on islands, matte on exposed clay
    texture: High-surface tension "lichen" crawl pattern
    depth: Glaze beads into islands
  application_effects:
    pooling: Glaze pulls back, creates intentional bare clay
    breaking: Not applicable - crawling is primary effect
  special_effects: Intentional crawling texture
  firing_atmosphere: Neutral
  notes: High-surface tension formula, intentional texture effect
```

#### 7. Tighty Whitey
```yaml
visual_reference:
  primary_color: Stark opaque white
  color_family: White/Matte
  surface:
    sheen: Satin-matte
    texture: Smooth, flat
    depth: Opaque, no movement
  application_effects:
    pooling: None
    breaking: None - consistent coverage
  special_effects: None
  firing_atmosphere: Neutral
  notes: High-opacifier formula, stable and unmoving
```

### Row 2: Greens and Shinos

#### 8. Froggy
```yaml
visual_reference:
  primary_color: Deep forest green
  color_family: Green/Saturated
  surface:
    sheen: High gloss
    texture: Smooth
    depth: Translucent with depth
  application_effects:
    pooling: Darkens significantly where pooled
    breaking: Minimal - maintains saturation
  special_effects: None
  firing_atmosphere: Reduction (likely chrome/tin or copper green)
  notes: Chrome-tin pink inhibitor may create depth, or copper-based
```

#### 9. Toady
```yaml
visual_reference:
  primary_color: Olive-drab to moss green
  color_family: Green/Earth
  surface:
    sheen: Semi-matt to satin
    texture: Mottled, orange peel
    depth: Semi-opaque with variation
  application_effects:
    pooling: Subtle darkening
    breaking: Minimal
  special_effects: Variegated, organic surface
  firing_atmosphere: Reduction
  notes: Earthy green, likely rutile or iron-based with other colorants
```

#### 10. Luster Shino
```yaml
visual_reference:
  primary_color: Pale cream to pearlescent grey
  color_family: Shino/Luster
  surface:
    sheen: Satin with subtle metallic luster
    texture: Smooth
    depth: Semi-opaque
  application_effects:
    pooling: Slight color shift
    breaking: May show carbon trap
  special_effects: Subtle metallic iridescence
  firing_atmosphere: Reduction critical for luster development
  notes: Shino family with reduction-cool luster effect
```

#### 11. Malcolm's Shino (Malcom Davis)
```yaml
visual_reference:
  primary_color: Rusty orange to creamy white
  color_family: Shino/American
  surface:
    sheen: Semi-gloss
    texture: Variable, may crawl
    depth: Semi-opaque with carbon trapping
  application_effects:
    pooling: White areas where thin, orange where thick
    breaking: Carbon trap creates black speckles
  special_effects: Carbon trapping (black speckles in white/orange)
  firing_atmosphere: Reduction essential for carbon trap
  notes: Famous American shino, soda feldspar base
```

#### 12. Jensen Blue (Aardvark CTG 04)
```yaml
visual_reference:
  primary_color: Variegated slate blue and mossy brown
  color_family: Blue/Variegated
  surface:
    sheen: Satin-matte
    texture: Smooth with color variation
    depth: Semi-opaque
  application_effects:
    pooling: Darkens in recesses
    breaking: Brown color shift at edges
  special_effects: Variegated surface, breaking reveals brown undertones
  firing_atmosphere: Reduction-sensitive
  notes: Named after Jensen, exact Aardvark match
```

#### 13. Ming Green
```yaml
visual_reference:
  primary_color: Deep emerald green
  color_family: Green/Celadon
  surface:
    sheen: High gloss
    texture: Smooth
    depth: Translucent with significant pooling
  application_effects:
    pooling: Extreme - darkens dramatically in recesses
    breaking: May show lighter green at edges
    thickness_variation: Runs on porcelain
  special_effects: Significant movement and pooling
  firing_atmosphere: Reduction (iron-based celadon)
  notes: Classic celadon family, high fluidity on porcelain
```

### Row 3: Celadons and Blues

#### 14. Amber Celadon
```yaml
visual_reference:
  primary_color: Honey to amber
  color_family: Celadon/Amber
  surface:
    sheen: Glossy to satin
    texture: Smooth
    depth: Translucent with significant variation
  application_effects:
    pooling: Dark tobacco color in recesses
    breaking: Straw color on ridges
    thickness_variation: High - dramatic color shift
  special_effects: Classic breaking and pooling
  firing_atmosphere: Reduction (iron-saturated celadon)
  notes: High iron content (3-5%) creates amber tones
```

#### 15. Celadon (Laguna LG-10/14/22)
```yaml
visual_reference:
  primary_color: Traditional pale jade to seafoam green
  color_family: Celadon/Traditional
  surface:
    sheen: Glossy
    texture: Smooth
    depth: Translucent, shows clay body
  application_effects:
    pooling: Darker green where thick
    breaking: Lighter at thin edges
  special_effects: Classic celadon translucency
  firing_atmosphere: Reduction (1-2% iron creates green)
  notes: Traditional low-iron celadon
```

#### 16. Grey Blue Celadon (Laguna LG-14)
```yaml
visual_reference:
  primary_color: Smoky steel blue
  color_family: Celadon/Blue
  surface:
    sheen: Glossy
    texture: Smooth
    depth: Translucent
  application_effects:
    pooling: Deep blue-grey in recesses
    breaking: Lighter blue-grey at edges
  special_effects: Subtle color variation with thickness
  firing_atmosphere: Reduction
  notes: Iron-cobalt combination or cobalt-enhanced celadon
```

#### 17. Shocking Purple
```yaml
visual_reference:
  primary_color: Deep violet
  color_family: Purple/Manganese
  surface:
    sheen: Satin to semi-matt
    texture: Smooth
    depth: Opaque
  application_effects:
    pooling: Minimal variation
    breaking: None
  special_effects: None
  firing_atmosphere: Reduction (manganese/cobalt)
  notes: Manganese dioxide + cobalt combination
```

#### 18. Aegean Blue (Aardvark CTG 21)
```yaml
visual_reference:
  primary_color: Saturated navy blue
  color_family: Blue/Cobalt
  surface:
    sheen: High gloss
    texture: Smooth glass
    depth: Deep and saturated
  application_effects:
    pooling: No visible variation
    breaking: None
  special_effects: None
  firing_atmosphere: Neutral (cobalt stable in both atmospheres)
  notes: Cobalt-based, exact Aardvark match
```

#### 19. Chun Blue (Aardvark TC-102 or CTG 12)
```yaml
visual_reference:
  primary_color: Opalescent sky blue
  color_family: Chun/Opalescent
  surface:
    sheen: Glossy with milky depth
    texture: Smooth
    depth: Translucent with visual depth
  application_effects:
    pooling: Subtle variation
    breaking: May show purple/red flash at edges
  special_effects: Rayleigh scattering from micro-bubbles, purple flash in reflected light
  firing_atmosphere: Reduction (copper + iron combination)
  notes: Classic Chun blue with purple flash
```

#### 20. Oilspot Blue/Green
```yaml
visual_reference:
  primary_color: Deep mottled teal to navy
  color_family: Blue/Green/Oilspot
  surface:
    sheen: High gloss
    texture: Smooth with oil spots
    depth: Semi-opaque with variation
  application_effects:
    pooling: Creates oil spot development
    breaking: Minimal
  special_effects: Oil spots (metallic silver/green spots)
  firing_atmosphere: Reduction critical for oil spot formation
  notes: High iron + titanium or manganese for oil spots
```

### Row 4: Iron Glazes

#### 21. Cosmic Brown
```yaml
visual_reference:
  primary_color: Dark chocolate with metallic flecks
  color_family: Brown/Crystalline
  surface:
    sheen: Satin-matte
    texture: Micro-crystallization
    depth: Semi-opaque
  application_effects:
    pooling: Subtle darkening
    breaking: Minimal
  special_effects: Metallic flecks, micro-crystallization
  firing_atmosphere: Reduction with slow cooling
  notes: Iron-silicate crystal formation
```

#### 22. Iron Red
```yaml
visual_reference:
  primary_color: Burnt sienna to brick red
  color_family: Red/Iron
  surface:
    sheen: Matt to stone-like
    texture: Smooth to slightly textured
    depth: Opaque
  application_effects:
    pooling: Minimal variation
    breaking: None
  special_effects: Iron precipitation during slow cooling
  firing_atmosphere: Reduction with controlled cooling
  notes: High iron (8-10%) with specific cooling schedule
```

#### 23. Teadust (Aardvark TC-104)
```yaml
visual_reference:
  primary_color: Black with olive-green to gold flecks
  color_family: Black/Teadust
  surface:
    sheen: Satin
    texture: Crystalline spots
    depth: Opaque base with crystal surface
  application_effects:
    pooling: Crystal development where thick
    breaking: Minimal
  special_effects: Iron-silicate crystals (olive/gold teadust spots)
  firing_atmosphere: Reduction with specific cooling cycle
  notes: Classic teadust, Aardvark TC-104 match
```

#### 24. Tenmoku (Laguna LG-1 or Aardvark CTG 07/15)
```yaml
visual_reference:
  primary_color: Raven black breaking to oil-spot brown
  color_family: Tenmoku/Black
  surface:
    sheen: Glossy
    texture: Smooth with oil spots
    depth: Semi-opaque with breaking
  application_effects:
    pooling: Black where thick
    breaking: Rust/brown at edges and thin spots
  special_effects: Oil spots, classic breaking
  firing_atmosphere: Reduction (6-10% iron)
  notes: Classic tenmoku, high iron reduction glaze
```

#### 25. Mellow Yellow
```yaml
visual_reference:
  primary_color: Ochre to mustard
  color_family: Yellow/Matte
  surface:
    sheen: Opaque matt
    texture: Smooth, stone-like
    depth: Flat and stable
  application_effects:
    pooling: None
    breaking: None
  special_effects: None
  firing_atmosphere: Neutral to reduction
  notes: Stable, non-running yellow
```

#### 26. Honey Luster
```yaml
visual_reference:
  primary_color: Warm golden-brown
  color_family: Luster/Gold
  surface:
    sheen: Shimmering micro-crystals
    texture: Smooth with luster
    depth: Semi-opaque
  application_effects:
    pooling: Slight variation
    breaking: None
  special_effects: Micro-crystallization creates lustrous effect
  firing_atmosphere: Reduction cooling critical
  notes: Crystal development during cooling creates luster
```

#### 27. Strontium Crystal Magic (Pete Pinnell)
```yaml
visual_reference:
  primary_color: Pale tan to cream
  color_family: Crystal/Strontium
  surface:
    sheen: Satin to glossy
    texture: Active crystallization
    depth: Semi-opaque with crystal growth
  application_effects:
    pooling: Crystal development in recesses
    breaking: None
  special_effects: Visible crystal structures (starbursts, dendrites)
  firing_atmosphere: Reduction with slow cooling for crystals
  notes: Pete Pinnell recipe, Glazy #33211, strontium flux
```

### Row 5: Copper Reds and Specialties

#### 28. John's Red (John Britt)
```yaml
visual_reference:
  primary_color: Oxblood to sang de boeuf
  color_family: Copper Red/Oxblood
  surface:
    sheen: High gloss
    texture: Smooth glass
    depth: Translucent with depth
  application_effects:
    pooling: Red intensifies where thick
    breaking: May shift green at edges (copper re-oxidation)
  special_effects: Copper reduction red, possible green flashing
  firing_atmosphere: Heavy reduction critical (0.5-1.5% copper)
  notes: John Britt recipe, Glazy #398657, difficult to fire consistently
```

#### 29. Pablo's Red
```yaml
visual_reference:
  primary_color: Deep maroon to burgundy
  color_family: Copper Red/Burgundy
  surface:
    sheen: Glossy
    texture: Smooth
    depth: More opaque than John's
  application_effects:
    pooling: Subtle variation
    breaking: Less shifting than John's
  special_effects: Stable copper red
  firing_atmosphere: Heavy reduction
  notes: Related to Panama Red, more stable than John's
```

#### 30. Pinky
```yaml
visual_reference:
  primary_color: Mottled lavender to pink
  color_family: Copper Red/Pink
  surface:
    sheen: Semi-gloss
    texture: Mottled
    depth: Semi-opaque
  application_effects:
    pooling: Subtle color variation
    breaking: None
  special_effects: Softer copper red variant
  firing_atmosphere: Reduction
  notes: Copper red with lower saturation or different chemistry
```

#### 31. Raspberry
```yaml
visual_reference:
  primary_color: Deep magenta to purple
  color_family: Purple/Magenta
  surface:
    sheen: High gloss
    texture: Smooth
    depth: Variegated
  application_effects:
    pooling: Creates variation
    breaking: Minimal
  special_effects: Variegated surface
  firing_atmosphere: Reduction (manganese/copper combination)
  notes: Complex colorant blend
```

#### 32. Sun Valley
```yaml
visual_reference:
  primary_color: Greyish blue with brown speckles
  color_family: Blue/Speckled
  surface:
    sheen: Matt to stony
    texture: Speckled surface
    depth: Opaque
  application_effects:
    pooling: None
    breaking: None
  special_effects: Reactive with iron body (speckles)
  firing_atmosphere: Reduction
  notes: Iron speckles from clay body interaction
```

#### 33. Angel Eyes
```yaml
visual_reference:
  primary_color: Deep midnight blue with floating lighter spots
  color_family: Blue/Oilspot
  surface:
    sheen: High gloss
    texture: Smooth with spots
    depth: Deep with contrast
  application_effects:
    pooling: Spot development
    breaking: None
  special_effects: Oil spots, gas-bubble halos
  firing_atmosphere: Reduction (oil spot formation)
  notes: Similar to oilspot tenmoku but blue base
```

---

## Clay Body Comparison

**Left Side Tiles:** Buff/toasty stoneware
- Shows warmer undertones
- Glazes interact with iron in body
- Carbon trapping more visible

**Right Side Tiles:** White stoneware or porcelain
- Shows cooler, cleaner colors
- Glazes sit on top without interaction
- Translucency more apparent

---

## Reduction Atmosphere Effects Confirmed

1. **Carbon Trapping:** Malcolm's Shino, Luster Shino (black speckles in white/orange)
2. **Oil Spots:** Tenmoku, Angel Eyes, Oilspot Blue/Green (metallic spots)
3. **Celadon Development:** Ming Green, Celadon, Amber Celadon (green from iron reduction)
4. **Copper Red:** John's Red, Pablo's Red (metallic copper red in reduction)
5. **Micro-crystallization:** Cosmic Brown, Teadust, Strontium Crystal Magic
6. **Rayleigh Scattering:** Chun Blue (opalescent milky depth from micro-bubbles)

---

## Application Thickness Effects

### Pooling (Darker in Recesses)
- Ming Green (extreme)
- Amber Celadon (dramatic tobacco/straw contrast)
- Celadon family (subtle)
- Larry's Grey

### Breaking (Color Shift at Edges)
- Tenmoku (rust/brown at edges)
- Amber Celadon (straw on ridges)
- Jensen Blue (brown breaking)
- John's Red (possible green at edges)

### No Movement/Stable
- Long Beach Black (saturated)
- Choinard White (opaque)
- Mellow Yellow (stable matt)

---

## Cross-Reference to Taxonomy

All 33 tiles successfully matched to the 32 studio glazes plus Angel Eyes (33rd entry).

**New Addition:**
- Angel Eyes: Not in original 32-glaze inventory, documented here for taxonomy update

**Visual Data Integration:**
- Primary colors documented for all glazes
- Surface sheen classified (gloss/satin/matte/semi-matt)
- Special effects catalogued (oil spots, carbon trap, crystals, luster)
- Application effects documented (pooling, breaking, thickness variation)

---

## Raw Model Responses

**Kimi K2.5 Response:** `/tmp/kimi_response.json` (truncated at 4000 tokens)
**Gemini 3 Flash Response:** `/tmp/gemini_response.json` (complete, 2041 tokens)

---

## Next Steps

1. ✅ Visual reference data complete for all 33 glazes
2. ⏭️ Integrate visual data into `ceramics-foundation/taxonomies/glazes.md`
3. ⏭️ Archive raw model responses to `archive/visual-analysis-raw/`
4. ⏭️ Update glaze inventory to include Angel Eyes as 33rd entry
