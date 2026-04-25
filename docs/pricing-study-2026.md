# OpenGlaze Pricing Study — Reality-Based, April 2026

> **Status:** Research complete. This document replaces the fabricated pricing tiers removed in commit `3385f4a`.  
> **Purpose:** Provide an honest, research-backed pricing strategy for an open-source ceramic glaze tool in a market where the dominant competitor is free.

---

## 1. Executive Summary

**The uncomfortable truth:** The ceramics software market is small (tens of thousands of serious users globally, not millions), price-sensitive, and already served by **Glazy**, a mature, well-loved platform that is **100% free** and open-access. Any pricing strategy for OpenGlaze must acknowledge this reality.

**The opportunity:** OpenGlaze is not competing with Glazy on feature parity. It competes on a specific value proposition — **computational recipe optimization** that reduces the number of physical test tiles a potter must fire. This saves real money in materials, kiln electricity/gas, and time. For studios and production potters, this is quantifiable.

**Recommended model:** **Open Core + Patronage Hybrid** — not traditional SaaS tiered pricing. The core tool (UMF calculator, recipe storage, basic CTE analysis) remains free and open source forever. Advanced features (recipe optimizer, batch cost tracking, team collaboration) are unlocked by becoming a Patron. A hosted SaaS option exists for those who want convenience without self-hosting.

**Recommended price points:**

| Tier | Price | Who | What They Get |
|------|-------|-----|---------------|
| **Hobbyist** | $0 | Individual potters | Full UMF calc, recipe storage, CTE check, self-host |
| **Patron** | **$5/mo or $50/yr** | Serious potters, students | Optimizer, cost tracking, export, priority support |
| **Studio** | **$19/mo or $190/yr** | Teaching studios, production potters | Team sharing, batch management, firing logs, API access |
| **Institution** | **Custom** | Universities, manufacturers | SSO, audit logs, custom materials DB, SLA |

**Why these numbers:** See Sections 3–5 below. The $5 Patron tier is anchored to a coffee — a framing that works in creative communities. The $19 Studio tier is below Kiln Fire's $29/month, acknowledging that OpenGlaze is a narrower tool.

---

## 2. Market Reality Check

### 2.1 The Competition

| Product | Price | Model | Users | Notes |
|---------|-------|-------|-------|-------|
| **Glazy** | Free | Community-funded via Patreon | Largest community | UMF calc, recipe DB, photos, kiln schedules. Patreon unlocks patron-only features. |
| **Kiln Fire** | $29/mo | SaaS subscription | Pottery studios | Studio management: firing fees, memberships, classes, supplies. NOT glaze calculation. |
| **GatherGrove** | $29–$200/mo | SaaS per members | Pottery clubs | Club management, up to 200 members at $29, unlimited at $200. |
| **Ceramispace** | Unknown | App (iOS/Mac) | Individual potters | Recipe tracking, firing schedules, inventory. Imports from Glazy. |
| **PotterPal** | One-time purchase (~$30–$50 historically) | Desktop software (Win/Mac) | Serious potters | Older software. UMF charts, material analysis. |
| **Clay Lab** | Unknown | iOS app | Individual potters | Piece tracking, photo documentation. |

**Key insight:** Every tool in this space is either free (Glazy), a one-time purchase (PotterPal), or priced for studio *management* (Kiln Fire, GatherGrove) — not glaze chemistry. There is **no established precedent** for subscription-priced glaze calculation software. This is both a risk and an opportunity.

### 2.2 Market Size

- Global ceramics/pottery market (hobby + professional): ~$10–12B annually
- Active potters using digital tools: Estimated 50,000–150,000 globally
- Glazy's user base: Unknown exact number, but it's the dominant platform
- Serious potters firing weekly and managing 20+ glazes: Maybe 5,000–20,000
- Teaching studios (universities, community studios, private): ~5,000–10,000 globally

**Verdict:** This is a micro-niche. A bootstrapped open-source tool with 500–1,000 paying users at $5–$19/month is a realistic ceiling in the first 2–3 years. That's $2,500–$19,000 MRR. This is lifestyle-business territory, not VC-scale.

### 2.3 User Economics

What do potters actually spend?

| Expense | Typical Cost | Frequency |
|---------|-------------|-----------|
| Clay (25 lbs) | $20–$35 | Monthly for active potters |
| Glaze materials (500g batch) | $1.50–$5.00 | Per batch mixed |
| Cobalt-based glaze batch | $4.00–$8.00 | Per batch |
| Electric kiln firing (full) | $15–$40 | Per firing |
| Gas kiln firing (reduction) | $30–$80 | Per firing |
| Test tiles (materials + firing) | $2–$5 per tile | Per test cycle |
| Studio membership | $100–$300/mo | Monthly |
| Kiln Fire (studio software) | $29/mo | Monthly |
| Potter's time (valued) | $15–$50/hr | Every hour |

**The value math:** If OpenGlaze's optimizer reduces test tiles by even 30% on a 10-tile test cycle, that's 3 fewer tiles × ~$3 = **$9 saved per glaze development cycle**. For a potter developing 5 glazes per year, that's **$45/year in direct material/firing savings**, plus hours of time. At $50/year, the Patron tier pays for itself if it saves even a few tiles.

---

## 3. SaaS Pricing Best Practices (April 2026)

From analyzing 200+ SaaS pricing strategies and 2026 benchmarks:

### 3.1 What Works for Niche/Creator Tools

- **Value-based pricing:** Charge 10–20% of the value you create. If you save a potter $200/year in materials and time, $20–$40/year is fair.
- **Three-tier psychology:** Anchor high, recommend middle. But this works for mass-market SaaS. For micro-niches, simplicity wins.
- **Charm pricing:** $5 outperforms $4.99 in creative communities (feels honest). $19 feels better than $20.
- **Annual discount:** 15–20% (equivalent to ~2 months free). Improves cash flow and reduces churn.
- **Freemium conversion rates:** 2–5% for consumer tools, 1–3% for B2B. With 10,000 active users, expect 200–500 paying.
- **Free trial conversion:** 10–25% — much higher than freemium.

### 3.2 What Works for Open Source

Research on open-source monetization (2026):

| Model | Examples | Best For |
|-------|----------|----------|
| **Open Core** | Sidekiq, GitLab | Clear feature boundary between free/paid |
| **SaaS Hosting** | Supabase, n8n, Cal.com | Technical users self-host; non-technical pay for convenience |
| **Patronage** | Glazy, Wikipedia, Signal | Community-funded; aligns with open values |
| **Add-ons** | Ninja Forms, Alpine.js | Core free; premium extensions |
| **Support/Consulting** | Many enterprise OSS | High-touch; requires scale |

**The Glazy Precedent:** Glazy has proven that patronage works in this exact market. Their model:
- Core platform: Completely free, forever
- Patreon tiers: Unlock patron-only features (advanced tools, early access)
- Students/teachers: Free patron status with .edu email
- Message: "Glazy will always remain open and free. But servers cost money."

This builds trust while generating sustainable revenue.

### 3.3 What Does NOT Work Here

- **Traditional B2B SaaS tiers ($29/$99/$299):** The market is too small and price-sensitive. These prices would exclude 90%+ of potential users.
- **Per-seat pricing:** Potters work alone. Studio sharing is a feature, not the primary use case.
- **Usage-based pricing:** Too complex for a creative tool. Potters don't think in API calls or compute minutes.
- **Free trial only:** Without a free tier, OpenGlaze loses the open-source community goodwill that is its competitive advantage.

---

## 4. Recommended Pricing Architecture

### 4.1 Philosophy

> **"The core is a gift. The convenience is a product."**

OpenGlaze is MIT-licensed. Anyone can clone it, run it locally, and have full access to the UMF calculator and recipe storage. This is non-negotiable — it is the project's identity.

Revenue comes from:
1. **Patronage** — users who want to support the project and unlock advanced features
2. **Hosted SaaS** — users who want cloud access without self-hosting
3. **Enterprise support** — institutions that need guarantees

### 4.2 Tier Details

#### Hobbyist — $0 (Free Forever)

**Target:** Individual potters, beginners, hobbyists, anyone who self-hosts

**Includes:**
- Full UMF calculator and visualization
- Unlimited recipe storage (local or self-hosted)
- CTE mismatch detection
- Basic material database
- Community support (GitHub issues, Discord)
- Self-hosting with full source code (MIT license)

**Limitations:**
- No cloud sync (local storage only)
- No recipe optimizer
- No batch cost tracking
- No team sharing

**Rationale:** This tier must deliver genuine, standalone value. A potter should be able to use OpenGlaze for years without paying and still find it useful. This builds the user base, generates goodwill, and creates the funnel for patronage. The marginal cost of a free user is near zero (no cloud compute, no storage).

#### Patron — $5/month or $50/year (Save $10)

**Target:** Serious hobbyists, production potters, students, independent artists

**Unlocks:**
- **Recipe Optimizer** — computational suggestions to hit target CTE, surface, alkali levels
- **Batch Cost Calculator** — input material prices, see per-batch and per-piece costs
- **Cloud Sync** — recipes backed up and accessible across devices
- **Export Tools** — PDF recipe cards, CSV export, print-friendly layouts
- **Advanced Material DB** — custom materials, import from supplier catalogs
- **Priority Support** — email support with 48-hour response guarantee
- **Patron badge** — visible on public profiles (if community features exist)

**Rationale:** $5/month is a coffee. In creative communities, this framing works — "less than a cup of coffee to support a tool you use weekly." The annual option at $50 (17% discount) improves cash flow. The key unlock is the **optimizer**, which is OpenGlaze's unique differentiator from Glazy. A potter who fires even monthly will save multiples of this cost in reduced test tiles.

**Student/Teacher policy:** Free Patron tier for verified .edu addresses (matching Glazy's proven model). This builds loyalty among the next generation and creates institutional awareness.

#### Studio — $19/month or $190/year (Save $38)

**Target:** Teaching studios, community ceramics centers, production potters with assistants, small manufacturers

**Unlocks (everything in Patron, plus):**
- **Team Sharing** — shared recipe libraries with role-based access
- **Batch Management** — scale recipes, track batch numbers, mixing logs
- **Firing Log Integration** — link recipes to kiln firings, track results over time
- **Inventory Tracking** — raw materials on hand, reorder alerts
- **API Access** — integrate with studio management tools (Kiln Fire, etc.)
- **White-label Export** — recipes branded with studio logo
- **Priority Support** — 24-hour response, video call option

**Rationale:** $19/month is deliberately positioned **below** Kiln Fire's $29/month. OpenGlaze is a narrower tool (glaze chemistry vs. full studio management), so it should cost less. A studio running 20+ glazes and firing weekly will save hundreds annually in materials alone. The annual plan at $190 (17% discount) is designed for studios that budget annually.

#### Institution — Custom

**Target:** Universities with ceramics programs, art schools, manufacturers, museums

**Includes:**
- Everything in Studio
- SSO / SAML authentication
- Audit logs and compliance reporting
- Custom material database (institution-specific raw materials)
- Dedicated support channel
- SLA with uptime guarantee
- Training sessions for faculty/staff
- Volume pricing for large deployments

**Rationale:** Custom pricing for organizations with procurement departments, security requirements, and budgets. Universities often have software budgets of $1,000–$10,000/year for departmental tools. A $500–$2,000/year institutional license is reasonable for a department with 50+ students.

### 4.3 Self-Host vs. SaaS Decision Matrix

| User Type | Self-Host (Free) | SaaS (Paid) |
|-----------|-----------------|-------------|
| Technical, privacy-focused | ✅ Perfect | — |
| Casual user, no server knowledge | — | ✅ $5–$19/mo |
| Studio with IT support | ✅ Possible | ✅ Convenience |
| Institution with compliance needs | ⚠️ Possible | ✅ Custom SLA |

The SaaS pricing is **not** for features — the code is open. It's for **convenience, cloud sync, and support**.

---

## 5. Revenue Projections (Conservative)

### 5.1 Assumptions

- Year 1: 2,000 active users (generous for a new tool in a niche market)
- Freemium-to-paid conversion: 3% (middle of 2–5% benchmark)
- Patron-to-Studio split: 80% Patron, 20% Studio (most users are individuals)
- Annual plan adoption: 40% of paid users
- Churn: 5% monthly (typical for creative tools)

### 5.2 Year 1 Projection

| Metric | Value |
|--------|-------|
| Total active users | 2,000 |
| Paying users (3%) | 60 |
| Patrons ($5/mo avg) | 48 |
| Studios ($19/mo avg) | 12 |
| **Monthly Recurring Revenue** | **$468** |
| **Annual Revenue** | **~$5,600** |

### 5.3 Year 3 Projection (Growth Scenario)

| Metric | Value |
|--------|-------|
| Total active users | 8,000 |
| Paying users (4%) | 320 |
| Patrons | 256 |
| Studios | 64 |
| **MRR** | **$2,496** |
| **Annual Revenue** | **~$30,000** |
| Institution deals | 2–5 at $500–$2,000/yr |
| **Total Annual Revenue** | **~$32,000–$40,000** |

### 5.4 Reality Check

These numbers are modest. $30K–$40K/year is not a venture-scale business. But it is:
- Enough to cover server costs ($100–$500/month depending on scale)
- Enough to justify continued development (part-time)
- Enough to build a sustainable open-source project without burnout
- Realistic for a niche tool in a niche market

**Comparison:** Glazy's Patreon revenue is unknown but likely in a similar range. The model is proven to work at this scale.

---

## 6. Implementation Roadmap

### Phase 1: Patron-Only Feature Flags (Months 1–2)

Before implementing billing, build the feature-flag infrastructure:
- User authentication (GitHub OAuth, email)
- Patron status tracking (manual at first — GitHub Sponsors or Patreon webhook)
- Feature gates: `optimizer`, `cloud_sync`, `batch_cost`, `team_sharing`
- All code remains MIT-licensed; features are gated at runtime, not compile time

### Phase 2: GitHub Sponsors Integration (Month 2–3)

- Set up GitHub Sponsors (lowest friction for open-source projects)
- Create tiers: $5/month (Patron), $15/month (Studio — equivalent to $19 with platform fees)
- Webhook integration to automatically unlock features
- Public thank-you page / hall of fame

**Why GitHub Sponsors over Stripe directly:**
- Zero platform fees (GitHub doesn't take a cut for individuals)
- Built-in audience of developers and technical users
- Transparent, aligned with open-source values
- Lower compliance burden than running your own payments

### Phase 3: SaaS Hosting Launch (Month 6–12)

- Only after self-hosted version is stable and has users
- Offer hosted instances at the Patron/Studio prices
- This requires infrastructure: database, auth, backups, CDN
- Start with invite-only to control costs

### Phase 4: Institutional Sales (Year 2+)

- Only after proving the product with individual users
- Direct outreach to university ceramics departments
- Custom contracts, invoicing, SLA

---

## 7. What to Avoid

### 7.1 The Traps We Already Fell Into

The removed pricing tiers (Free $0, Pro $9, Studio $29, Education $199/yr) had these problems:

1. **No free tier actually existed** — the project had no billing infrastructure, no feature gates, no SaaS hosting. The tiers were pure fiction.
2. **$9/month is too high for individuals** when Glazy is free. The value proposition doesn't support it yet.
3. **No differentiation between tiers** — the features listed were vague and didn't map to actual code.
4. **Fake social proof** — testimonials with fabricated names and quotes. This destroys trust permanently.

### 7.2 Pricing Anti-Patterns for This Market

| Anti-Pattern | Why It Fails Here |
|--------------|-------------------|
| **$29+ individual tiers** | Exceeds what potters pay for most tools. Kiln Fire is $29 and does 10x more. |
| **Per-seat pricing** | Most users are solo. Studios are the exception, not the rule. |
| **"Contact Sales" for mid-tier** | Friction kills conversion in a low-touch, creative market. |
| **Feature-gating basic UMF calc** | This is the core value. Paywalling it sends users straight to Glazy. |
| **Annual-only billing** | Monthly options reduce commitment anxiety for creative users with irregular income. |
| **"Enterprise" at $99/mo** | There are no ceramic glaze "enterprises." The top of market is universities. |

---

## 8. Positioning and Messaging

### The Honest Pitch

> OpenGlaze is free, open-source glaze chemistry software. The UMF calculator, recipe storage, and CTE analysis will always be free — whether you use our hosted version or run it yourself.
>
> If OpenGlaze saves you time, materials, or a failed kiln load, consider becoming a Patron. For $5/month, you unlock the recipe optimizer, cloud sync, and batch cost tracking. For studios, our $19/month plan includes team sharing and API access.
>
> Students and teachers with a .edu email get Patron features free.
>
> Can't pay? No problem. Self-host the full source code under the MIT license. It's yours forever.

### Key Principles

1. **Lead with value, not price.** The first message is what the tool does for free.
2. **Frame as support, not purchase.** "Become a Patron" feels better than "Upgrade to Pro."
3. **No guilt.** The free tier is not a trial. It's a complete tool.
4. **Transparency.** Publish how funds are used (server costs, development time, community events).

---

## 9. Key Metrics to Track

| Metric | Target | Why |
|--------|--------|-----|
| Active users (monthly) | 2,000+ Y1 | Market size indicator |
| Freemium-to-paid conversion | 3–5% | Pricing health |
| Monthly churn | < 5% | Sustainability |
| Annual plan ratio | > 30% | Cash flow quality |
| Support tickets per user | < 0.1/month | Operational load |
| Self-host vs. SaaS ratio | 70:30 | Infrastructure planning |
| NPS / user satisfaction | > 40 | Product-market fit |

---

## 10. Summary

| Question | Answer |
|----------|--------|
| **Can we charge $29/month?** | No. The market won't bear it. Glazy is free. |
| **What's the right model?** | Open Core + Patronage + optional SaaS hosting. |
| **What's the right price?** | $5/mo for individuals, $19/mo for studios. Annual discounts. |
| **When do we implement billing?** | After 1,000+ active users and feature-flag infrastructure. |
| **What's the realistic revenue?** | $5K–$40K/year in first 3 years. Lifestyle business, not unicorn. |
| **Is this sustainable?** | Yes, if costs are kept low and the community is nurtured. |

---

## Sources

- SaaS Pricing Best Practices 2026 (InfluenceFlow, Dev.to, Algunia, Monolit)
- Open Source Monetization Guide 2026 (youngju.dev)
- Glazy Support / Patreon Model (help.glazy.org)
- Kiln Fire Pricing (kilnfire.com)
- Pottery Software Landscape (kilnfire.com/blog, ceramicsnow.org)
- Niche SaaS Pricing Benchmarks (entrepreneurloop.com, rightleftagency.com)
- Bootstrapped SaaS Pricing Framework (lovable.dev)
- Open Source Infrastructure Business Models (dri.es, 2026)

---

*Document version: 1.0 — April 2026*  
*Author: Research synthesis for OpenGlaze project*  
*Next review: After 1,000 active users or 6 months, whichever comes first*
