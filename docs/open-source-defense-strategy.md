# OpenGlaze Defense Strategy: Staying Open Without Getting Exploited

> **The honest answer up front:** For a niche ceramics tool, the biggest threat isn't Amazon stealing your code — it's obscurity. But if you want real protection, there are concrete, proven options. This document lays them out with tradeoffs.

---

## 1. Threat Assessment: What's the Real Risk?

### The Cloud Vendor Nightmare (Overblown for This Market)

The canonical horror story is **Elasticsearch vs. AWS**:
1. Elastic releases Elasticsearch under Apache 2.0
2. AWS launches "Amazon Elasticsearch Service," makes billions
3. Elastic changes license to SSPL
4. AWS forks the project as "OpenSearch"
5. Community splits, everyone loses

**But here's the thing:** AWS, Google Cloud, and Azure do not care about ceramic glaze software. They care about infrastructure that millions of developers depend on — databases, search engines, container orchestration. The ceramics market is too small for them to notice.

**Realistic threats for OpenGlaze:**

| Threat | Likelihood | Impact |
|--------|-----------|--------|
| A solo developer forks and hosts a competing SaaS | Medium | Low (no users, no trust) |
| A pottery studio self-hosts for their students instead of paying | High | Low (they wouldn't have paid anyway) |
| A ceramics supply company adds "glaze tools" to their site | Low | Medium (has distribution, but not focus) |
| AWS/Azure/GCP hosts a managed OpenGlaze | **Near zero** | N/A |

**Verdict:** You are not building infrastructure. You are building a niche creative tool. The economics that make cloud vendor exploitation profitable simply don't exist here. The thing most likely to kill OpenGlaze is **nobody using it**, not someone stealing it.

---

## 2. Defense Strategies (Ranked by Practicality)

### Strategy A: Accept the Risk and Build a Moat (Recommended)

**What:** Keep MIT license. Don't try to legally prevent competition. Instead, make OpenGlaze the *obvious* choice through non-code advantages.

**Your moats:**

1. **Community & Network Effects**
   - Build a shared recipe database that users contribute to
   - Verified recipe ratings, photos, test results
   - A fork has no recipes, no community, no trust
   - *Example:* Glazy's real value isn't the software — it's the 100,000+ recipes and the community verifying them

2. **First-Mover & Brand**
   - Be the "official" OpenGlaze. Own the GitHub org, the domain, the docs
   - Publish regularly, build SEO, become the search result
   - A fork starts at zero recognition

3. **Convenience Moat (SaaS)**
   - Self-hosting is free but requires technical skill
   - Most potters are not developers
   - Your hosted version is the path of least resistance
   - *Example:* WordPress.org is free; WordPress.com (hosted) makes $500M+/year

4. **Continuous Development**
   - A fork is a snapshot. You're shipping weekly
   - Users follow the living project, not a stagnant fork

5. **Trust & Transparency**
   - Potters are a tight-knit community
   - If someone forks and tries to monetize aggressively, the community will notice and talk
   - Your open-source ethos is your marketing

**Why this is the best strategy for OpenGlaze:**
- Zero legal complexity
- Zero community backlash risk
- Aligns with your actual threat model (obscurity >> theft)
- Lets you focus on users, not lawyers

---

### Strategy B: Trademark Protection

**What:** Keep MIT license for code. Register "OpenGlaze" as a trademark. Forks can use the code but not the name.

**How it works:**
```
Code: MIT — anyone can fork, modify, sell
Name: Trademark — only the official project can call itself "OpenGlaze"
```

**Examples:**
- **Firefox:** Code is open (MPL), but you can't call your fork "Firefox" without Mozilla's permission
- **WordPress:** Code is GPL, but "WordPress" is trademarked
- **Docker:** Code is open, "Docker" is trademarked

**Pros:**
- Prevents confusion in the marketplace
- Lets you control the brand
- Doesn't restrict code freedom

**Cons:**
- Registration costs ($250–$750 in the US, more internationally)
- Must actively enforce (send cease-and-desist letters) or lose it
- Doesn't prevent competing products, just competing *names*

**Verdict:** Worth doing eventually, but not urgent. Register the trademark once you have users and revenue. It's cheap insurance.

---

### Strategy C: License Change to AGPL

**What:** Replace MIT with AGPLv3. This is the "poison pill" for cloud hosting.

**How AGPL works:**
- Anyone can use, modify, and distribute the code (like MIT)
- **BUT** if you run AGPL code as a *network service* (SaaS), you must share your modifications with users
- This means a cloud vendor hosting OpenGlaze must open-source any improvements they make

**Examples:**
- **MongoDB** originally used AGPL (later created SSPL)
- **GitLab** uses a hybrid: core is MIT, EE features are proprietary

**Pros:**
- Cloud vendors hate AGPL because it forces them to share
- Protects against "host and improve in secret" scenarios
- Still genuinely open source (OSI-approved)

**Cons:**
- AGPL is controversial in the business world — some companies ban it outright
- Harder to get corporate adoption (universities, manufacturers)
- Changing license on existing code requires consent from *all* contributors
- For a ceramics tool, this is overkill — you're solving a problem you don't have

**How to change license (if you decide to):**
1. Stop accepting contributions under MIT
2. Require Contributor License Agreements (CLAs) going forward
3. For existing code: since you're currently the sole contributor, you can relicense your own work
4. Update `LICENSE` file and all headers
5. Announce clearly with rationale

**Verdict:** Not recommended for OpenGlaze at this stage. The cost (confusion, corporate friction) exceeds the benefit (theoretical cloud vendor protection).

---

### Strategy D: The "Open Core" Model with Proprietary Extensions

**What:** Core glaze calculator stays MIT. Advanced features (optimizer, batch costing, team sharing) are in a separate, proprietary module.

**Architecture:**
```
openglaze-core/          → MIT (UMF calc, recipe storage, CTE)
openglaze-pro/           → Proprietary (optimizer, cloud sync, cost tracking)
```

**Examples:**
- **GitLab:** CE is MIT, EE is proprietary
- **Sidekiq:** Core is LGPL, Pro/Enterprise are commercial
- **Metafizzy:** Isotope/Flickity core is open, commercial license required for commercial use

**Pros:**
- Community gets full basic tool
- Revenue comes from premium extensions
- Clear boundary: open vs. closed

**Cons:**
- Two codebases to maintain
- Community may resent paywalled features
- Requires architectural separation from day one

**Verdict:** This is the model the pricing study already recommends. The core is free forever; patron-funded features are logically separable (optimizer is a module, cloud sync is a service). You don't need a proprietary license — feature flags and auth are enough at this scale.

---

### Strategy E: The Business Source License (BSL)

**What:** Code is source-available but not "open source" by OSI definition. It becomes truly open (e.g., Apache 2.0) after a time delay (e.g., 4 years).

**How BSL works:**
- Year 0–4: You have exclusive right to monetize
- Year 4+: License converts to Apache 2.0 (fully open)
- During the exclusive period: anyone can *use* the code, but can't compete commercially

**Examples:**
- **HashiCorp** (Terraform, Vault) — caused major community backlash
- **MariaDB** (created BSL)
- **Sentry**

**Pros:**
- Strong protection against commercial competition
- Code eventually becomes truly open

**Cons:**
- **Not open source** — you lose the "open source" badge and goodwill
- HashiCorp's BSL transition created OpenTofu fork; community trust was damaged
- For a tiny project, this signals fear and insecurity
- Massive overkill for ceramics software

**Verdict:** Do not do this. The community damage is real and permanent. BSL is for infrastructure companies with $100M+ revenue and existential cloud vendor threats.

---

## 3. The Real Protection: Make It Not Worth Stealing

The best defense is making OpenGlaze *unstealable* in practice, not in law. Here's how:

### Make the Data the Product

| What | Why It's Hard to Steal |
|------|------------------------|
| Verified recipe database | 100K recipes with test photos, user ratings, firing notes |
| Community contributions | Users trust recipes from known community members |
| Integration partnerships | Supplier material catalogs, kiln controller APIs |
| Curated learning content | Video tutorials, glaze theory guides, firing schedules |

A competitor can fork your code in 5 minutes. They cannot fork 5 years of community-contributed recipes and trust.

### Be the Default

- `openglaze.org` should be the first Google result for "glaze UMF calculator"
- Your GitHub repo should have the most stars
- Your documentation should be the most comprehensive
- A fork starts at Page 10 of search results

### Ship Faster Than Forks

| Metric | Official | Fork |
|--------|----------|------|
| Release cadence | Weekly | When maintainer has time |
| Bug fixes | 24–48 hours | Unknown |
| New features | User-driven roadmap | Copied from upstream |
| Support | Active Discord/forum | GitHub issues only |

Users follow the project that listens and ships.

---

## 4. Practical Checklist

### Now (Pre-Launch)

- [ ] **Register the domain** `openglaze.org` (or whatever you use) — prevent cybersquatting
- [ ] **Secure the GitHub org** `github.com/openglaze` — prevent namespace squatting
- [ ] **Add a `TRADEMARK.md`** file stating that "OpenGlaze" is a trademark even though code is MIT
- [ ] **Require CLAs** if you start accepting external contributions — preserves your right to relicense

### Later (With Users & Revenue)

- [ ] **Register trademark** (USPTO, ~$250–$750) — formal protection for the name
- [ ] **Consider AGPL** only if a credible threat emerges (unlikely)
- [ ] **Build the recipe database** — this is your real moat
- [ ] **Launch SaaS hosting** — convenience beats forks for non-technical users

### Never (For This Project)

- [ ] **BSL / SSPL** — community destruction for a theoretical threat
- [ ] **Patent anything** — expensive, antagonistic, irrelevant to ceramics
- [ ] **Lawyer-heavy enforcement** — costs more than it's worth at this scale

---

## 5. Summary Table

| Strategy | Cost | Protection Level | Community Risk | Recommendation |
|----------|------|-----------------|----------------|----------------|
| **Build moats (community, data, SaaS)** | Time | High (practical) | None | **Do this** |
| **Trademark the name** | $250–$750 | Medium (brand) | None | **Do this later** |
| **Open Core (proprietary extensions)** | Engineering | Medium (feature) | Low | **Already doing this** |
| **AGPL license** | Legal complexity | High (legal) | Medium | **Not now** |
| **BSL / SSPL** | Legal + trust | Very High | **Severe** | **Don't do this** |
| **Do nothing** | $0 | Low | None | **Acceptable for now** |

---

## Final Word

> "The best way to protect your open-source project is to make it so good and so loved that forking it is a waste of time."

For OpenGlaze, the risk of theft is **theoretical**. The risk of irrelevance is **real**. Spend your energy on:
1. Making the optimizer genuinely useful
2. Building a recipe database people want to contribute to
3. Becoming the place potters go to talk about glaze chemistry

A competitor with your code but no community is just a slower, sadder version of you.

---

*Document version: 1.0 — April 2026*
