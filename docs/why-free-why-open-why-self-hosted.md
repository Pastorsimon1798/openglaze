# Why OpenGlaze Must Be Free, Open Source, and Self-Hosted

## A Deep Analysis of the Decision and Its Consequences

> **Thesis:** OpenGlaze is not a SaaS opportunity that happens to be open source. It is an open source project that happens to solve a problem for potters. Reversing that priority would kill the project before it gains a single user.

---

## 1. The Ceramics Community Is Not a Market — It's a Culture of Sharing

### What the Research Shows

The ceramics community operates on a fundamentally different economic logic than software consumers. From research on pottery culture:

> "One of the great things about being a potter is the way that experience, tools, and tips are shared by those who love the craft. At my first lesson at the potter's wheel, I was blown away by the way my peers (who were strangers at the time) invested in sharing knowledge with the newbies." — opensource.com, "A potter's community: Mother of innovation"

This is not anecdotal. It is structural. Pottery guilds, community studios, Raku firings, and online forums all operate on reciprocal knowledge exchange. The cultural norm is:
- **Share recipes freely** — Glazy's entire existence depends on this
- **Help newcomers** — experienced potters teach beginners without charging
- **Collaborate on problems** — crazing, shivering, pinholing are solved collectively
- **Destroy and restart** — the pottery exercise of making, slicing, analyzing, smashing, and rebuilding embodies a culture of iterative improvement over ownership

### What This Means for Pricing

A paywall on glaze chemistry software is **culturally alien** to this community. It reads as:
- "I have knowledge you need, and I'm charging for it" — which contradicts the guild ethos
- "Your glaze data lives on my servers, not yours" — which contradicts studio autonomy
- "The basic tool is free, but the good features cost money" — which breeds resentment in a community that shares everything

**Glazy understood this.** Derek Au, Glazy's creator, is a potter who became a programmer, not a programmer who saw a market opportunity. His framing:

> "Glazy is 100% free for use by anyone. Glazy doesn't spy on you, sell your information to third parties, or otherwise profit on you in any way." — help.glazy.org/support

And critically:

> "Glazy will always remain open and free."

Glazy has a Patreon. But the Patreon is framed as **server cost support**, not as payment for features. Even the "Patron-only features" (Target & Solve, Blends, Dark Mode) are perks for supporters, not a business model. The core value — the recipe database, the calculator, the community — is unconditionally free.

**OpenGlaze must match this ethos or be rejected by the community it serves.**

---

## 2. The Market Is Too Small to Support a Business

### The Numbers

| Metric | Estimate |
|--------|----------|
| Global ceramics/pottery market | ~$10–12B annually |
| Active potters using digital tools | 50,000–150,000 globally |
| Serious potters firing weekly, managing 20+ glazes | 5,000–20,000 |
| Teaching studios (universities, community, private) | 5,000–10,000 |
| **Addressable market for glaze calculation software** | **Maybe 10,000–30,000** |

### The Reality of Niche SaaS

Bootstrapped SaaS wisdom says: find a niche of 50,000+ users, charge $29–$79/month, and build a lifestyle business. But that wisdom assumes:
- The niche is **underserved** (no dominant free alternative)
- Users are **businesses** with budgets (not hobbyists with disposable income)
- The tool is **mission-critical** (not a nice-to-have optimization)

OpenGlaze fails all three tests:
1. **Glazy exists** and is free, mature, and loved
2. **Users are mostly individuals** — hobbyists, students, independent artists
3. **The tool is optimizing, not enabling** — potters can mix glazes without it; it just reduces waste

A realistic conversion rate of 3% on 10,000 users at $8/month = $2,400 MRR = $29,000/year. That's before server costs, payment processing, support burden, and the engineering time to build and maintain billing infrastructure.

**The economics of monetization don't work at this scale.** The economics of a free, community-supported tool do.

---

## 3. The Scientific Tool Precedent: Free Is the Expectation

### What Scientific Software Actually Costs

Look at the landscape of chemistry and materials science software:

| Tool | Domain | License | Model |
|------|--------|---------|-------|
| **Jmol** | Molecular visualization | LGPL | Free, open source |
| **Avogadro** | Molecular editor | BSD | Free, open source |
| **CIF2Cell** | Crystallography | MIT-like | Free, open source |
| **nmrshiftdb2** | NMR spectra | Open content | Free, community database |
| **GenX** | X-ray reflectivity | GPL | Free, open source |
| **smina** | Molecular docking | Apache 2.0 | Free, open source |
| **ChemAxon** | Chemistry suite | Proprietary | Free for academics only |

The pattern is unmistakable: **scientific calculation tools are expected to be free.** The exceptions (ChemAxon) are enterprise tools with academic exemptions, not individual creative tools.

The ceramics community is even more price-sensitive than academic science because:
- No institutional budgets to tap
- No grant funding for software
- Individual potters pay out of pocket for everything

**OpenGlaze is a scientific calculator for ceramic chemistry.** Scientific calculators don't charge subscription fees. They are utilities.

---

## 4. The Open Source Monetization Failure Rate Is High

### What Happens When Small Projects Try to Monetize

Research on open source monetization identifies five common failure patterns:

1. **Premature monetization** — introducing paid features before the community has grown sufficiently. Users find alternatives and leave.

2. **Poor free/paid boundary** — converting core features to paid triggers community backlash. Or paid features lack appeal, resulting in extremely low conversion.

3. **Ignoring enterprise needs** — designing only for individual developers, failing to meet enterprise requirements (SSO, audit logs, compliance).

4. **Inadequate cloud vendor defense** — no strategy for when AWS launches a competing managed service.

5. **Unsustainable sponsorship model** — relying solely on sponsorships, unable to sustain full-time maintenance. Core maintainer burnout.

### The High-Profile Catastrophes

| Project | What Happened | Result |
|---------|--------------|--------|
| **HashiCorp / Terraform** | Switched from MPL to BSL | Community created OpenTofu fork; mass exodus |
| **Redis** | Changed to "dual source-available" license | Linux Foundation created Valkey fork; 50+ companies contributed |
| **Elastic / Elasticsearch** | Switched from Apache 2.0 to SSPL | AWS forked as OpenSearch; community split |
| **MongoDB** | Created SSPL | Survived but only because of massive enterprise revenue and Atlas cloud service |

The Linux Foundation's 2025 report explicitly frames this as a trend:

> "Following on the heels of successful forks of formerly open source projects last year, 2025 proved that forking is not merely a technical response to licensing disputes, but also a transformative force that fundamentally reshapes the economics of enterprise software." — Linux Foundation Annual Report 2025

**OpenGlaze is not MongoDB.** It does not have the enterprise revenue, the venture funding, or the market size to survive a license-change fork. If the community forked OpenGlaze, the fork would win — because in a niche market, the community IS the product.

---

## 5. Self-Hosting Is a Feature, Not a Limitation

### Why Potters Want Control

Ceramic glaze recipes are **intellectual property**. A production potter's glaze palette is their competitive advantage:
- The celadon that sells at every craft fair
- The shino that took 200 test tiles to perfect
- The crystalline glaze that no one else has figured out

These recipes are trade secrets. Potters do not want them living on someone else's server.

Self-hosting means:
- **Data sovereignty** — recipes never leave the studio's computer
- **No vendor lock-in** — if the project dies, the tool still works
- **No subscription anxiety** — no fear of price hikes or service shutdowns
- **Customization** — modify the code for studio-specific needs

### The Scientific Community Expects Self-Hosting

From open source scientific hardware research:

> "One way to reduce the cost of scientific equipment is to apply the same free and open source model that drives innovation in software to scientific hardware... open hardware was found to reduce the costs of scientific equipment as a whole by 87% compared to equivalent or lesser proprietary tools." — Hal.science, "Impacts of Open Source Hardware in Science"

The ceramics community is not software engineers, but they understand tools. A potter who mixes their own glazes to save money is the same person who will self-host free software to avoid subscription fees.

---

## 6. The Opportunity Cost of Building Billing Infrastructure

### What Monetization Actually Requires

To monetize OpenGlaze, you would need to build and maintain:

| Component | Engineering Effort | Ongoing Cost |
|-----------|-------------------|--------------|
| User authentication system | 2–4 weeks | Maintenance, security patches |
| Subscription billing (Stripe/Paddle) | 2–3 weeks | Transaction fees (2.9% + $0.30), chargebacks |
| Feature flags / access control | 1–2 weeks | Complexity in every feature decision |
| License key system (for self-hosted) | 2–3 weeks | Support burden for key issues |
| Terms of Service / Privacy Policy | Legal review | Updates, compliance |
| SaaS hosting infrastructure | Ongoing | Servers, CDN, database, backups |
| Customer support for billing | Ongoing | Refunds, disputes, "why can't I access X?" |
| Tax compliance (VAT, sales tax) | Ongoing | Accountant, filings, nexus management |

**Conservative estimate: 8–12 weeks of engineering + $500–$2,000/month ongoing.**

### What That Same Effort Could Build Instead

| Alternative | Value to Users |
|-------------|---------------|
| Import/export from Glazy | Seamless workflow integration |
| Batch scaling calculator | "I need 5,000g, not 100g" |
| Firing schedule database | Cone 6 oxidation, cone 10 reduction, etc. |
| Photo logging for test tiles | Before/after documentation |
| Mobile-responsive UI | Use in the studio, not just at a desk |
| More material databases | Non-US suppliers, local materials |

**Every week spent on billing is a week not spent on making the tool better for potters.**

---

## 7. The Trust Dynamics of a Niche Community

### Game Theory vs. Reality

Classical economics says open source is a public goods problem:

> "In this sense, an OSS community is an example of a public goods game, in which participants have no punishment for free-riding, and they equally benefit from the common good... the game theoretical result of the 'tragedy of the commons' implies that, when collaborators are purely rational, the expected outcome of the project is a complete failure." — ETH Zurich, "The Role of Emotions in Open Source"

But the ceramics community is not "purely rational" in the economic sense. It is **relationally motivated**:
- Potters share recipes because it builds reputation and trust
- Teachers help students because it perpetuates the craft
- Contributors code because they use the tool and want it better
- The "payment" is community standing, not money

### The Fork Risk Is Real — And It Works Both Ways

If OpenGlaze were monetized poorly, the community would fork it. Research on forks found:

> "The complete failure of a fork occurs in less than one case out of five (19%)... nearly eight out of ten forks adopt a governance structure characterized by comparable or greater openness than in the original project." — Academic study on OSS forks

And from the Linux Foundation:

> "Forked projects under neutral foundation governance consistently attract more diverse contributor bases than their proprietary predecessors." — Linux Foundation Annual Report 2025

**If potters feel exploited, they will fork OpenGlaze.** And because the community is small and tight-knit, the fork would likely succeed. The original project would be left with billing infrastructure and no users.

---

## 8. The Glazy Precedent: Proof That Free Works

### What Glazy Actually Is

Glazy is:
- A ceramics recipe database with 100,000+ recipes
- A UMF calculator and analysis tool
- A community of potters sharing test results and photos
- Completely free for all users
- Funded by Patreon donations for server costs
- Run by Derek Au, a potter-programmer, as a labor of love

Glazy's Patreon offers:
- A "flame" badge ($2/month minimum)
- Target & Solve feature
- Blends (Line, Triaxial, Biaxial)
- Dark Mode
- Calculated Thermal Expansion

But critically: **the core value is free.** The Patreon is framed as "help us pay for servers," not "pay us for software."

### What Glazy Proves

1. **A free glaze tool can survive long-term** — Glazy has been running since at least 2016
2. **The ceramics community will support infrastructure costs** — enough patrons pay to keep servers running
3. **The creator can sustain part-time development** — Derek Au maintains it while also being a working potter
4. **Competing with a free, loved tool is nearly impossible** — no one has displaced Glazy because no one can match the combination of free + community + trust

**OpenGlaze's path is to be the best free, open-source complement to Glazy, not a paid competitor to it.**

---

## 9. Voluntary Support Is Not Monetization

### The Critical Distinction

There is a world of difference between **monetization** (paywalls, tiers, SaaS) and **voluntary support** (Patreon, Ko-fi, GitHub Sponsors, "buy me a coffee").

| Monetization | Voluntary Support |
|-------------|-------------------|
| "Pay $8/month or you can't use the optimizer" | "The optimizer is free. If it saved you a test tile, here's my Ko-fi" |
| Feature gates, auth systems, billing infrastructure | A link in the README and on the landing page |
| "Pro" vs "Free" tiers | One tier: everything is free, support is appreciated |
| SaaS hosting required | Self-hosted forever, creator gets coffee money |
| Legal complexity (ToS, Privacy Policy, tax) | Personal donation, minimal compliance |

**Glazy does exactly this.** The entire platform is free. Derek Au has a Patreon. Patrons get a flame badge and minor perks (dark mode, blends). But the core value — recipes, calculator, community — is unconditionally free. The Patreon is framed as "help us pay for servers," not "pay us for software."

**This is the model OpenGlaze should follow.**

### What Voluntary Support Looks Like

**README.md:**
> OpenGlaze is free and open source under the MIT license. If this tool saved you materials, time, or a failed kiln load, consider [buying me a coffee](https://ko-fi.com/yourname) or [supporting on Patreon](https://patreon.com/yourname). No pressure — the tool is yours either way.

**Landing page:**
> OpenGlaze is free, open source, and self-hosted. Built by a potter, for potters. [☕ Buy me a coffee]

**GitHub Sponsors:**
> Sponsor this project to help cover development time and keep the optimizer improving.

### Why This Works

1. **Zero friction** — A user never encounters a paywall, signup gate, or "upgrade" button
2. **Zero engineering cost** — No auth, no billing, no feature flags. Just a link.
3. **Culturally appropriate** — "Buy me a coffee" is the language of craft and gratitude, not commerce
4. **Proven in this exact community** — Glazy's Patreon sustains server costs and part-time development
5. **Honest** — The creator gets support if users feel grateful, not because users are forced

### What Voluntary Support Does NOT Mean

- ❌ Gating features behind donations
- ❌ "Donate to unlock" or "supporter-only" versions
- ❌ Nag screens, countdowns, or guilt trips
- ❌ Creating a sense of obligation

The link exists. Users see it. Some click it. Most don't. Everyone gets the full tool regardless.

---

## 10. What "Free and Self-Hosted" Actually Means in Practice

### The Calculator

- MIT-licensed Python/Flask application
- Clone from GitHub, `pip install -r requirements.txt`, `python server.py`
- Runs on localhost or any server the user controls
- UMF, CTE, recipe storage — all included, no limits

### The Optimizer

- ALSO in the same MIT-licensed repo
- Same installation process
- No feature flags, no license keys, no "Pro" version
- If you can run the calculator, you can run the optimizer

### The Data

- Recipes stored in local JSON/SQLite files
- No cloud sync, no user accounts, no data leaving the machine
- Export/import as JSON, CSV, or plain text
- Full data portability

### The Community

- GitHub issues for bugs and feature requests
- No paid support tier — all support is community support
- Contributions welcome under MIT license
- No CLA required — if you contribute, your code stays MIT forever

### The Creator

- Builds the tool because they use it and care about it
- Accepts voluntary support via Patreon / Ko-fi / GitHub Sponsors
- Frames support as gratitude, not payment
- Keeps building because the work is meaningful, not because revenue targets demand it

---

## 10. The Counterarguments (And Why They're Wrong)

### "But we could make money!"

**Reality:** You *can* make money — through voluntary support. Patreon, Ko-fi, GitHub Sponsors. The difference is: users pay because they *want to*, not because they *have to*. Glazy's Derek Au makes enough from Patreon to cover server costs and justify development time. He doesn't have a business. He has a community that appreciates him.

### "But we need to sustain development!"

**Reality:** The most sustainable open source projects combine two things: (1) code that's easy for others to contribute to, and (2) a creator who feels valued. Voluntary support provides the second. When users send $5 and say "this saved me a kiln load," that's fuel to keep building. It doesn't require billing infrastructure — just a link and gratitude.

### "But what about server costs?"

**Reality:** There are no server costs if there is no server. Self-hosted means users run it themselves. The GitHub Pages landing page is free. If you want to host a demo instance, Patreon/GitHub Sponsors can cover it. The support is for *you*, not for infrastructure you don't have.

### "But other open source projects monetize!"

**Reality:** Other open source projects monetize because they're infrastructure used by businesses with budgets. OpenGlaze is a creative tool for individual artists. But that doesn't mean the creator shouldn't accept voluntary support. It means the support should be voluntary, not transactional.

### "But we spent time building the optimizer — shouldn't we be paid?"

**Reality:** You should be *supported*. There's a difference. Being paid implies a transaction: I give you money, you give me access. Being supported implies gratitude: I give you money because what you built helped me. The optimizer is already built. Put it out there. If it helps people, some of them will want to say thank you with coffee money.

---

## 11. Summary: The Five Pillars

### 1. Cultural Alignment
The ceramics community shares knowledge freely. A paywall is culturally alien and would be rejected. Voluntary support ("buy me a coffee") aligns with the culture of gratitude.

### 2. Market Reality
The addressable market is 10,000–30,000 users globally. Monetization (tiers, SaaS) would generate $20,000–$40,000/year at best — not worth the infrastructure cost. Voluntary support costs nothing to implement and lets the community decide your value.

### 3. Scientific Precedent
Chemistry and materials science tools are expected to be free. OpenGlaze is a scientific calculator, not a SaaS product. The creator can still accept voluntary support — scientists do this via grants, potters via Patreon.

### 4. Fork Risk
In a niche community, the fork wins if users feel exploited. A paywall triggers forks. A "buy me a coffee" link does not.

### 5. Opportunity Cost
Building billing infrastructure takes 8–12 weeks. A Ko-fi link takes 5 minutes. Every hour not spent on payments is an hour spent on the optimizer, the UI, or the material database.

---

## 12. What Success Looks Like

Success for OpenGlaze is not MRR. It is:

- **A potter in rural Montana uses it to fix a crazing glaze** without paying a cent
- **A university ceramics department installs it on a lab computer** for 50 students
- **A studio in Jingdezhen forks it** to add Chinese material databases
- **Glazy links to OpenGlaze** as a recommended tool for recipe analysis
- **The ceramics community says** "OpenGlaze is the tool potters built for potters"
- **A potter sends $5 on Ko-fi** with a note: "Saved me 12 test tiles. Thank you."

**That is the goal. Impact first. Support follows.**

---

*Document version: 1.0 — April 2026*  
*Sources: Linux Foundation Annual Report 2025, ETH Zurich OSS research, Glazy documentation, ceramics community ethnography, open source monetization studies, scientific software licensing analysis*
