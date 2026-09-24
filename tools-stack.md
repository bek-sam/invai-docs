# InvAI — Recommended Tool Stack and Cost Model

As of Sep 23, 2026. Based on five research reports in [research/05–09](research/) and the model in [calc/cost_model.py](calc/cost_model.py) (run `python3 calc/cost_model.py`). Prices marked unverified in the reports are flagged at the end; confirm them before signing contracts.

**Bottom line:**

- **Almost all core software is free.** It is open source, and hosting on AWS is about $265/mo at pilot and $2,140/mo at scale.
- **The only big variable cost is the shipping-label fee.** It is bigger than everything else combined.
- **Margins:**
  - About 47% at pilot and 55% at scale if we charge shops $0.15/label.
  - Subscriptions alone give 71–77% margin once there are 20+ shops.
- **Scenarios used everywhere below:**

| Scenario | Shops | Orders per day |
| --- | --- | --- |
| Pilot | 3 | 900 |
| Growth | 20 | 8,000 |
| Scale | 100 | 40,000 |

---

## 1. The recommended stack

Paid items show their monthly cost as Pilot / Growth / Scale. Everything else is free and open source (you pay only for the servers it runs on).

### Frontend ([report](research/09-tools-frontend.md))

| Need | Pick | Runner-up | Why |
| --- | --- | --- | --- |
| App framework | **Vite 8 + React 19 SPA** with TanStack Router | Next.js 16 | Everything is behind a login, so server rendering adds complexity for nothing. Simpler offline support for the floor app. Hosts as static files anywhere |
| UI kit | **shadcn/ui + Tailwind v4** | Mantine 9 | You own the code; AI coding assistants know it best |
| Data tables | **TanStack Table 9 + Virtual** | AG Grid Community | Thousands of rows with virtual scrolling; matches shadcn. AG Grid Enterprise ($999 one-time) only if owners want Excel pivots |
| Server data / state | **TanStack Query + Zustand** | SWR + Jotai | Standard, with offline helpers |
| Forms | **react-hook-form + Zod** | TanStack Form | Most familiar to AI assistants |
| Charts | **Recharts** (shadcn charts) | ECharts | Enough for KPIs; ECharts for dense heatmaps |
| Gang-sheet viewer | **OpenSeadragon** with server-made zoom tiles | — | Browsers can't show a 6,600 × 72,000 px image directly |
| Design / template editor | **Konva (react-konva)** | Fabric.js; Polotno ($249/mo) only if customers self-edit | Edit on a low-resolution copy; the server renders the final file |
| Floor app offline + scanning | **vite-plugin-pwa + Dexie** + a ~50-line scanner hook + barcode-detector for the camera | STRICH (€99/mo) | onscan.js and html5-qrcode are unmaintained |
| AI chat UI | **Vercel AI SDK 7 + assistant-ui** | Hand-built with shadcn | Streaming and tool calls built in; no Vercel hosting needed |
| English + Spanish | **react-i18next** | Lingui | Floor staff can choose their language |

### Backend ([report](research/06-tools-backend.md))

| Need | Pick | Runner-up | Why |
| --- | --- | --- | --- |
| Runtime | **Node 24 LTS** | Bun | Every library targets Node first |
| API server | **Hono** | Fastify | Small, fast, standards-based |
| API contract | **oRPC** | tRPC | The same procedures give typed calls to the web app now and a public REST API with OpenAPI docs later |
| Database access | **Drizzle ORM** | Kysely | Company data walls (row-level security) defined in code next to the tables; one `withTenant()` helper |
| Background jobs | **BullMQ + Bull Board** + outbox table | Hatchet | About $40–600/mo of servers against $1,200–11,600/mo for Inngest, Trigger.dev or Temporal at scale. Its Python client lets the imaging service share the same queues |
| Login | **Better Auth** (organizations, roles, 2FA) + our own station-PIN plugin | WorkOS AuthKit | $0 at any size, and staff data stays in our database. No provider offers shared-tablet PIN switching, so we build it either way |
| Live updates to tablets | **Server-Sent Events + Redis pub/sub** | Centrifugo, or Ably at $36–351/mo | Tablets mostly listen; about $0 even at 1,000 devices |
| Imaging service | **Python FastAPI + pyvips**; long renders read from BullMQ directly | Litestar | Best image libraries are Python-only |
| Validation / env | **Zod v4 + t3-env** | Valibot | Shared by oRPC, Better Auth and the AI SDK |
| Monorepo / lint / tests | **pnpm + Turborepo, Biome, Vitest, Playwright** | Nx, ESLint | Least setup |

### Hosting and data ([report](research/05-tools-hosting.md))

| Need | Pick | Runner-up | Monthly cost | Why |
| --- | --- | --- | --- | --- |
| Hosting | **AWS**: ECS Fargate on ARM, set up with **SST v3** | Render ($260 / $785 / $2,065) | $265 / $810 / $2,140 (about $1.8k at scale with 1-year commitments) | Amazon's buyer-data rules require encryption keys, 12-month logs, a firewall, 30-day vulnerability scans and 30-day data deletion. AWS provides all of them. Moving hosts later costs more than the $75–150/mo a cheaper host saves |
| Database | **RDS PostgreSQL** (single-zone at pilot, Multi-AZ from growth) | Cloud SQL, Neon | Included above | Aurora Serverless costs about 2× RDS for a database that is always busy |
| Redis | **ElastiCache Valkey** nodes | Redis Cloud | Included above | Upstash bills per command, which is expensive with BullMQ |
| Files | **S3** with encryption, behind the **CloudFront $15 flat plan** (includes firewall) | Cloudflare R2 | Included above | The flat plan removes download fees; S3 lifecycle rules delete labels after 30 days |
| Money savers | NAT instance instead of NAT gateway (saves about $30/mo); imaging on Fargate Spot (up to 70% off) | — | — | — |

Avoid Fly.io and Railway for anything holding Amazon buyer data. Fly's managed Postgres docs say patching is "not there yet". Railway runs Postgres as a plain container, and its compliance features need an Enterprise contract.

### AI and imaging ([report](research/08-tools-ai-imaging.md))

| Need | Pick | Runner-up | Monthly cost | Why |
| --- | --- | --- | --- | --- |
| Listing copy, OCR, assistant | **Claude API**: `claude-opus-5` at low/medium effort with batch + caching; test `claude-sonnet-5` on real pilot data | `claude-sonnet-5` | Opus: $105 / $1,045 / $5,225 · Sonnet: $42 / $418 / $2,090 | The gap is about $31 per shop per month (1–2 points of margin), so choose on quality after an eval, not on price. Text inside designs is read in the same call for about $0.0005 |
| Design generation | **Ideogram 3 Transparent** (via fal): Turbo for drafts, Balanced for finals, about $0.042/image | GPT Image 1.5/2.5 (has IP indemnity) | $63 / $630 / $3,360 | Best text on shirts and the only strong model with native transparent PNG. Recraft ($0.08) when a vector SVG is needed |
| Upscale + background removal | **Real-ESRGAN + BiRefNet**, self-hosted on **Modal** GPUs | fal hosted versions | $4 / $30 / $148 | 10–100× cheaper than Topaz or remove.bg. Generative upscalers invent new text, so avoid them |
| Mockups | **Own compositor** (pyvips: displacement map + color tint) | Dynamic Mockups during pilot | $5 / $15 / $50 | Exact to the real blank; generative mockups distort the design |
| Trademark check | **Local USPTO index** + **Signa** API on the ~10% of flagged matches | Signa for every check | $119 / $139 / $479 | Covers trademarks only, not copyrighted characters |
| Keyword data | **DataForSEO**, cached across companies | Keywords Everywhere | $50 / $75 / $250 | No Etsy search-volume API exists |
| AI monitoring | **Langfuse** | Braintrust | $29 / $42 / $124 | Tracing, prompt versions and evals in one tool |
| Nesting | **rectpack** now; **jagua-rs/sparrow** for shape-aware nesting later | libnest2d | $0 | Shape-aware nesting may save 10–25% film |
| Forecasting | **statsforecast** | Prophet | $1 / $5 / $20 | Handles sparse sales per size and color |

### Outside services ([report](research/07-tools-services.md))

| Need | Pick | Runner-up | Monthly cost | Why |
| --- | --- | --- | --- | --- |
| Shipping labels | **EasyPost Forge** | ShipStation API, Shippo | $0.08/label (unverified; negotiate) | The only provider with documented platform markup (FlexRate) and code-free sub-accounts per shop |
| Silent label printing | **PrintNode** | QZ Tray ($62/mo flat; cheaper at scale) | $60 / $288 / $1,450 | The server pushes prints; no browser needs to stay open |
| Billing | **Stripe Billing, paid by ACH** | Polar, Paddle | See model | ACH is 0.8% capped at $5. Card fees on postage would cost about $174k/mo at scale |
| Email | **AWS SES** | Resend | $3 / $24 / $128 | Cheapest |
| Errors, analytics, logs | **Sentry + PostHog + Axiom** | New Relic free tier | $0 / $95 / $621 | Generous free tiers |
| Support chat | **Crisp** | Plain | $0 / $45 / $95 | Flat price |
| Uptime and on-call | **Better Stack** | UptimeRobot | $0 / $29 / $54 | Includes a status page |
| Search | **Postgres full-text search** | Typesense | $0 | Enough for order and design search |
| Code / CI / tasks | **GitHub + Actions + Renovate + GitHub Projects**; **CodeRabbit** reviews | Linear | $24 | 2,000 free CI minutes a month |

### Hardware per shop (one-time, paid by the shop; street prices, unverified)

| Item | Pick | Qty | Cost |
| --- | --- | --- | --- |
| Label printer | Zebra ZD421d (native ZPL) | 3 | ~$1,500 |
| Barcode scanner | Tera HW0002 (2D, Bluetooth) | 4 | ~$220 |
| Tablet | Samsung Galaxy Tab A9+ (Android works better for web apps than iPad) | 2 | ~$440 |
| Print host | Raspberry Pi 5 kit for PrintNode | 1 | ~$100 |
| **Total** | | | **~$2,260** (budget kit ~$1,085) |

---

## 2. Cost and margin model

Assumptions:
- **Plans:** $349/mo at pilot volume (300 orders/day); $699/mo at 400/day.
- **Label fees:** $0.15 per label charged to shops; EasyPost charges us $0.08 above 3,000 free labels.
- **Stripe:** subscriptions and label fees on one monthly ACH invoice; postage wallets topped up weekly by ACH.
- **Pen test:** about $6.5k a year, counted from growth, before the Amazon review.
- **Claude model:** the table uses Sonnet 5. With Opus 5 the margin is 1 point lower at every size.

| | Pilot | Growth | Scale |
| --- | --- | --- | --- |
| Shops | 3 | 20 | 100 |
| Orders (labels) per month | 27,000 | 240,000 | 1,200,000 |
| Subscription revenue | $1,047 | $13,980 | $69,900 |
| Label fee revenue ($0.15) | $4,050 | $36,000 | $180,000 |
| **Total revenue** | **$5,097** | **$49,980** | **$249,900** |
| Platform costs (hosting, AI, services, tools) | $666 | $3,219 | $11,623 |
| EasyPost label fees ($0.08) | $1,920 | $18,960 | $95,760 |
| Stripe fees | $117 | $893 | $4,464 |
| **Gross profit** | **$2,394** | **$26,908** | **$138,053** |
| Gross margin | 47% | 54% | 55% |
| Margin on subscriptions alone | 25% | 71% | 77% |
| Platform cost per shop | $222 | $161 | $116 |

What the numbers say:

1. **Platform costs are small and fall per shop as we grow**, from $222 to $116 per shop per month. The largest lines at scale are design generation ($3,360), hosting ($2,140) and the Claude API ($2,090 with Sonnet 5).
2. **The pilot runs at a thin margin** because fixed costs (hosting, trademark data, keyword data) are spread over 3 shops. That's normal, and pilots are free for 3 months anyway.
3. **Label fees set profit and price.** Scale sensitivity, gross profit per month:

| Our label price → / EasyPost fee ↓ | $0.05 | $0.08 | $0.10 | $0.15 |
| --- | --- | --- | --- | --- |
| $0.08 (list price, unverified) | $18,893 (15%) | $54,641 (33%) | $78,473 (41%) | $138,053 (55%) |
| $0.05 (negotiated) | $54,803 (42%) | $90,551 (55%) | $114,383 (60%) | $173,963 (70%) |
| $0.03 (volume deal) | $78,743 (61%) | $114,491 (69%) | $138,323 (73%) | $197,903 (79%) |

What a 400-orders/day shop pays us per month (plan plus label fees): $1,299 at $0.05 per label, $1,659 at $0.08, $1,899 at $0.10, $2,499 at $0.15.

**Pricing recommendation:** charge **$0.10 per label** and negotiate EasyPost to **$0.05 or less** before growth. That gives about 60% margin at scale. A 400/day shop then pays about $1,900/mo. In exchange it drops ShipStation, the outside gang-sheet service, listing and SEO tools, a mockup tool and spreadsheets. Check that total against what pilot shops pay today; it's question 9 in the concept doc. Charging $0.15 per label makes our price higher than Pythias ($599–1,499), which could cost us sales.

---

## 3. Changes to the architecture doc

The research changed these earlier choices; [architecture.md](architecture.md) has been updated to match.

| Area | Before | Now | Reason |
| --- | --- | --- | --- |
| Web app | Next.js | Vite + React SPA | Behind a login; simpler offline support; static hosting |
| API | Fastify + tRPC | Hono + oRPC | One API gives typed internal calls and public REST |
| Realtime | WebSocket gateway | Server-Sent Events + Redis | Tablets mostly receive; fewer moving parts |
| Default AI model | Opus 5 only | Opus 5 vs Sonnet 5, decided by an eval on pilot data | Cost gap is small, so quality decides |
| Image generation | "a hosted image model" | Ideogram 3 via fal; Recraft for vector | Text quality and transparent PNG |
| GPU work | Replicate/fal/Modal | Modal (self-hosted open models) | Cheapest; $30/mo free credit covers the pilot |

---

## 4. Verify before committing

1. **EasyPost's per-label fee** above 3,000 labels, Forge contract terms, and whether FlexRate markup requires us to collect postage from shops.
2. **Whether TikTok Shop still allows labels bought outside TikTok** in the US.
3. **Ideogram 4.0 and GPT Image 2.5 per-image prices**, and IP indemnity terms per image provider.
4. **PrintNode vs QZ Tray** on the pilot shops' actual printers.
5. **Cloud security tooling cost** (GuardDuty, Security Hub, Inspector) and a pen-test quote.
6. **Mockup and upscale speed on Modal.** The runtimes used here are estimates.
7. **Hardware prices** at the time of purchase.

Full per-item verification notes are in each research report.
