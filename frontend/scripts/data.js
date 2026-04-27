/**
 * OpenGlaze Data - Community glaze database with chemistry, recipes, and combinations
 * Traditional and published glazes across cone 5, 6, and 10
 *
 * All glazes are traditional (centuries-old), published in ceramic literature
 * (John Britt, Pete Pinnell, Malcom Davis, Matt Fiske), or generic chemistry
 * (base + colorant). No studio-specific, proprietary, or commercial formulas.
 *
 * COLORANT RULES: Based on research from DigitalFire, Ceramic Arts Network,
 * John Britt, Glazy.org, Ceramic Materials Workshop, and peer-reviewed
 * ceramic science literature.
 */

const FAMILY_ORDER = ['Reds', 'Yellows', 'Greens', 'Blues', 'Purples', 'Browns', 'Neutrals', 'Whites', 'Clears', 'Shinos', 'Crystals', 'Reactive'];

const COLORANT_RULES = [
    // === IRON ===
    { id: 'iron-reduction-green', rule: 'Iron 1-2% in reduction = celadon/jade green. More iron (3-5%) = darker olive to iron red.', confidence: 'high' },
    { id: 'iron-oxidation-amber', rule: 'Iron in oxidation = amber, brown, tan. Same iron in reduction = green, black, or red.', confidence: 'high' },
    { id: 'iron-high-saturation', rule: 'High iron (8%+) in reduction = tenmoku black with amber breaks. Very predictable.', confidence: 'high' },
    { id: 'iron-kills-copper-red', rule: 'Iron suppresses copper red. Copper red needs iron-free bases. Iron + copper = muddy brown.', confidence: 'high' },
    { id: 'iron-plus-cobalt', rule: 'Iron shifts cobalt from pure blue toward blue-green/teal.', confidence: 'high' },

    // === COPPER ===
    { id: 'copper-reduction-red', rule: 'Copper 0.5-1.5% in heavy reduction = copper red (sang de boeuf). Needs tin oxide 1-2%.', confidence: 'high' },
    { id: 'copper-oxidation-green', rule: 'Copper in oxidation = green (turquoise to emerald). Same copper in reduction = red or purple.', confidence: 'high' },
    { id: 'copper-plus-zinc-green', rule: 'Copper + zinc = turquoise green. Zinc enhances copper greens but destroys copper reds.', confidence: 'high' },
    { id: 'copper-plus-iron', rule: 'Copper over iron-rich glaze = brown/muddy, not purple. Iron interferes with copper color development.', confidence: 'high' },
    { id: 'copper-reduction-sensitive', rule: 'Copper red is extremely reduction-sensitive. Too little reduction = green. Too much = murky metallic.', confidence: 'high' },

    // === COBALT ===
    { id: 'cobalt-stable-blue', rule: 'Cobalt is the most predictable colorant. Always produces blue in any atmosphere at any cone.', confidence: 'high' },
    { id: 'cobalt-over-white', rule: 'Cobalt over white/opaque base = bright, clean blue. The best way to get vivid blue.', confidence: 'high' },
    { id: 'cobalt-over-iron', rule: 'Cobalt over iron base = blue-green to dark navy. Iron shifts cobalt toward green.', confidence: 'high' },
    { id: 'cobalt-plus-manganese', rule: 'Cobalt + manganese = purple-toned blue. Classic combination for purples.', confidence: 'high' },
    { id: 'cobalt-plus-zinc', rule: 'Cobalt in zinc-rich bases = muted violet-blue. Zinc dulls cobalt.', confidence: 'medium' },
    { id: 'cobalt-plus-rutile', rule: 'Cobalt + rutile = mottled, streaky blue with variegation.', confidence: 'medium' },

    // === CHROME ===
    { id: 'chrome-alone-green', rule: 'Chrome oxide alone = green. Stable and predictable in oxidation.', confidence: 'high' },
    { id: 'chrome-tin-pink', rule: 'Chrome 0.2-0.5% + tin 1.5-2% = pink (chrome-tin pink). Needs zinc-free base.', confidence: 'high' },
    { id: 'chrome-zinc-kills-pink', rule: 'Zinc DESTROYS chrome-tin pink. Even small zinc amounts turn pink to brown. Critical rule.', confidence: 'high' },
    { id: 'chrome-zinc-brown', rule: 'Chrome + zinc = brown (not green). Zinc transforms chrome green to brown.', confidence: 'high' },

    // === MANGANESE ===
    { id: 'manganese-oxidation-purple', rule: 'Manganese in oxidation = purple to brown. In reduction = brown, metallic effects.', confidence: 'high' },
    { id: 'manganese-plus-cobalt', rule: 'Manganese + cobalt = purple. The classic purple combination.', confidence: 'high' },
    { id: 'manganese-plus-iron', rule: 'Manganese + iron = deep brown to black. Darkens significantly.', confidence: 'high' },
    { id: 'manganese-high-blister', rule: 'High manganese (>3%) can cause blistering and surface defects.', confidence: 'medium' },

    // === ZINC ===
    { id: 'zinc-color-killer', rule: 'Zinc kills: chrome-tin pink, chrome green. Zinc enhances: copper green, crystallization.', confidence: 'high' },
    { id: 'zinc-preserves-red', rule: 'Zinc-free clears preserve copper red. Zinc-containing clears can shift red.', confidence: 'high' },

    // === RUTILE / TITANIUM ===
    { id: 'rutile-variegation', rule: 'Rutile (TiO2 + iron) creates variegation, mottling, and micro-crystals. Unpredictable but beautiful.', confidence: 'high' },
    { id: 'rutile-plus-iron', rule: 'Rutile + iron = blue-green to teal effects. Titanium-iron interaction.', confidence: 'medium' },
    { id: 'rutile-plus-cobalt', rule: 'Rutile + cobalt = streaky, mottled blue. Titanium disrupts uniform cobalt color.', confidence: 'medium' },
    { id: 'rutile-phototropy', rule: 'Rutile can cause phototropy — glaze looks different colors in different lighting.', confidence: 'medium' },

    // === SHINOS ===
    { id: 'shino-goes-first', rule: 'SHINOS MUST BE THE BASE LAYER. Shino over almost any other glaze crawls or looks terrible.', confidence: 'high' },
    { id: 'shino-carbon-trap', rule: 'Shinos trap carbon in reduction. Thin application = more orange. Thick = more white/gray.', confidence: 'high' },
    { id: 'shino-under-celadon', rule: 'Celadon over shino = jade green with carbon trap patterns showing through. Classic combo.', confidence: 'high' },
    { id: 'shino-under-tenmoku', rule: 'Tenmoku over shino = dark iron pools over warm carbon trap texture.', confidence: 'high' },

    // === TENMOKU ===
    { id: 'tenmoku-iron-rich', rule: 'Tenmoku has 8-10% iron. It dominates any glaze layered over it — expect darkening.', confidence: 'high' },
    { id: 'tenmoku-amber-breaks', rule: 'Tenmoku breaks amber/gold where thin. Over white base, breaks are more visible.', confidence: 'high' },
    { id: 'tenmoku-plus-chun', rule: 'Chun Blue (copper+iron) over Tenmoku = purple flash at boundary where both glazes interact.', confidence: 'high' },

    // === LAYERING PRINCIPLES ===
    { id: 'opaque-under-transparent', rule: 'Opaque base + transparent top = clean, bright color. The best general-purpose layering strategy.', confidence: 'high' },
    { id: 'dark-under-light', rule: 'Dark glaze under light = the dark shows through. Light glaze under dark = dark dominates.', confidence: 'high' },
    { id: 'fluid-over-stiff', rule: 'Fluid glaze over stiff glaze = pooling in recesses, crawling on high spots. Texture matters.', confidence: 'high' },
    { id: 'high-iron-warning', rule: 'Both glazes high in iron = very dark, muddy result. Limit iron to one layer.', confidence: 'high' },
];

const DATA = {
    research_backed: [
        // === CONE 10 COMBINATIONS ===
        {
            id: 1,
            top: "Celadon",
            base: "Classic Shino",
            cone: "10",
            result: "Jade green with warm orange/gray carbon trap patterns showing through thin areas",
            chemistry: "Shino as base prevents crawling; carbon trap shows through translucent celadon; iron in celadon (1-2%) doesn't conflict with shino",
            bestOn: "Textured surfaces, carved decoration",
            risk: "low",
            prediction_grade: "likely",
            application: "Shino base (even coat) → Celadon over (thin to medium)",
            confidence: "high",
            source: "Classic combo — documented across multiple sources"
        },
        {
            id: 2,
            top: "Tenmoku",
            base: "Carbon Trap Shino",
            cone: "10",
            result: "Dark brown/black tenmoku pooling in recesses over iridescent orange/gray shino",
            chemistry: "Shino as base prevents crawling; high-iron tenmoku pools in texture; warm shino shows through where tenmoku thins",
            bestOn: "Sculptural pieces, forms with texture",
            risk: "low",
            prediction_grade: "likely",
            application: "Carbon Trap Shino base → Tenmoku over (thin on high spots)",
            confidence: "high",
            source: "Well-documented shino-under-dark-glaze combo"
        },
        {
            id: 3,
            top: "Chun Blue",
            base: "Classic Shino",
            cone: "10",
            result: "Blue pooling over warm carbon trap shino; cool-warm contrast where Chun is thicker",
            chemistry: "Shino as base prevents crawling; Chun (copper+iron) creates blue tones contrasting with warm shino oranges",
            bestOn: "Vases, tall forms",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Standard shino-under-fluid-glaze pattern"
        },
        {
            id: 4,
            top: "Iron Red",
            base: "Carbon Trap Shino",
            cone: "10",
            result: "Rust red breaking over iridescent shino texture with warm metallic undertones",
            chemistry: "Iron red (8-12% iron) breaks nicely over shino texture; both are warm-toned glazes",
            bestOn: "Accent pieces, decorative ware",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "High-iron glaze over shino — documented pattern"
        },
        {
            id: 5,
            top: "Iron Luster",
            base: "Classic Shino",
            cone: "10",
            result: "Golden amber over warm carbon trap; potentially monotone warm-on-warm",
            chemistry: "Both iron-based warm glazes; similar color temperature may lack contrast",
            bestOn: "Simple forms where subtle warmth works",
            risk: "low",
            prediction_grade: "possible",
            confidence: "medium",
            warning: "May lack visual contrast — two warm glazes can blend together"
        },
        {
            id: 6,
            top: "Jade Green",
            base: "Classic Shino",
            cone: "10",
            result: "Opaque jade green over orange/gray carbon trap patterns",
            chemistry: "Jade green is opaque iron green (3-5% iron in reduction); higher opacity than celadon so less shino shows through",
            bestOn: "Bold pieces where strong color contrast is desired",
            risk: "low",
            prediction_grade: "possible",
            confidence: "medium",
            source: "Similar to celadon-over-shino but more opaque"
        },
        {
            id: 7,
            top: "Copper Red",
            base: "Opaque White",
            cone: "10",
            result: "Bright copper red with clean white breaks at edges",
            chemistry: "White base ensures clean copper red development; zirconium white reflects light through copper red; breaks white where thin",
            bestOn: "Rims, edges where breaking shows",
            risk: "medium",
            prediction_grade: "likely",
            warning: "Copper red needs heavy reduction — if reduction is weak, turns green/gray",
            application: "Opaque White base → Copper Red over",
            confidence: "high",
            source: "Classic copper red over white — textbook combo"
        },
        {
            id: 8,
            top: "Cobalt Blue",
            base: "Opaque White",
            cone: "10",
            result: "Clean, stable cobalt blue over white",
            chemistry: "Cobalt (0.5-1%) over white = most reliable blue in ceramics. Cobalt is atmosphere-stable.",
            bestOn: "Any form, especially functional ware",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Cobalt over white — the most predictable ceramic color"
        },
        {
            id: 9,
            top: "Zinc-Free Clear",
            base: "Copper Red",
            cone: "10",
            result: "Copper red with added gloss and surface protection, no color shift",
            chemistry: "Zinc-free clear preserves true copper red color. Zinc-containing clears would risk shifting red toward brown.",
            bestOn: "Functional ware, any form",
            risk: "low",
            prediction_grade: "likely",
            application: "Copper Red base → Zinc-Free Clear over",
            confidence: "high",
            source: "Zinc-free clear over copper red — standard protection"
        },
        {
            id: 10,
            top: "Zinc-Free Clear",
            base: "Manganese Purple",
            cone: "10",
            result: "Manganese-cobalt purple with added gloss, no color shift",
            chemistry: "Zinc-free clear adds gloss without modifying manganese-cobalt purple",
            bestOn: "Decorative pieces where glossy purple is desired",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Clear over stable purple — straightforward"
        },
        {
            id: 11,
            top: "Chrome-Tin Pink",
            base: "Opaque White",
            cone: "10",
            result: "Soft coral to rose pink with clean white base showing through at breaks",
            chemistry: "Chrome-tin pink NEEDS white base (zinc-free) to develop properly. Opaque White has no zinc.",
            bestOn: "Delicate pieces, functional ware",
            risk: "medium",
            prediction_grade: "likely",
            warning: "Chrome-tin pink needs oxidation for best color; reduction may shift toward gray-green. Zinc destroys this color.",
            confidence: "high",
            source: "Chrome-tin pink over zinc-free white — well-documented requirement"
        },
        {
            id: 12,
            top: "Chun Blue",
            base: "Tenmoku",
            cone: "10",
            result: "Dark brown/black base with purple flash where Chun and Tenmoku interact at the boundary",
            chemistry: "Chun (copper+iron) over high-iron Tenmoku — both are iron-rich. The purple flash happens where copper from Chun meets iron from Tenmoku.",
            bestOn: "Rims, bowls, vertical forms with thin edges",
            risk: "medium",
            prediction_grade: "likely",
            warning: "Run potential — both glazes are fluid. Watch thickness on vertical surfaces.",
            application: "Tenmoku base (thin) → Chun Blue over",
            confidence: "high",
            source: "Well-documented classic combo — copper+iron interaction"
        },
        {
            id: 13,
            top: "Chun Blue",
            base: "Panama Red",
            cone: "10",
            result: "Blue and red boundary with purple transition where glazes overlap",
            chemistry: "Both contain copper — Chun has copper+iron, Panama Red has copper+tin. Where thin, red shows through creating purple transition zone.",
            bestOn: "Pieces where color transitions are desirable",
            risk: "medium",
            prediction_grade: "possible",
            warning: "Two copper glazes may compete — test thickness ratios",
            confidence: "medium",
            source: "Copper-over-copper — less documented but chemically plausible"
        },

        // === CONE 6 OXIDATION COMBINATIONS (electric kiln) ===
        {
            id: 14,
            top: "Cobalt Blue (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Bright, clean cobalt blue over white — most predictable combo at any temperature",
            chemistry: "Cobalt is atmosphere-stable at any cone. Over white, produces the cleanest blue possible.",
            bestOn: "Any form — the most reliable electric kiln combo",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Cobalt over white — works identically at every temperature"
        },
        {
            id: 15,
            top: "Clear (Cone 6)",
            base: "Iron Red (Cone 6)",
            cone: "6",
            result: "Glossy iron red with added surface protection",
            chemistry: "Clear adds gloss without modifying iron red color in oxidation",
            bestOn: "Functional ware, mugs, bowls",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Clear over iron red — standard electric kiln approach"
        },
        {
            id: 16,
            top: "Turquoise (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Clean turquoise blue-green over bright white",
            chemistry: "Copper + zinc over white = turquoise. White base maximizes brightness.",
            bestOn: "Any form where vivid turquoise is desired",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Copper-zinc turquoise over white — well-documented"
        },
        {
            id: 17,
            top: "Copper Green (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Bright emerald green over white — copper in oxidation at its best",
            chemistry: "Copper in oxidation = reliable green. Over white = clean, bright result.",
            bestOn: "Functional ware, decorative pieces",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Copper green over white in oxidation — textbook result"
        },
        {
            id: 18,
            top: "Temmoku (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Dark brown/black with amber breaks over white — dramatic contrast",
            chemistry: "High-iron temmoku breaks amber where thin over white; same principle as cone 10 but slightly lighter",
            bestOn: "Rims, bowls, any form with edges",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Temmoku over white — works at any cone temperature"
        },
        {
            id: 19,
            top: "Celadon (Cone 6)",
            base: "Shino (Cone 6)",
            cone: "6",
            result: "Light jade green over warm shino texture — electric kiln version of the classic combo",
            chemistry: "Mid-range shino as base; celadon (iron green) over shows through translucently. Lighter than cone 10 version.",
            bestOn: "Textured pieces, carved decoration",
            risk: "medium",
            prediction_grade: "possible",
            confidence: "medium",
            source: "Mid-range adaptation of classic celadon-over-shino"
        },

        // === CONE 6 REDUCTION COMBINATIONS (gas kiln) ===
        {
            id: 20,
            top: "Copper Red (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Copper red over white in mid-range reduction — similar to cone 10 but slightly softer",
            chemistry: "Copper red works at cone 6 in reduction. White base ensures clean development.",
            bestOn: "Functional ware with rims where breaks show",
            risk: "medium",
            prediction_grade: "likely",
            warning: "Requires gas kiln with good reduction at cone 6",
            confidence: "high",
            source: "Published in John Britt — The Complete Guide to Mid-Range Glazes"
        },
    ],
    user_predictions: [
        // === CONE 10 ===
        {
            id: 101,
            top: "Celadon",
            base: "Strontium Crystal Matte",
            cone: "10",
            result: "Jade green potentially obscuring crystal formations — celadon may be too opaque",
            chemistry: "Strontium Crystal forms visible crystals; celadon's translucency should allow crystals to show, but may fill texture",
            risk: "medium",
            prediction_grade: "possible",
            confidence: "low",
            warning: "Crystal glazes need specific cooling schedules — celadon over may interfere with crystal growth"
        },
        {
            id: 102,
            top: "Tenmoku",
            base: "Iron Luster",
            cone: "10",
            result: "Dark brown over golden amber — both iron-based, may lack contrast",
            chemistry: "Tenmoku (8-10% iron) over Iron Luster (4-5% iron) — both high-iron glazes stacked = risk of monotone dark brown",
            risk: "high",
            prediction_grade: "unlikely",
            confidence: "low",
            warning: "HIGH IRON WARNING: Both glazes are iron-rich. Likely results in muddy, very dark brown with no visual interest."
        },
        {
            id: 103,
            top: "Copper Red",
            base: "Tea Dust",
            cone: "10",
            result: "Likely muddy brown — copper red suppressed by Tea Dust's ~8% iron",
            chemistry: "IRON KILLS COPPER RED. Tea Dust has ~8% iron which will suppress Copper Red copper development.",
            risk: "high",
            prediction_grade: "unlikely",
            confidence: "medium",
            warning: "IRON KILLS COPPER RED — this combo is likely to fail. Iron in Tea Dust will prevent copper red formation."
        },
        {
            id: 104,
            top: "Celadon",
            base: "Iron Yellow",
            cone: "10",
            result: "Green-yellow chartreuse from iron green + iron yellow combination",
            chemistry: "Both use iron as colorant — celadon has 1-2% iron (green in reduction), Iron Yellow has 4-5% iron (yellow). Combined iron shifts toward chartreuse.",
            risk: "low",
            prediction_grade: "possible",
            confidence: "medium",
            source: "Iron+iron layering — additive iron effect"
        },
        {
            id: 105,
            top: "Tea Dust",
            base: "Tenmoku",
            cone: "10",
            result: "Very dark brown/black — both extremely iron-rich, likely no visual distinction",
            chemistry: "Tea Dust (~8% Fe) + Tenmoku (8-10% Fe) = massive iron overload. Expect near-black with no interesting variation.",
            risk: "high",
            prediction_grade: "unlikely",
            confidence: "low",
            warning: "HIGH IRON WARNING: Two very high-iron glazes stacked. Will be dark, muddy, and uninteresting."
        },
        {
            id: 106,
            top: "Chrome-Tin Raspberry",
            base: "Opaque White",
            cone: "10",
            result: "Deep raspberry to magenta with white breaks; needs oxidation for best pink",
            chemistry: "Chrome-tin raspberry (higher chrome than Chrome-Tin Pink) over zinc-free white. More saturated.",
            risk: "medium",
            prediction_grade: "possible",
            warning: "Chrome-tin needs oxidation. Reduction shifts toward gray. Zinc destroys the color.",
            confidence: "medium",
            source: "Same chemistry as Chrome-Tin Pink but more saturated"
        },
        {
            id: 107,
            top: "Iron-Rutile Brown",
            base: "Opaque White",
            cone: "10",
            result: "Warm brown with rutile variegation over white; cleaner than over dark base",
            chemistry: "Iron-rutile brown over white = warmer, lighter brown with visible rutile streaks",
            risk: "low",
            prediction_grade: "possible",
            confidence: "medium",
            source: "Iron-rutile over white — should maintain variegation"
        },
        {
            id: 108,
            top: "Zinc Clear",
            base: "Copper-Cobalt Blue",
            cone: "10",
            result: "Copper-cobalt blue intensified by zinc — may shift toward more vivid blue",
            chemistry: "Zinc Clear contains zinc. Zinc can intensify copper blues. Should deepen Copper-Cobalt Blue.",
            risk: "low",
            prediction_grade: "likely",
            confidence: "medium",
            source: "Zinc enhances copper-based blues — documented interaction"
        },

        // === CONE 6 OXIDATION ===
        {
            id: 109,
            top: "Manganese Purple (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Lavender to purple over white — brighter than over dark bases",
            chemistry: "Manganese + cobalt over white = cleaner, lighter purple in oxidation",
            risk: "low",
            prediction_grade: "likely",
            confidence: "medium",
            source: "Manganese-cobalt purple over white — should work well at cone 6"
        },
        {
            id: 110,
            top: "Iron Red (Cone 6)",
            base: "White (Cone 6)",
            cone: "6",
            result: "Rust red with white breaks — oxidation iron red is reliable and warm",
            chemistry: "Iron red in oxidation at cone 6 = reliable warm red. Over white = clean breaks.",
            risk: "low",
            prediction_grade: "likely",
            confidence: "high",
            source: "Iron red over white at mid-range — well-documented"
        },
    ],
    glazes: [
        // =============================================================
        // CONE 10 — REDUCTION (gas kiln)
        // =============================================================

        // CLEARS
        {
            name: "Zinc-Free Clear",
            cone: "10",
            atmosphere: "reduction",
            family: "Clears",
            hex: "#e8e4dc",
            chemistry: "Zinc-free clear glaze — silica, feldspar, whiting base",
            behavior: "Preserves true colors underneath; won't shift copper reds or chrome greens",
            layering: "Excellent over any color; protects surface without color modification. USE THIS over copper reds and chrome-tin pinks.",
            source: "Published zinc-free clear glaze formulation"
        },
        {
            name: "Zinc Clear",
            cone: "10",
            atmosphere: "reduction",
            family: "Clears",
            hex: "#f0ebe3",
            chemistry: "Contains zinc oxide as flux — enhances color response from oxides",
            behavior: "Zinc enhances oxide color response; may shift chrome greens to brown; enhances copper greens toward turquoise",
            layering: "DO NOT use over chrome-tin pinks or chrome greens (zinc kills them). Good over copper greens and blues.",
            warning: "Contains zinc — destroys chrome-tin pink and shifts chrome green to brown",
            source: "Published zinc-containing clear glaze formulation"
        },

        // WHITES
        {
            name: "Opaque White",
            cone: "10",
            atmosphere: "reduction",
            family: "Whites",
            hex: "#f5f2ed",
            chemistry: "Zirconium white: 8-12% zirconium silicate opacifier; zinc-free",
            behavior: "Bright opaque white; excellent coverage; reflects light through transparent overlays",
            layering: "THE base for transparent colors — ensures clean, bright development. Copper reds break white. Chrome-tin pinks NEED this (zinc-free).",
            recipe: "Custer Feldspar 40, Silica 25, Whiting 15, Kaolin 10, Zircopax 10",
            source: "Standard zirconium white — published in multiple ceramic references"
        },

        // GREENS
        {
            name: "Jade Green",
            cone: "10",
            atmosphere: "reduction",
            family: "Greens",
            hex: "#5a8a5a",
            chemistry: "Iron green: 3-5% Fe2O3 in heavy reduction; more opaque than celadon",
            behavior: "Opaque jade green; pools darker in recesses",
            layering: "Over white = brighter green. Over shino = jade over warm carbon trap.",
            recipe: "Custer Feldspar 30, Whiting 20, EPK 15, Silica 35, Red Iron Oxide 4",
            source: "Based on Ming Dynasty Chinese greenware type"
        },
        {
            name: "Celadon",
            cone: "10",
            atmosphere: "reduction",
            family: "Greens",
            hex: "#7eb09b",
            chemistry: "1-2% iron oxide in reduction; calcium flux promotes jade color",
            behavior: "Translucent jade-like green; pools darker in recesses, breaks lighter on edges",
            layering: "Over shino = classic combo (jade over carbon trap). Over white = cleaner green. Over tenmoku = dark celadon.",
            recipe: "Custer Feldspar 45, Silica 25, Whiting 18, EPK 12, Red Iron Oxide 1.5",
            source: "Traditional Asian glaze — thousands of years of history"
        },
        {
            name: "Warm Celadon",
            cone: "10",
            atmosphere: "reduction",
            family: "Greens",
            hex: "#8aa07a",
            chemistry: "Warm celadon: 2-3% iron oxide + 1% yellow iron oxide; higher total iron shifts toward amber-green",
            behavior: "Warmer celadon; amber-green instead of blue-green",
            layering: "Over white = warmer green. Over shino = warm jade over carbon trap.",
            recipe: "Custer Feldspar 28, Whiting 20, EPK 20, Silica 32, Red Iron Oxide 2.5, Yellow Iron Oxide 1",
            source: "Warm celadon variation — published recipe"
        },

        // SHINOS
        {
            name: "Carbon Trap Shino",
            cone: "10",
            atmosphere: "reduction",
            family: "Shinos",
            hex: "#c9a070",
            chemistry: "High soda feldspar base (60-70%) with spodumene; carbon trap mechanism",
            behavior: "Iridescent metallic sheen; carbon trap orange/gray patterns",
            layering: "ACCEPTS overlays well: Tenmoku, Celadon, Iron Red work over it.",
            warning: "NEVER apply over another glaze — will crawl catastrophically. Shinos MUST be the base layer.",
            recipe: "Soda Feldspar 65, Spodumene 15, EPK 10, Nepheline Syenite 10",
            source: "Published shino formulation — well-documented in ceramic literature"
        },
        {
            name: "Classic Shino",
            cone: "10",
            atmosphere: "reduction",
            family: "Shinos",
            hex: "#d4956a",
            chemistry: "High soda, low clay for maximum carbon trapping",
            behavior: "Orange/gray carbon trap patterns",
            layering: "Excellent under Celadon, Chun Blue, Tenmoku, Iron Luster.",
            warning: "NEVER apply over another glaze — will crawl. MUST be base layer.",
            recipe: "Nepheline Syenite 48, Soda Ash 4, Spodumene 22, EPK 15, Silica 11",
            source: "Published shino formulation (Malcom Davis) — widely shared"
        },

        // BLUES
        {
            name: "Cobalt Blue",
            cone: "10",
            atmosphere: "reduction",
            family: "Blues",
            hex: "#3a5f8a",
            chemistry: "Cobalt-based blue: 0.5-1% cobalt carbonate",
            behavior: "Stable cobalt blue; most predictable colorant",
            layering: "Over white = bright clean blue. Over iron base = blue-green/teal shift.",
            recipe: "Base glaze + Cobalt Carbonate 0.5-1%",
            source: "Standard cobalt blue — published in ceramic textbooks"
        },
        {
            name: "Copper-Cobalt Blue",
            cone: "10",
            atmosphere: "reduction",
            family: "Blues",
            hex: "#4a7c9b",
            chemistry: "Copper/cobalt blend: copper 1% + cobalt 0.5%",
            behavior: "Complex blue with depth from dual colorants",
            layering: "Over white = clean complex blue. Over iron = may darken significantly.",
            source: "Community copper-cobalt blue — published recipe"
        },
        {
            name: "Chun Blue",
            cone: "10",
            atmosphere: "reduction",
            family: "Blues",
            hex: "#5a8ab0",
            chemistry: "Copper (0.5-1%) + iron (1-2%) in reduction; fluid melt",
            behavior: "Blue with purple edges; creates purple flash over iron glazes like Tenmoku",
            layering: "Over Tenmoku = purple flash (classic). Over shino = blue over warm carbon trap. Over white = clean blue. Fluid — watch for runs.",
            source: "Traditional Chinese Jun/Chun ware type — published formulation"
        },

        // REDS
        {
            name: "Iron Red",
            cone: "10",
            atmosphere: "reduction",
            family: "Reds",
            hex: "#8b3a3a",
            chemistry: "Iron saturation red: 8-12% iron oxide in reduction",
            behavior: "Deep rust red to brick red; breaks to amber where thin",
            layering: "Over shino = warm metallic-red. Over white = cleaner red. NOT compatible with copper reds (both compete).",
            recipe: "Custer Feldspar 40, Whiting 15, EPK 15, Silica 30, Red Iron Oxide 10",
            source: "Classic iron red glaze — published in ceramic references"
        },
        {
            name: "Copper Red",
            cone: "10",
            atmosphere: "reduction",
            family: "Reds",
            hex: "#b33a3a",
            chemistry: "Copper red: 0.5-1.5% CuCO3 in heavy reduction with tin oxide 1-2%",
            behavior: "Bright copper red; requires heavy reduction starting at cone 012; breaks to white on edges over white base",
            layering: "Zinc-Free Clear over preserves red. Zinc Clear over RISKS shifting red (has zinc). Over white = clean breaks. Iron in base KILLS this glaze.",
            warning: "NEVER layer over iron-rich bases. Iron suppresses copper red development.",
            recipe: "Potash Feldspar 40, Whiting 20, Kaolin 15, Silica 25 + Tin Oxide 1.5%, Copper Carbonate 0.75%",
            source: "Published in John Britt — The Complete Guide to High-Fire Glazes"
        },
        {
            name: "Panama Red",
            cone: "10",
            atmosphere: "reduction",
            family: "Reds",
            hex: "#a83232",
            chemistry: "Copper red: 0.5-1% CuCO3 + 1-2% tin oxide in reduction",
            behavior: "Blood red to tomato red; may show blue-purple edges where thin over white",
            layering: "Zinc-Free Clear over preserves red. Opaque White under = clean breaks. Iron in base KILLS this glaze.",
            warning: "Requires heavy reduction. Iron kills copper red. Zinc-containing clears may shift color.",
            recipe: "Custer Feldspar 48, Whiting 14, EPK 6, Silica 15, Ferro 3134 9, Zinc 0.5, Talc 4 + Tin 1.2%, Copper Carbonate 0.8%",
            source: "Published in John Britt — Panama Red family"
        },

        // PURPLES
        {
            name: "Manganese Purple",
            cone: "10",
            atmosphere: "reduction",
            family: "Purples",
            hex: "#7a4a8a",
            chemistry: "Manganese-cobalt purple: 3-4% manganese dioxide + 0.5% cobalt carbonate",
            behavior: "Vibrant purple; surface depends on base glaze",
            layering: "Zinc-Free Clear over adds gloss. White underlayer = brighter lavender.",
            recipe: "Base glaze + Manganese Dioxide 3.5%, Cobalt Carbonate 0.5%",
            source: "Community manganese-cobalt purple — published recipe"
        },
        {
            name: "Chrome-Tin Pink",
            cone: "10",
            atmosphere: "reduction",
            family: "Purples",
            hex: "#c9a0b0",
            chemistry: "Chrome-tin pink: Chrome oxide 0.2-0.4% + tin oxide 1.5-2%",
            behavior: "Soft coral to rose pink",
            layering: "White underlayer ESSENTIAL (prevents muddy result). MUST use zinc-free clear over. Zinc destroys this color.",
            warning: "Zinc destroys chrome-tin pink. Needs oxidation for best color. Reduction may shift toward gray-green.",
            recipe: "Base + Chrome Oxide 0.3%, Tin Oxide 1.5%",
            source: "Chrome-tin pink — published in ceramic chemistry references"
        },
        {
            name: "Chrome-Tin Raspberry",
            cone: "10",
            atmosphere: "reduction",
            family: "Purples",
            hex: "#a04060",
            chemistry: "Chrome-tin raspberry: higher chrome (0.4-0.5%) + tin oxide (2%)",
            behavior: "Deep raspberry to magenta; more saturated than Chrome-Tin Pink",
            layering: "White underlayer essential. Zinc-free clear only.",
            warning: "Same zinc/oxidation warnings as Chrome-Tin Pink. Higher chrome = more saturated but less forgiving.",
            recipe: "Base + Chrome Oxide 0.4%, Tin Oxide 2%",
            source: "Chrome-tin raspberry — published in ceramic chemistry references"
        },

        // BROWNS / DARKS
        {
            name: "Iron-Rutile Brown",
            cone: "10",
            atmosphere: "reduction",
            family: "Browns",
            hex: "#5a4030",
            chemistry: "Iron-rutile brown: 5-6% red iron oxide + 2-3% rutile",
            behavior: "Rich warm brown with rutile variegation",
            layering: "Accepts transparent overlays. Celadon over = olive-brown. Chun over = brown with blue edges.",
            recipe: "Custer Feldspar 40, Whiting 15, EPK 10, Silica 35, Red Iron Oxide 5, Rutile 3",
            source: "Community iron-rutile brown — published recipe"
        },
        {
            name: "Tea Dust",
            cone: "10",
            atmosphere: "reduction",
            family: "Browns",
            hex: "#6a5540",
            chemistry: "High iron (~8%) + rutile/ilmenite for crystal spots",
            behavior: "Dark brown with yellow-green crystal spots",
            layering: "Very iron-rich — will darken any glaze over it. DO NOT combine with copper reds (iron kills them).",
            warning: "Very high iron content. Will suppress copper red development if layered under copper reds.",
            source: "Traditional tea dust glaze — published in ceramic reference books"
        },
        {
            name: "Tenmoku",
            cone: "10",
            atmosphere: "reduction",
            family: "Browns",
            hex: "#2a1a10",
            chemistry: "8-10% iron oxide in reduction; stiff melt",
            behavior: "Dark brown/black with amber breaks where thin",
            layering: "Chun Blue over = purple flash at boundary. Celadon over = dark celadon. Very iron-rich — dominates overlying glazes.",
            recipe: "Custer Feldspar 35, Silica 25, Whiting 15, Kaolin 15, Iron Oxide 10",
            source: "Traditional Japanese glaze — centuries of history"
        },
        {
            name: "Oil Spot Tenmoku",
            cone: "10",
            atmosphere: "reduction",
            family: "Reactive",
            hex: "#1a1510",
            chemistry: "High iron (~10%) with excess iron floating to surface during firing, creating metallic spots",
            behavior: "Black base with gold/silver metallic oil spots; spots form during cooling",
            layering: "DO NOT layer — oil spot formation requires direct surface exposure. Use alone.",
            warning: "Oil spots require specific cooling schedule. Fast cooling = fewer spots. Slow cooling = more spots.",
            recipe: "Custer Feldspar 30, Silica 20, Whiting 15, Kaolin 15, Red Iron Oxide 12, Rutile 2",
            source: "Traditional Chinese Song Dynasty glaze — well-documented"
        },
        {
            name: "Hare's Fur Tenmoku",
            cone: "10",
            atmosphere: "reduction",
            family: "Reactive",
            hex: "#1a1210",
            chemistry: "Very high iron (~12%) with fluid melt creating streaky runs that look like rabbit fur",
            behavior: "Black with amber/rust streaks running down vertical surfaces; highly fluid",
            layering: "DO NOT layer over. Can have clear or shino UNDER it for added depth. Use on vertical forms.",
            warning: "Very fluid — will run off pots if too thick. Test on vertical tiles first.",
            recipe: "Custer Feldspar 28, Silica 18, Whiting 12, Kaolin 10, Red Iron Oxide 14",
            source: "Traditional Chinese Song Dynasty glaze — well-documented"
        },
        {
            name: "Rutile-Eye Brown",
            cone: "10",
            atmosphere: "reduction",
            family: "Browns",
            hex: "#3a2a1a",
            chemistry: "Iron oxide (5%) + Rutile (4%) — rutile creates 'eye' variegation",
            behavior: "Dark brown/black with variegated 'eye' patterns from rutile",
            layering: "Similar to Tenmoku behavior. Accepts transparent overlays.",
            recipe: "Custer Feldspar 40, Whiting 20, EPK 10, Silica 30, Red Iron Oxide 5, Rutile 4",
            source: "Published on Ceramic Action blog (Matt Fiske)"
        },

        // YELLOWS
        {
            name: "Iron Yellow",
            cone: "10",
            atmosphere: "reduction",
            family: "Yellows",
            hex: "#c9a962",
            chemistry: "Iron yellow: 4-5% yellow iron oxide (FeOOH) or praseodymium zirconium stain",
            behavior: "Warm honey yellow; varies with atmosphere",
            layering: "Celadon over = chartreuse (iron+iron). Chun Blue over = blue where they meet.",
            recipe: "Iron: Base + Yellow Iron Oxide 4% OR Praseodymium Stain 6%",
            source: "Community iron yellow — published recipe"
        },
        {
            name: "Iron Luster",
            cone: "10",
            atmosphere: "reduction",
            family: "Yellows",
            hex: "#c9a050",
            chemistry: "Iron reduction luster: 4-5% iron oxide with slow cooling",
            behavior: "Golden honey to amber; iridescent from iron crystallization",
            layering: "Tenmoku over = dramatic dark-over-gold. Zinc-Free Clear over = gloss without shift.",
            recipe: "Base glaze + Red Iron Oxide 4.5%",
            source: "Community iron luster — published recipe"
        },

        // CRYSTALS
        {
            name: "Strontium Crystal Matte",
            cone: "10",
            atmosphere: "reduction",
            family: "Crystals",
            hex: "#a09080",
            chemistry: "High strontium carbonate as flux — creates macro-crystalline matte surface",
            behavior: "Forms visible crystal structures; matte base",
            layering: "Celadon over may obscure crystals. Clear over adds gloss.",
            recipe: "Strontium Carbonate 18, Feldspar 35, Silica 30, Kaolin 15, Whiting 2",
            source: "Pete Pinnell Strontium Crystal Matte — published on Glazy.org"
        },

        // REACTIVE
        {
            name: "Reactive Rutile",
            cone: "10",
            atmosphere: "reduction",
            family: "Reactive",
            hex: "#7a6a5a",
            chemistry: "Rutile-based (TiO2 with ~10% iron); reactive to iron in clay body",
            behavior: "Highly variegating: tan/peach when thick, blue/purple near iron",
            layering: "Unpredictable. Color responds to iron content in clay body and thickness.",
            source: "Community rutile-based reactive glaze — published formulation"
        },
        {
            name: "Ash Glaze",
            cone: "10",
            atmosphere: "reduction",
            family: "Reactive",
            hex: "#b0a080",
            chemistry: "Wood ash (unwashed) as primary flux; variable composition creates unique results",
            behavior: "Warm beige to green to amber; runs and pools creating natural drip patterns; every firing unique",
            layering: "Best used alone. Ash glaze variability makes layering predictions unreliable.",
            warning: "Ash composition varies by tree species, season, and soil. Test each ash batch.",
            recipe: "Wood Ash 40, Feldspar 30, Ball Clay 15, Silica 15",
            source: "Oldest glaze type in ceramics — used for thousands of years across all cultures"
        },

        // =============================================================
        // CONE 6 — OXIDATION (electric kiln)
        // =============================================================

        // CLEARS
        {
            name: "Clear (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Clears",
            hex: "#e8e4dc",
            chemistry: "Mid-range clear: frit-based or feldspar-silica with boron flux",
            behavior: "Crystal clear in oxidation; protects underlying colors without modification",
            layering: "Use over any colored glaze for gloss protection. Safe over all colors in oxidation.",
            recipe: "Ferro Frit 3134 30, Feldspar 25, Silica 25, Kaolin 10, Whiting 10",
            source: "Standard mid-range clear — published in ceramic textbooks"
        },

        // WHITES
        {
            name: "White (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Whites",
            hex: "#f5f2ed",
            chemistry: "Zirconium opacified white for mid-range oxidation",
            behavior: "Bright opaque white; excellent coverage in electric kiln",
            layering: "THE base for all transparent colors at cone 6. Ensures clean color development.",
            recipe: "Feldspar 35, Silica 20, Whiting 15, Kaolin 10, Zircopax 12, Frit 3134 8",
            source: "Standard cone 6 white — published in multiple references"
        },
        {
            name: "Matte White (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Whites",
            hex: "#e8e2d8",
            chemistry: "High alumina matte white; more whiting, less silica than glossy white",
            behavior: "Soft matte white surface; velvety feel",
            layering: "Use as base for transparent colors when matte surface is desired. Glossy overlays will dominate.",
            recipe: "Feldspar 40, Whiting 20, Kaolin 20, Silica 10, Zircopax 10",
            source: "Standard matte white — published in ceramic textbooks"
        },

        // GREENS
        {
            name: "Celadon (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Greens",
            hex: "#90b8a0",
            chemistry: "Iron green in oxidation: 1.5-2% iron oxide; lighter blue-green than reduction celadon",
            behavior: "Light jade green; more blue-toned than reduction celadon; translucent",
            layering: "Over shino = lighter version of classic combo. Over white = clean light green.",
            recipe: "Feldspar 40, Silica 25, Whiting 18, Kaolin 12, Frit 3134 5, Red Iron Oxide 1.5",
            source: "Mid-range celadon — published in John Britt mid-range references"
        },
        {
            name: "Copper Green (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Greens",
            hex: "#5a9a5a",
            chemistry: "Copper in oxidation: 2-3% copper carbonate = reliable bright green",
            behavior: "Bright emerald green; copper in oxidation is the most reliable way to get green",
            layering: "Over white = cleanest green. Clear over = gloss protection.",
            recipe: "Base glaze + Copper Carbonate 2.5%",
            source: "Copper green in oxidation — textbook ceramic chemistry"
        },

        // BLUES
        {
            name: "Cobalt Blue (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Blues",
            hex: "#3a5f8a",
            chemistry: "Cobalt blue: 0.5-1% cobalt carbonate — identical chemistry to cone 10 version",
            behavior: "Stable cobalt blue; works identically in oxidation and reduction",
            layering: "Over white = bright clean blue. The most predictable color at any temperature.",
            recipe: "Base glaze + Cobalt Carbonate 0.75%",
            source: "Cobalt blue at mid-range — published in ceramic textbooks"
        },
        {
            name: "Turquoise (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Blues",
            hex: "#4a9a8a",
            chemistry: "Copper + zinc: 1.5% copper carbonate + 3% zinc oxide in oxidation",
            behavior: "Bright turquoise blue-green; zinc shifts copper from green toward blue",
            layering: "Over white = clean turquoise. Clear over = deeper gloss.",
            recipe: "Base glaze + Copper Carbonate 1.5%, Zinc Oxide 3%",
            source: "Copper-zinc turquoise — published in ceramic chemistry references"
        },
        {
            name: "Chun Blue (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Blues",
            hex: "#5a8ab0",
            chemistry: "Copper + iron mid-range oxidation: copper 0.5-1% + iron 1-2%",
            behavior: "Blue with subtle purple edges; lighter and less dramatic than cone 10 reduction version",
            layering: "Over temmoku = less purple flash than cone 10 but still visible. Over white = clean blue.",
            source: "Mid-range Chun type — published formulation"
        },

        // REDS
        {
            name: "Iron Red (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Reds",
            hex: "#9a4a3a",
            chemistry: "High iron (8-10%) in oxidation; slower cooling promotes red over brown",
            behavior: "Warm rust red to brick red; reliable in electric kiln with slow cooling",
            layering: "Clear over = glossy protection. Over white = cleaner red with white breaks.",
            recipe: "Feldspar 35, Silica 20, Whiting 15, Kaolin 10, Frit 3134 10, Red Iron Oxide 10",
            source: "Mid-range iron red — published in John Britt mid-range references"
        },

        // PURPLES
        {
            name: "Manganese Purple (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Purples",
            hex: "#7a4a8a",
            chemistry: "Manganese-cobalt purple: 3% manganese dioxide + 0.5% cobalt carbonate",
            behavior: "Purple in oxidation; reliable and stable",
            layering: "Over white = lavender. Clear over = glossy purple.",
            recipe: "Base glaze + Manganese Dioxide 3%, Cobalt Carbonate 0.5%",
            source: "Manganese-cobalt purple at mid-range — published recipe"
        },

        // DARKS
        {
            name: "Temmoku (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Browns",
            hex: "#2a1a10",
            chemistry: "High iron (~8%) in mid-range oxidation; slightly lighter than cone 10 version",
            behavior: "Dark brown to near-black; amber breaks where thin; reliable in electric kiln",
            layering: "Over white = dramatic contrast with amber breaks. Chun Blue over = subtle purple.",
            recipe: "Feldspar 30, Silica 20, Whiting 15, Kaolin 15, Frit 3134 10, Red Iron Oxide 10",
            source: "Mid-range temmoku — published in ceramic references"
        },

        // SHINOS
        {
            name: "Shino (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Shinos",
            hex: "#d4956a",
            chemistry: "Soda feldspar base adapted for mid-range; less carbon trapping than cone 10",
            behavior: "Warm orange to cream; less dramatic carbon trap than cone 10 but attractive",
            layering: "Use as base layer. Celadon over = warm green over orange. Clear over = gloss with orange showing.",
            warning: "MUST be base layer — same rule as cone 10 shinos.",
            recipe: "Soda Feldspar 55, Spodumene 15, EPK 15, Nepheline Syenite 10, Silica 5",
            source: "Mid-range shino adaptation — published in ceramic literature"
        },

        // =============================================================
        // CONE 6 — REDUCTION (gas kiln)
        // =============================================================

        {
            name: "Copper Red (Cone 6)",
            cone: "6",
            atmosphere: "reduction",
            family: "Reds",
            hex: "#b33a3a",
            chemistry: "Copper red at mid-range: 0.5-1% copper carbonate + 1-2% tin oxide in reduction",
            behavior: "Copper red in cone 6 reduction; slightly softer than cone 10 but still vivid",
            layering: "Over white = clean breaks. Zinc-Free Clear over = protection. Iron in base kills this glaze.",
            warning: "Requires gas kiln with good reduction. Iron kills copper red. Not for electric kilns.",
            recipe: "Custer Feldspar 42, Silica 20, Whiting 18, Kaolin 10, Frit 3134 10 + Tin Oxide 1.5%, Copper Carbonate 0.75%",
            source: "Published in John Britt — The Complete Guide to Mid-Range Glazes"
        },
        {
            name: "Carbon Trap Shino (Cone 6)",
            cone: "6",
            atmosphere: "reduction",
            family: "Shinos",
            hex: "#c9a070",
            chemistry: "Soda feldspar base with spodumene; carbon trap in mid-range reduction",
            behavior: "Iridescent orange/gray patterns; similar to cone 10 but slightly less dramatic",
            layering: "Accepts overlays: Celadon, Temmoku work over it. MUST be base layer.",
            warning: "NEVER apply over another glaze. Requires reduction. Not for electric kilns.",
            recipe: "Soda Feldspar 60, Spodumene 15, EPK 10, Nepheline Syenite 10, Soda Ash 5",
            source: "Mid-range carbon trap shino — published in ceramic literature"
        },
        {
            name: "Oribe (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Greens",
            hex: "#4a8a4a",
            chemistry: "Copper green in oxidation: 2-3% copper carbonate; traditional Japanese Oribe type",
            behavior: "Bright green; named after tea master Furuta Oribe (16th century); varies from emerald to blue-green",
            layering: "Over white = cleaner green. Clear over = gloss. Traditional on foodware.",
            recipe: "Base glaze + Copper Carbonate 2.5%",
            source: "Traditional Japanese Oribe glaze — documented since 1600s"
        },
        {
            name: "Kaki (Cone 6)",
            cone: "6",
            atmosphere: "oxidation",
            family: "Reds",
            hex: "#b06a30",
            chemistry: "Iron-saturated: 6-8% red iron oxide; persimmon orange to dark red-brown",
            behavior: "Warm persimmon to brick orange; richer and more complex than simple iron red",
            layering: "Over white = bright persimmon. Clear over = deeper color. Accepts overlays well.",
            recipe: "Feldspar 35, Silica 20, Whiting 15, Kaolin 10, Frit 3134 10, Red Iron Oxide 8",
            source: "Traditional Japanese Kaki glaze — published in ceramic references"
        },
    ],
    ideas: []
};

// Export for use
window.DATA = DATA;
window.FAMILY_ORDER = FAMILY_ORDER;
window.COLORANT_RULES = COLORANT_RULES;
