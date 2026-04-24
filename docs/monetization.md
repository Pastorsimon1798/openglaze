# OpenGlaze Monetization Plan

Revenue model and go-to-market strategy for OpenGlaze.

## Philosophy

OpenGlaze follows an **"open core"** model:

- **Core software** is 100% open source (MIT license)
- **Hosted service** generates revenue through convenience and managed infrastructure
- **Self-hosting remains free** — no artificial restrictions
- **Community contributions** are welcomed and celebrated

This aligns with our mission: *empower ceramic artists with great tools, regardless of their technical ability or budget.*

## Revenue Streams

### 1. Hosted SaaS Subscriptions (Primary)

Recurring revenue from users who prefer a managed service.

#### Pricing Tiers

| Tier | Monthly | Yearly | Target User |
|------|---------|--------|-------------|
| **Free** | $0 | $0 | Individual potters, students |
| **Pro** | $9 | $90 | Serious hobbyists, small studios |
| **Studio** | $29 | $290 | Professional studios, 2-5 members |
| **Education** | — | $199 | Schools, universities |
| **Enterprise** | Custom | Custom | Large organizations, custom integrations |

#### Tier Breakdown

**Free**
- Unlimited glazes
- 50 firings/month
- 1 studio
- Basic AI (local Ollama)
- Community support

**Pro ($9/mo)**
- Everything in Free
- Unlimited firings
- Advanced analytics
- 2 team members
- Cloud AI (Claude)
- Priority email support
- Export to PDF/CSV

**Studio ($29/mo)**
- Everything in Pro
- 5 team members
- Custom branding (logo, colors)
- API access
- Webhook integrations
- Shared glaze libraries
- Advanced permissions

**Education ($199/yr)**
- Everything in Studio
- Unlimited users per institution
- LMS integration (Canvas, Moodle)
- Curriculum templates
- Student progress tracking
- Dedicated support contact

**Enterprise (Custom)**
- Everything in Education
- Custom integrations
- SLA guarantees
- On-premise deployment support
- Training and onboarding
- White-label option

#### Pricing Psychology

- **Free tier** is genuinely useful — builds trust and word-of-mouth
- **Yearly discount** (2 months free) improves cash flow and retention
- **Studio tier** anchors Pro as a good value
- **Education pricing** builds future customer pipeline

### 2. Self-Hosted Support & Services

Revenue from organizations running OpenGlaze on their own infrastructure.

| Service | Price | Description |
|---------|-------|-------------|
| **Setup Assistance** | $500 one-time | Remote installation and configuration |
| **Annual Support** | $1,200/yr | Email support, security patches, updates |
| **Custom Development** | $150/hr | Feature development, integrations |
| **Training Workshop** | $2,000/day | On-site or virtual team training |
| **Migration Service** | $800+ | Migrate from Glazy, Insight, spreadsheets |

### 3. Marketplace (Future)

Digital marketplace for ceramic resources:

| Product Type | Revenue Split | Example |
|-------------|---------------|---------|
| Premium glaze templates | 70/30 (creator/platform) | "Cone 10 Crystalline Pack" — $15 |
| Firing schedules | 70/30 | "Wood Firing Schedules" — $10 |
| Educational courses | 60/40 | "Mastering Copper Red" — $49 |
| Material databases | 80/20 | "Local Clay Analyses" — $25 |

### 4. Affiliate & Partnership Revenue

- **Ceramic supply referrals** — Partner with clay suppliers, kiln manufacturers
- **Book recommendations** — Affiliate links to ceramic chemistry books
- **Workshop promotions** — Promote workshops, take booking fee

### 5. Sponsorship & Grants

- **Arts council grants** — Apply for technology-in-arts funding
- **Corporate sponsorship** — Kiln manufacturers, clay suppliers
- **GitHub Sponsors** — Direct community support
- **Open Collective** — Transparent funding for specific features

## Unit Economics

### Cost Per User (Hosted)

| Cost Category | Free | Pro | Studio |
|--------------|------|-----|--------|
| Infrastructure | $0.50/mo | $1.50/mo | $3.00/mo |
| AI API (Claude) | $0 | $2.00/mo | $5.00/mo |
| Payment processing | $0 | $0.30/mo | $0.90/mo |
| Support | $0 | $0.50/mo | $2.00/mo |
| **Total Cost** | **$0.50/mo** | **$4.30/mo** | **$10.90/mo** |
| **Revenue** | **$0** | **$9/mo** | **$29/mo** |
| **Gross Margin** | **N/A** | **52%** | **62%** |

*Infrastructure costs assume efficient multi-tenant hosting on Hetzner/DigitalOcean*

### Break-Even Analysis

| Scenario | Monthly Users Needed | Monthly Revenue |
|----------|---------------------|-----------------|
| Solo founder, part-time | 50 Pro + 10 Studio | $740 |
| Small team (2 people) | 150 Pro + 30 Studio | $2,220 |
| Sustainable business | 500 Pro + 100 Studio | $7,400 |

## Go-to-Market Strategy

### Phase 1: Community Building (Months 1-6)

**Goals:**
- 100 active self-hosted users
- 10 paying SaaS customers
- Establish presence in ceramics community

**Tactics:**
- Launch on Hacker News, Reddit r/Pottery, Ceramic Arts Network
- Partner with 3 ceramics YouTubers for tutorials
- Publish glaze chemistry blog posts (SEO)
- Attend 2 ceramics conferences with demo booth
- Create "OpenGlaze for Studios" PDF guide

### Phase 2: Product-Market Fit (Months 6-12)

**Goals:**
- 500 active users (combined hosted + self-hosted)
- 100 paying customers
- 5 education customers

**Tactics:**
- Launch Education tier with pilot schools
- Release mobile PWA improvements
- Add integrations (Instagram, Etsy shop links)
- Launch glaze recipe sharing community
- Begin marketplace development

### Phase 3: Scale (Months 12-24)

**Goals:**
- 5,000+ active users
- 1,000+ paying customers
- $10K+ MRR
- Break-even or profitable

**Tactics:**
- Hire first support engineer
- Expand to international markets (Europe, Australia)
- Launch marketplace beta
- Enterprise pilot programs
- Raise seed funding if needed for acceleration

## Customer Acquisition Channels

| Channel | CAC Estimate | Conversion | Priority |
|---------|-------------|------------|----------|
| Organic search (SEO) | $0 | 2-5% | High |
| Ceramics forums/communities | $0 | 5-10% | High |
| YouTube tutorials | $50/video | 3-8% | High |
| Word of mouth | $0 | 10-20% | High |
| Instagram/TikTok | $20/post | 1-3% | Medium |
| Paid search (Google) | $15-30 | 2-4% | Medium |
| Ceramic conferences | $500/event | 15-30% | Medium |
| University outreach | $50/school | 5-15% | Medium |
| Partnerships (kiln makers) | $0 | 5-10% | Low |

## Retention Strategy

### Reducing Churn

| Strategy | Implementation |
|----------|---------------|
| **Data lock-in prevention** | Easy export to CSV/YAML at any tier |
| **Progress tracking** | Show user's glaze development over time |
| **Community** | Studio collaboration, shared libraries |
| **Gamification** | Streaks, badges, leaderboards |
| **Annual billing discount** | 2 months free for yearly commitment |
| **Downgrade path** | Free tier preserves data, just limits features |
| **Win-back emails** | "We miss you" with new features after 30 days inactive |

### Key Metrics to Track

| Metric | Target |
|--------|--------|
| Monthly Churn Rate | < 5% |
| Annual Churn Rate | < 30% |
| Free-to-Paid Conversion | > 5% |
| Net Revenue Retention | > 100% |
| Customer Lifetime Value | > $200 |
| LTV:CAC Ratio | > 3:1 |

## Competitive Positioning

| Competitor | Their Strength | Our Advantage |
|-----------|---------------|---------------|
| **Glazy** | Large database, established | Open source, self-hostable, AI-powered |
| **Insight/Live** | Professional chemistry tools | Modern UI, collaboration, mobile |
| **Spreadsheets** | Free, flexible | Structured, searchable, shareable |
| **Custom software** | Perfect fit | 10% of cost, 90% of features |

### Unique Value Propositions

1. **"Own your data"** — Export anytime, self-host if we disappear
2. **"Built for studios"** — Multi-user collaboration out of the box
3. **"AI-powered"** — Kama assistant understands glaze chemistry
4. **"Open source"** — Community-driven, transparent development

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Low adoption in ceramics community | Medium | High | Free tier, education partnerships, content marketing |
| High infrastructure costs | Low | Medium | Efficient hosting, usage limits on free tier |
| AI API costs exceed revenue | Medium | Medium | Local AI option, usage caps, pricing adjustments |
| Competitor releases free alternative | Medium | Medium | Open source differentiation, community moat |
| Founder burnout (solo) | Medium | High | Automated systems, community maintainers, eventual hiring |
| Open source forks diverge | Low | Low | Be the "official" instance, trademark protection |

## Financial Projections

### Conservative Scenario (Year 1)

| Month | Hosted Users | Paying | MRR | Cumulative Revenue |
|-------|-------------|--------|-----|-------------------|
| 1 | 20 | 2 | $18 | $18 |
| 3 | 100 | 10 | $90 | $270 |
| 6 | 300 | 35 | $315 | $1,350 |
| 9 | 600 | 75 | $675 | $3,375 |
| 12 | 1,000 | 120 | $1,080 | $6,480 |

### Optimistic Scenario (Year 1)

| Month | Hosted Users | Paying | MRR | Cumulative Revenue |
|-------|-------------|--------|-----|-------------------|
| 1 | 50 | 5 | $45 | $45 |
| 3 | 250 | 30 | $270 | $810 |
| 6 | 800 | 120 | $1,080 | $4,860 |
| 9 | 2,000 | 350 | $3,150 | $14,175 |
| 12 | 4,000 | 700 | $6,300 | $31,500 |

### Year 2 Targets

| Metric | Target |
|--------|--------|
| MRR | $15,000 - $30,000 |
| Paying Customers | 1,500 - 3,000 |
| Self-Hosted Instances | 5,000+ |
| Education Customers | 50+ |
| Enterprise Customers | 5-10 |
| Team Size | 3-5 people |

## Implementation Timeline

### Month 1-2: Foundation
- [ ] Set up Stripe/PayPal merchant accounts
- [ ] Configure billing webhooks
- [ ] Create pricing page on website
- [ ] Set up analytics (Plausible or Fathom)

### Month 3-4: Launch
- [ ] Launch Free + Pro tiers
- [ ] Publish launch post on HN, Reddit, forums
- [ ] Contact 10 ceramics YouTubers for collaboration
- [ ] Submit to open source directories

### Month 5-6: Growth
- [ ] Launch Studio tier
- [ ] First blog posts (SEO content)
- [ ] Attend first ceramics conference
- [ ] Reach out to 5 art schools for Education pilot

### Month 7-12: Scale
- [ ] Launch Education tier
- [ ] Marketplace beta
- [ ] Partnership with kiln/clay suppliers
- [ ] Apply for arts/technology grants
- [ ] Consider seed funding for acceleration

## Success Metrics Dashboard

Track weekly:

```
┌─────────────────────────────────────────┐
│  OpenGlaze Revenue Dashboard            │
├─────────────────────────────────────────┤
│  MRR: $X,XXX                            │
│  New signups this week: XX              │
│  Free → Paid conversions: X%            │
│  Churn this month: X%                   │
│  Active self-hosted instances: XXX      │
│  AI queries this week: X,XXX            │
│  Support tickets: XX (avg response: Xh) │
└─────────────────────────────────────────┘
```

---

*This plan is a living document. Review and update quarterly based on actual data.*
