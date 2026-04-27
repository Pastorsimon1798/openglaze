# Voice Rules: Anti-Robot Writing Guidelines

> **DIRECTION NOTE (2026-04-27):** OpenGlaze is now studio-agnostic. Do NOT generate
> captions referencing any specific studio, city, or location (no "Default Studio",
> "Long Beach", "Clay on First"). Generate generic captions that any potter anywhere
> could use. References to specific studios have been removed from the app.
>
> The writing style rules below (anti-robot patterns, emoji rules, etc.) remain valid.

**Purpose:** Create authentically human pottery captions that avoid AI detection patterns
**Last Updated:** 2026-04-27
**TDD Status:** All rules are actionable and testable

---

## Banned Words

### LinkedIn Robot Words (NEVER USE)

Words that are instant AI tells - commonly used by LinkedIn AI writers.

```
delve, delving, let's delve
tapestry, rich tapestry
realm, in the realm of
landscape
embrace, embracing
elevate, elevating
navigate, navigating
embark, embarked
foster, fostering
```

### Corporate Speak (AVOID)

Generic business language that feels inauthentic for pottery.

```
groundbreaking
invaluable
relentless
endeavor
enlightening
insights
esteemed
shed light
crucial
paramount
```

### Overused Connectors (MINIMIZE)

These signal AI writing - use natural alternatives instead.

```
furthermore
moreover
additionally
thus
in conclusion
it's worth noting
```

**Test Rule:** Caption MUST NOT contain any words from these lists.

---

## Punctuation Rules

### Em Dash Limit

**Rule:** Maximum 1 em dash (—) per caption. Ideally zero.

**Why:** AI is addicted to em dashes - they're baked into training data.

**Test:** Count em dashes in caption. Must be <= 1.

**Alternatives:**
- Use periods to create separate sentences
- Use commas for simpler breaks
- Use parentheses for asides (like this)

### General Preferences

- Prefer periods over dashes
- Use parentheses for asides
- Avoid the "Not only [X], but also [Y]" pattern

---

## Human Voice Markers

### Required Elements (Minimum 1 Per Caption)

Every caption needs at least ONE of these:

| Type | Examples |
|------|----------|
| **Specific Detail** | Dimensions (height, width), timeframes (three weeks from lump to this), attempt numbers (attempt 4, finally got it right), quantifiable details (47 seconds, cone 10) |
| **Process Struggle** | Finally got the foot right, spent way too long on this handle, wobbly but charming, this one was supposed to be a bowl |
| **Uncertainty** | I think this might be my favorite, didn't turn out how I planned (and that's okay), not sure about this color |
| **Surprise** | Didn't expect that color, the glaze did its thing, kiln surprises, that spot where it thinned out |

**Test Rule:** Caption MUST include at least ONE specific detail, process struggle, uncertainty signal, or surprise element.

---

## Conversational Fillers

**Rule:** Use 0-1 per caption maximum. Don't overdo.

```
honestly
tbh
funny story
plot twist
so yeah
anyway
```

---

## Real Potter Language

### Vocabulary Translations

Replace generic descriptions with specific pottery terminology.

| Avoid | Use Instead |
|-------|-------------|
| "beautiful texture" | The way it catches light, tooth, grain, you can feel where my hands were |
| "unique piece" | One of one, this one's got personality, never made another like it, the only bud vase that survived the kiln disaster |
| "handmade with care" | Spent way too long on this foot, you can feel where my hands were, feels good in the hand |
| "stunning results" | The glaze did its thing, breaking at the edges, darker where it pooled |
| "beautiful" | Satisfying, clean, chunky, delicate, heavy (in a good way), the way it sits, nice weight |
| "color variation" | The glaze did its thing, breaking at the edges, darker where it pooled, that spot where it thinned out |

### Kiln & Firing Language

**Use:**
- Kiln opening
- Cone 10
- Reduction
- Came out of the kiln
- Gas kiln surprises

**Avoid:**
- Kiln reveal
- High fire (vague - say cone 6, cone 10)
- Special atmosphere
- Emerged from firing
- Unpredictable results

**Test Rule:** Replace generic descriptions with specific pottery terminology.

---

## Caption Structure Rules

### Length Guidelines

| Metric | Target |
|--------|--------|
| **Target** | 300-500 characters |
| **Sweet Spot** | 41 avg engagement observed at this length |
| **Minimum** | 50+ characters (below this = poor performance) |
| **Avoid** | <50 characters with no context |

### Structure Template

```
[What it is] + [key technique/material] [optional emoji]

[Process detail or story - what makes this piece special]
[Additional context or surprise element]

[Question OR 'Save this for [reason]' OR 'Send to someone who...']

#hashtags
```

**Formula Example:**
```
Tenmoku glaze on B-Mix clay. The combo I didn't know I needed.

This one fought me a bit - the foot took three tries. But I love how
the glaze broke at the rim. Darker where it pooled, just a hint of
the warm brown clay showing through.

Scale of 1-10, how much do you love a good glaze crawl?

#pottery #ceramics #longbeachartist
```

### Sentence Variety

**Rule:** Mix sentence lengths dramatically.

- **Avoid:** All sentences 6-8 words (AI pattern)
- **Target:** Mix of 3-word, 15-word, 8-word sentences
- **Test:** Sentence lengths must vary by >50%

### Engagement Triggers

**Effective Patterns:**
- Process reveals ("Watch how...")
- Asking preferences ("What type of details...")
- Behind-the-scenes struggles ("Definitely need to come up with a better system...")
- Excitement about results ("Love how the colors come to life...")

**Question Frequency:** Include in 80%+ of posts (currently only 10%)

**Question Style:** Specific, not generic ("Rate this glaze 1-10" not "What do you think?")

### Emoji Usage

- **Frequency:** 1-2 per post maximum
- **Current Style:** 15% of posts use emojis
- **Keeps Authenticity:** Yes, don't overdo it

### Tone Guidelines

Characteristics to maintain:
- Warm
- Educational
- Slightly vulnerable ("trying something new")

---

## Hook Patterns

Opening lines that work for pottery content.

| Type | Example |
|------|---------|
| **Specific Hook** | Tenmoku glaze on B-Mix clay. The combo I didn't know I needed. |
| **Process Hook** | From lump to vase in 47 seconds (actually 3 hours) |
| **Vulnerability Hook** | This one was supposed to be a bowl. |
| **Question Hook** | Scale of 1-10, how much do you love a good glaze crawl? |
| **Anti-Hook** | Just a vase. A really good one though. |

**Note:** Anti-hooks work particularly well for pottery - understated confidence.

---

## Local Voice Elements

### Studio References

When relevant, include:

- **Tag them in posts:** @yourstudio
- **Mention location:** "Made at Default Studio in Long Beach"
- **Free pickup option:** "Free pickup in Long Beach / at Default Studio"

### Community References

- Long Beach references
- Fellow Long Beach makers
- LB pottery community
- Cross-promotion with studio members (e.g., Beth Bowman @bowman_ceramics)

---

## Quality Checklist

Final validation tests before publishing.

| Test | Check |
|------|-------|
| **No banned words** | Scan for all words in banned_words lists |
| **Em dash limit** | Count em dashes - must be <= 1 |
| **Sentence variety** | Sentence lengths must vary by >50% |
| **Specific detail** | At least one specific detail (dimension, time, attempt number) |
| **Natural voice** | Would you say this out loud to a friend? |
| **Potter authenticity** | Would a potter roll their eyes at this? |
| **Length check** | 300-500 characters optimal |
| **Engagement trigger** | Includes question or save/share CTA |

---

## Sources

1. `/brand-vault/voice-rules.md` - Original voice rules documentation
2. `/brand-vault/voice-humanization-research.md` - Anti-AI detection research

---

## Metadata

- **Extraction Methodology:** TDD
- **Red Phase:** Rules must be actionable and testable
- **Green Phase:** Read both source files, extracted all voice-related rules
- **Refactor Phase:** Organized into testable categories with validation criteria
- **Actionability:** Every rule includes a test or validation method
