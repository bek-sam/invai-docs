# InvAI Stack Research: Comparison and Recommendations (as of 2026-09-23)

**How this was checked**
- **GitHub stars, licenses and last-push dates** came live from the GitHub API today.
- **Weekly downloads** came from api.npmjs.org for Sep 15–21, 2026.
- **Package versions** came from npm and PyPI.
- **Prices** came from each vendor's pricing page through WebFetch. A small model summarised those pages, so recheck any number before you commit money.
- **Web search was used up** for this session, so I fetched pages directly.
- **Flags:** ⚠️UNVERIFIED means I couldn't confirm it today (from memory or from a page summary that looked inconsistent). "Estimate" means my own infrastructure sizing.

**Shared assumptions for the cost maths**
- **Job runs per month** = runs per day × 30:
  - Pilot: 50k × 30 = **1.5M runs/mo**
  - Growth: 400k × 30 = **12M runs/mo**
  - Scale: 2M × 30 = **60M runs/mo**
- **Realtime devices** are online 12 h/day for 30 days:
  - Connection-minutes = devices × 720 × 30.
  - Messages = orders/day × 10 status events × 10 subscribed devices × 30 days.
  - Pilot: 900 × 100 × 30 = 2.7M msgs/mo
  - Growth: 8,000 × 100 × 30 = 24M msgs/mo
  - Scale: 40,000 × 100 × 30 = 120M msgs/mo

---

## 1. API framework and API style

### 1a. HTTP framework

| Option | Maturity (stars / npm per week / version) | Cost | Pros | Cons | Fit |
|---|---|---|---|---|---|
| **Hono** | 32.3k★ / 46.1M per week (+42.9M @hono/node-server) / v4.13.9 | OSS (MIT) | Built on Web standards, so it runs on Node, Bun, Deno and edge runtimes. Tiny and fast. `@hono/zod-openapi` (1.59M per week) gives REST + OpenAPI + a typed `hc` client. oRPC and Better Auth both mount on it cleanly. | You assemble the pieces yourself (no DI, no module system). The Node adapter adds a thin layer. | **9** |
| **Fastify** | 37.2k★ / 9.6M per week / v5.12.5 | OSS (MIT) | Most mature high-performance Node server. Strong plugin set (rate-limit, swagger, websockets, SSE). Validation and serialisation driven by schemas. | Node only. Its plugin/encapsulation model has a learning curve. Type-provider typing is more verbose than Hono's. | **8.5** |
| NestJS | 76.7k★ / 10.3M per week / v12.1.0 | OSS (MIT) | Batteries included: DI, modules, first-party BullMQ module, Swagger, guards. Suits larger teams. | Heavy boilerplate and decorators, which is a lot for a solo developer. Slower iteration. Awkward alongside Zod-first contracts. | 6.5 |
| Express 5 | 69.5k★ / 101M per week / v5.2.1 | OSS | Everyone knows it, and the ecosystem is huge. | Slowest option. Types are bolted on. No built-in validation or OpenAPI. Mostly legacy momentum. | 5 |
| Elysia (Bun) | 19.2k★ / 0.81M per week / v1.4.30 | OSS | Excellent end-to-end types (Eden). Very fast on Bun. | Tied to Bun; the Node adapter is secondary. Relies heavily on one maintainer (⚠️ my assessment). Smaller ecosystem. | 5.5 |
| Next.js route handlers only | (part of Next.js) | $0 | No second service to run. | Wrong home for workers, long renders, persistent connections and webhooks with retries. Serverless timeouts. Ties the public API to the web app's deploy cycle. | 3 |
| AdonisJS | 19.1k★ / 88k per week (@adonisjs/core) | OSS | Laravel-style, batteries included (Lucid ORM, auth, validation). | Small community. Its own ORM and validator clash with Drizzle/Zod. Weaker RLS story. | 5 |

### 1b. API style (typed internal API plus a public REST API later)

| Option | Maturity | Pros | Cons | Fit |
|---|---|---|---|---|
| **oRPC** | middleapi/orpc ~5.6k★ (page summary, ⚠️) / @orpc/server 946k per week / v1.15.4 | Contract-first. **Built-in OpenAPI generation**, so the same procedures can serve typed RPC to Next.js *and* the public REST API. First-class TanStack Query support. Standard Schema, so it works with Zod, Valibot or ArkType. Adapters for Hono, Fastify, Next and Node. | Younger than tRPC and a smaller community. | **9** |
| tRPC v11 | 40.7k★ / 3.7M per week / v11.19.0 | Most proven option; excellent Next.js/React Query DX. | Not REST. A public API needs a third-party trpc-to-openapi layer or a second API. | 7.5 |
| Hono + zod-openapi (plain OpenAPI) | 1.59M per week | REST-native from day one. Real OpenAPI document. `hc` typed client. | RPC ergonomics are clunkier (route definitions are verbose). You write your own React Query wrappers. | 8 |
| ts-rest | 3.3k★ / 479k per week / **last push 2026-02-06** | Contract-first REST. | Development seems to have slowed (no pushes for about 7 months). | 5 |
| GraphQL | graphql 33.9M per week | Flexible querying for dashboards. | Overkill for a solo developer: N+1 problems, auth per resolver, caching. Public GraphQL is a poor match for print-shop integrators. | 4 |

**Recommendation:** use **Hono on Node 24 with oRPC**. oRPC's `RPCHandler` serves the Next.js app and its `OpenAPIHandler` exposes the same procedures as public REST later. One schema source (Zod) drives types, validation and OpenAPI. Mount Better Auth and webhook routes directly on Hono.
**Runner-up:** Fastify + tRPC, if you want the most battle-tested pieces and can accept a separate REST layer later.

---

## 2. ORM / query layer and Postgres RLS

**The pattern that works everywhere:**
- Open a transaction, run `select set_config('app.company_id', $1, true)` (the same as `SET LOCAL`), then run your queries.
- **Critical settings that apply whatever the ORM:**
  - Connect as a role that is not the table owner and has no BYPASSRLS, or use `FORCE ROW LEVEL SECURITY`.
  - Policies use `company_id = (select current_setting('app.company_id', true))::uuid`. The subselect lets Postgres evaluate it once instead of per row.
  - Index `company_id`.
  - `SET LOCAL` is safe behind PgBouncer in transaction mode; plain session `SET` is not.

| Option | Maturity | How RLS via SET LOCAL works | Pros | Cons | Fit |
|---|---|---|---|---|---|
| **Drizzle** | 35.9k★ / 16.3M per week / stable **0.45.3**; **1.0 is at RC** (`rc` tag 1.0.0-rc.4). Source: orm.drizzle.team/docs/rls | `db.transaction(async tx => { await tx.execute(sql\`select set_config(...)\`); ... })` is trivial. **Policies and roles live in the schema** (`pgPolicy`, `pgRole`, `.withRLS()`), and drizzle-kit generates their migrations. | SQL-like and type-safe. No engine binary. Fast. RLS is a first-class feature. | Still pre-1.0; the move to 1.0 brings some API changes (relational queries v2). Migrations are less polished than Prisma's. | **9.5** |
| **Kysely** | 14.2k★ / 12.0M per week | `db.transaction().execute(async trx => { await sql\`select set_config(...)\`.execute(trx); ... })` | Most transparent SQL builder. Excellent types. Rock solid. | No schema or migration generator (you write SQL migrations, which suits RLS anyway). No relations API. | 9 |
| Prisma 7 (stable 7.10.0; 7.0 released 2025-11-19; **8.0 RC** in progress, rc.15 on 2026-09-14) | prisma/orm 47.7k★ / 12.2M per week | v7 is Rust-free and requires driver adapters (`@prisma/adapter-pg`). RLS runs through a **client extension** that wraps each query in a batch `$transaction([set_config, query])`. | Best migrations, schema DX and Studio. v7 removed the Rust engine (smaller, faster). | **No RLS policies in the schema** (you manage them in raw SQL migrations). The per-query transaction wrapping costs performance and fits badly with interactive transactions. `$use` middleware was removed in v7. Churn from 7 to 8. | 6.5 |
| TypeORM | 36.7k★ / 3.56M per week | Via a QueryRunner transaction plus a raw `set_config`. | Familiar to NestJS users. | Weak typing. History of slow maintenance. Decorator-based entities. | 4 |
| MikroORM | 9.2k★ / 659k per week | `em.transactional` plus `execute`. It also has app-level filters. | Unit of work, good design. | Smaller community. The identity map adds complexity when combined with per-tenant transactions. | 6 |

**Recommendation:** **Drizzle**. You define RLS policies in TypeScript, so policies and migrations stay together. Use one `withTenant(companyId, fn)` helper that opens the transaction and runs `set_config`. Pin to 0.45.x or adopt 1.0 once it goes GA.
**Runner-up:** Kysely with hand-written SQL migrations. Avoid Prisma for an RLS-centric design.

---

## 3. Background jobs and workflows (the most important choice)

**Requirements:**
- Order sync every 5–10 minutes per connection.
- Webhooks, retries and idempotency.
- **Rate limiting per external API and per connection.**
- Cron.
- Long renders and fan-out.

Average load at Scale is 2M/86,400 ≈ **23 jobs/s**, maybe around 230/s at a 10× peak. Every option below handles this; the difference is cost and features.

### Cost assumptions
- Self-hosted infrastructure numbers are my estimates for a small VPS or PaaS. Redis is already in your stack.
- Inngest bills an execution for each run plus each step; I show 1 execution per run and 3 per run.
- Temporal: 2 actions per run (workflow start plus one activity).
- Trigger.dev: invocation $0.000025 per run plus compute. Low case is Micro at $0.0000169/s × 2 s; high case is Small-1x at $0.0000338/s × 5 s.
- AWS: Lambda at 512 MB × 5 s = 2.5 GB-s per run at $0.0000166667 per GB-s, plus SQS at 3 requests per run.

| Option | Price basis (source) | Pilot 1.5M/mo | Growth 12M/mo | Scale 60M/mo | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **BullMQ (self-hosted, OSS MIT)** + Bull Board (free, 1.25M per week) | $0 licence; you pay for Redis and workers | Estimate **~$40–70** (1 worker VM + Redis) | Estimate **~$100–200** (2–3 workers, Redis with a replica) | Estimate **~$300–600** (4–6 workers, Redis HA 4 GB) | 9.4k★, 5.9M per week, v6.3.8. Retries/backoff, `jobId` idempotency, deduplication, Job Schedulers (cron), **Flows (parent/child fan-out)**, per-queue rate limiter, manual `RateLimitError`. There is an **official Python client** (`bullmq` 3.2.6 on PyPI), so the imaging service can consume the same queues. Reuses your Redis. | Per-group (per-tenant or per-connection) rate limiting and concurrency need **BullMQ Pro** (Groups); OSS workarounds are a queue per provider or a Redis token bucket. Redis must run with `maxmemory-policy noeviction` and persistence (AOF). No transactional enqueue with Postgres. Taskforce.sh pricing ⚠️UNVERIFIED (page is rendered by JS; I believe it is roughly $20–100/mo per tier). BullMQ Pro prices are ⚠️UNVERIFIED; its docs only say "per-organization license". | **9** |
| pg-boss (MIT) | $0; uses your Postgres | ~$0 extra (more database load) | ~$0–50 | Estimate +$50–150 for a bigger database | 4.0k★, 1.24M per week, v12.34. **Transactional enqueue** in the same transaction as your data, so it doubles as an outbox. Cron, singleton/throttle/debounce, dead-letter queues. | About 60M rows/mo of churn means careful archive/vacuum. Rate limiting per key is basic. The job tables sit next to RLS tables, so they need a separate schema and role. | 7.5 |
| Graphile Worker (MIT) | $0; Postgres | ~$0 | ~$0–50 | +$50–150 | 2.4k★, 396k per week, v0.18. LISTEN/NOTIFY with under 3 ms latency, `job_key` deduplication, crontab, serial named queues, batch jobs (worker.graphile.org). | Still 0.x. Rate limiting needs an add-on. Smaller community. | 7 |
| Temporal (self-hosted MIT, or Cloud) | Cloud: from **$50 per 1M actions**, dropping to $25/M with volume; no base fee on pay-as-you-go; storage $0.042 per GB-hour active; $500/mo Business support add-on (temporal.io/pricing) | 1.5M × 2 = 3M actions × $50/M = **$150** + workers | 24M × $50/M = **$1,200** (down to ~$600 at $25/M) + workers | 120M × $25–50/M = **$3,000–6,000** + workers | Gold standard for durable workflows (23.3k★). Great for long multi-step order-to-sheet-to-print sagas. | Steep learning curve (determinism rules). Self-hosting is heavy (Cassandra or Postgres + ES). Overkill for polling jobs. | 6 |
| Inngest (Cloud; source-available ⚠️SSPL-style licence, GitHub reports NOASSERTION) | Free: 50k executions. **Pro $99** includes 1M, overage **$0.000050 down to $0.000015 per execution** (tiered). Business $499 includes 10M. An execution is counted per run *and* per step (inngest.com/pricing). | 1 per run: 99 + 0.5M × $0.00005 = **$124**. 3 per run: 4.5M → 99 + 3.5M × $0.00005 = **$274** | 1 per run: Business 499 + 2M × ($0.000015–0.00005) = **$529–599**. 3 per run (36M): 499 + 26M × (…) = **$889–1,799** | 1 per run (60M): 499 + 50M × (…) = **$1,249–2,999**. 3 per run (180M): **$3,049–8,999**, realistically Enterprise | Best DX. Built-in concurrency/throttle **keyed per tenant**, debounce, idempotency, fan-out, cron. | You still host the compute behind an HTTP endpoint. Cost grows with steps. Limits: 1,000 steps per function, 2 h per step, 4 MiB step output. Vendor lock-in to the event model. | 6.5 |
| Trigger.dev v4 (Apache-2.0, self-hostable) | Pro **$50/mo includes $50 usage**. $0.000025 per run + compute per second (Micro $0.0000169, Small-1x $0.0000338). Concurrency 200+ (trigger.dev/pricing) | Low: 1.5M × (0.000025 + 2 × 0.0000169) = 1.5M × $0.0000588 = **$88**. High: 1.5M × (0.000025 + 5 × 0.0000338) = 1.5M × $0.000194 = **$291** | Low **$706**, high **$2,328** | Low **$3,528**, high **$11,640** | Runs the compute for you (no worker servers). Checkpointed waits. Long tasks without timeouts. Good dashboard, queues and concurrency keys. | Most expensive at scale for short, frequent jobs. Each run is a container, which adds latency. Self-hosting v4 is a whole platform to operate. | 6.5 |
| Hatchet (MIT, self-host or Cloud) | Developer: free up to 100k runs, then **$10 per 1M runs**. Team $500/mo, Scale $1,000/mo (hatchet.run/pricing) | (1.5 − 0.1) × $10 = **$14** (Developer tier) | 11.9 × $10 = **$119**, or $500+ on Team | 59.9 × $10 = **$599**, or $1,000+ | 8.0k★. Postgres-backed. **Built-in per-key rate limits and fair concurrency** (per tenant or per connection). Durable workflows, cron, fan-out. TypeScript and Python SDKs, so the imaging service can be a worker. | Young and fast-moving. Unclear whether the Developer tier is meant for production (⚠️). Self-hosting means running the Hatchet engine plus Postgres. | **8** |
| Restate | Cloud pricing ⚠️UNVERIFIED (page not readable). Licence shows NOASSERTION on GitHub (I believe it is BSL ⚠️) | n/a | n/a | n/a | Durable execution with low latency. Single binary. | Smallest ecosystem (158k per week). BSL-style licence risk. | 5 |
| AWS SQS + Lambda (+ Step Functions) | SQS 1M requests/mo free, then ⚠️$0.40/M standard (rate not on the fetched page). Lambda $0.20/M + $0.0000166667 per GB-s. Step Functions Standard $0.000025 per transition; Express $1/M (aws.amazon.com) | 3.75M GB-s − 0.4M free = 3.35M × $0.0000166667 = $56, + SQS (4.5M − 1M) × $0.40/M = $1.40, + requests about $0.10 → **~$57**. Step Functions at 4 transitions per run adds 6M × $0.000025 = **$150** | 30M GB-s = $500 + $14 SQS + $2.40 → **~$517** (+$1,200 with Step Functions) | 150M GB-s = $2,500 + $72 + $12 → **~$2,584** (+$6,000 with Step Functions) | Scales to anything. No servers. | VPC + NAT (about $32/mo or more ⚠️) to reach Postgres and Redis. 15-minute Lambda cap. Cold starts. Heavy AWS lock-in. Local development is painful for a solo developer. | 5 |

**Recommendation:** **BullMQ, self-hosted on your existing Redis.**
- It is the cheapest at every tier: roughly $40–600/mo versus $1.2k–11k for the managed options at Scale.
- It is TypeScript-native, with Flows for fan-out, Job Schedulers for per-connection sync, and `jobId` for idempotency.
- Its official Python client lets the imaging service share the same queues.
- Pair it with a small **transactional outbox table in Postgres**, so enqueueing is atomic with your writes.
- Enforce per-connection and per-API limits with a Redis token bucket, or buy BullMQ Pro Groups if that becomes painful.
- Use Bull Board as the free admin UI.

**Runner-up:** **Hatchet**. Pick it if per-tenant fairness and rate limiting out of the box matter more than Redis familiarity. Its Cloud pricing at $10/M runs is the cheapest managed option.
**Avoid:** Trigger.dev and Inngest, which are priced per run or per step, for high-frequency polling at Scale. They are fine for a small number of AI or long-running workflows if you want managed durability for those alone.

---

## 4. Authentication (organisations, roles, PIN login for floor staff, 2FA)

**Nobody offers shared-tablet PIN login.**
- None of the hosted providers supports "shared tablet, staff switch in with a 4–6 digit PIN" natively (⚠️ based on docs reviewed).
- The usual design: the tablet authenticates as a **device/station** credential, and staff switch with a PIN checked by *your* backend, which issues a short-lived, narrowly scoped session.
- With Better Auth that is a small custom plugin. With hosted providers you build it beside them anyway.

**Amazon PII:** the auth provider holds staff identities, not buyer PII. It is still a sub-processor to list. Self-hosting keeps all data in your Postgres and your region.

**Seats:** Pilot is 60 users / 3 orgs, Growth 500 / 20, Scale 3,000 / 100.

| Option | Price basis (source) | Pilot | Growth | Scale | Organisations and roles, SSO, 2FA | Self-host, data location | Fit |
|---|---|---|---|---|---|---|---|
| **Better Auth** | MIT, $0. 30.1k★, 6.07M per week, v1.7.5 | **$0** | **$0** | **$0** | Organisation plugin: owner/admin/member, **dynamic per-org roles** (access control), teams, invitations; default cap of 100 members per org, configurable. 2FA plugin: TOTP, email/SMS OTP, backup codes, trusted devices. Passkeys, SSO plugin. | Your Postgres, your region (best for the Amazon review). Works with Drizzle. | **9.5** |
| WorkOS AuthKit | **Free up to 1M MAU**. SSO / Directory Sync $125 per connection. Custom domain $99/mo (workos.com/pricing) | $0 | $0 | $0 (+$99 custom domain, +$125 per enterprise SSO customer) | Organisations, per-org custom roles, MFA included. Best-in-class enterprise SSO. | Hosted only (US ⚠️). | 8 |
| Clerk | Pro **$25/mo** (MFA needs Pro). 50k MRU and 100 organisations included; orgs capped at **20 members** unless you buy B2B add-on at $100/mo (clerk.com/pricing) | $25 (+$100 if any shop has more than 20 staff) = **$25–125** | 500 / 20 = 25 members per org, so add-on needed: **$125** | 3,000 / 100 = 30 per org, so add-on; 100 orgs included: **$125** | Best prebuilt UI for Next.js. Orgs, roles, MFA. | Hosted (US ⚠️). High lock-in (components, user IDs). | 7 |
| Kinde | Free: 10.5k MAU, 5 orgs, only 2 roles. **Pro $25**: 50 orgs, then $0.50 per extra org (kinde.com/pricing) | $25 (Free lacks the roles you need) | $25 | 25 + 50 × $0.50 = **$50** | Unlimited roles on Pro. MFA. | Hosted. | 6.5 |
| Stytch B2B | Free: 10k MAU, unlimited orgs, 5 SSO connections, then $125 per connection (stytch.com/pricing) | $0 | $0 | $0 | Strong B2B model, org-level MFA policies. | Hosted. Ownership changed (I believe Twilio acquired it ⚠️UNVERIFIED). | 7 |
| Auth0 B2B | Essentials: about **$150/mo at 500 MAU**, $300 at 1k. Free tier has no MFA and 5 orgs (auth0.com/pricing; tier figures ⚠️ the page summary was inconsistent) | $150 | $150 | Around $525–1,300 at 3k MAU (⚠️) | Mature orgs, RBAC, enterprise MFA. | Hosted; EU/US tenant regions. | 5 |
| Supabase Auth | Pro **$25**: 100k MAU; TOTP MFA free; phone MFA $75 (supabase.com/pricing) | $25 | $25 | $25 | **No built-in organisations or RBAC** (you build it with claims and RLS). | Awkward if your Postgres isn't Supabase. | 5 |
| Zitadel | Cloud Free: 100 DAU. Pro **$100/mo** (25k DAU). **AGPL-3.0** self-host (zitadel.com/pricing, GitHub) | $0 | $100 | $100 | Multi-tenant organisations are native. Strong RBAC and MFA. | Self-host (Go, 15.1k★), but AGPL. | 6.5 |
| Keycloak | Apache-2.0, 37.0k★; you host it | Estimate ~$20–50 infrastructure | ~$20–50 | ~$50–100 | Everything (realms, organisations, SSO, MFA). | JVM with a real operations burden; clunky for a solo developer. | 5 |
| Lucia | **Deprecated March 2025**; the README now points to a single-file reference implementation | — | — | — | — | Don't use it. | 1 |

**Recommendation:** **Better Auth**. It costs $0 at every tier, keeps data in your own RLS Postgres (the cleanest story for the Amazon PII review), includes org plugin roles and 2FA, and lets you write the custom **station + PIN** plugin in-process. Add Better Auth's SSO plugin, or WorkOS SSO alone, if an enterprise customer later asks for SAML.
**Runner-up:** **WorkOS AuthKit**, if you'd rather not own auth security. It is $0 up to 1M MAU and has the best SSO path, but PIN login stays custom.

---

## 5. Validation, env, monorepo and dev tooling

| Area | Options (npm per week, version, stars) | Recommendation | Why | Runner-up |
|---|---|---|---|---|
| Validation | **Zod v4** (212M per week, v4.6.5, 44.0k★); Valibot (13.4M, 9.0k★); ArkType (1.35M, 7.9k★) | **Zod v4** (9.5/10) | Default schema library for oRPC, Hono zod-openapi, Better Auth, the AI SDK and t3-env. v4 is much faster and has `zod/mini` for small bundles. Valibot and ArkType are fine but have smaller ecosystems. Standard Schema keeps switching possible. | Valibot (8) |
| Env | @t3-oss/env-core with Zod | t3-env | Typed, validated env shared across apps. | envalid |
| Monorepo | **pnpm + Turborepo** (turbo 17.6M per week, v2.11.3, 31.1k★); Nx (7.1M, 29.4k★); Bun workspaces | **pnpm + Turborepo** (9) | Least configuration, fast caching, strict pnpm dependency isolation. Wrap the Python app with a `package.json` script that calls `uv`. Nx is better polyglot but heavier. Bun workspaces tie you to Bun. | Nx (7.5) |
| Lint and format | **Biome** v2.5.14 (10.7M per week, 25.9k★); ESLint (120M) + Prettier | **Biome** (8.5) | One fast tool. v2 adds type-aware rules such as floating-promises (⚠️ confirm the rule has left nursery). Keep a minimal typescript-eslint pass *only* if you need rules Biome lacks. Unhandled promises in job code are the big risk. | ESLint flat config + Prettier (7.5) |
| Unit tests | Vitest v5.0.1 (73.8M per week) | **Vitest** | Standard for TypeScript. Use Testcontainers Postgres for RLS tests (⚠️ suggestion). | — |
| End-to-end | Playwright (@playwright/test 44.4M per week) | **Playwright** | Can emulate tablets. | — |
| Runtime | Node 22 (maintenance LTS since 2025-10-21, EOL **2027-04-30**); **Node 24** (LTS; maintenance from 2026-10-20; EOL **2028-04-30**); Node 26 (Current, **LTS on 2026-10-28**, EOL 2029-04-30); Bun; Deno 2 (source: nodejs/Release schedule.json) | **Node 24 LTS** (9). Move to 26 after it reaches LTS. | Every dependency here (BullMQ, Drizzle, Better Auth, sharp) targets Node first. Bun is fast but adds compatibility risk for workers and native modules. Deno has the weakest fit. Note: from Node 27 the project moves to one major release per year. | Bun (6) |

---

## 6. Python imaging service

| Option | Maturity | Pros | Cons | Fit |
|---|---|---|---|---|
| **FastAPI** | 102.6k★, v0.141.1 | Largest ecosystem, Pydantic v2, OpenAPI you can turn into a typed TypeScript client. | Still 0.x versioning. CPU-bound renders need plain `def` handlers or a process pool, not async. | **9** |
| Litestar | 8.5k★, v2.24.0 | Faster serialisation (msgspec), more structured, 2.x stable. | Smaller community. | 7.5 |
| Flask | 74.8k★ | Simple. | WSGI; no built-in validation or OpenAPI. | 5.5 |

| How renders run | Pros | Cons | Fit |
|---|---|---|---|
| **HTTP call from the BullMQ worker** (idempotency key, results written to S3/R2) | Simple; one queue system; retries owned by BullMQ. | Long renders over HTTP need generous timeouts; the worker slot stays busy while it waits. | **8.5** for renders under ~2–5 min |
| **BullMQ Python worker** (official `bullmq` 3.2.6 on PyPI) | Same queues and retry semantics; no HTTP timeouts; the Python side scales on its own. | The Python client has fewer features than the Node one (⚠️ check Flows and rate limiting support). | **8.5** for long renders |
| Celery 5.6.3 | Mature. | Second broker and a second retry/monitoring system on top of BullMQ. | 5 |
| Dramatiq 2.2.1 | Simpler than Celery. | Still a second queue system. | 5.5 |

**Recommendation:** **FastAPI**. Short renders are called over HTTP from the BullMQ worker; long gang-sheet renders are consumed directly by a BullMQ Python worker.
**Runner-up:** Litestar.

---

## 7. Realtime for floor tablets and dashboards

Volumes: Pilot 30 devices, 2.7M msgs/mo, 648k connection-minutes. Growth 200 devices, 24M msgs, 4.32M connection-minutes. Scale 1,000 devices, 120M msgs, 21.6M connection-minutes.

| Option | Price basis (source) | Pilot | Growth | Scale | Pros | Cons | Fit |
|---|---|---|---|---|---|---|---|
| **SSE from the API + Redis pub/sub** (replay from a Redis Stream via Last-Event-ID) | $0; runs on the existing API | ~$0 | ~$0–10 | Estimate ~$10–40 | Fewest moving parts. Plain HTTP, works through proxies, native browser reconnect. Tablets send commands with ordinary POSTs. | One-way only. You add heartbeats (proxy idle timeouts) and a replay buffer yourself. | **9** |
| Socket.io + Redis adapter (self-hosted) | $0 (63.2k★, 13.6M per week) | ~$0 | ~$0–10 | ~$10–40 | Rooms per org or station, acks, connection-state recovery, bidirectional. | Sticky sessions with multiple nodes. Its own protocol. | 8.5 |
| Centrifugo OSS (Apache-2.0, 10.8k★) | $0 + a small VM; PRO is quote-only | Estimate ~$5–10 | ~$10 | ~$20–40 | Go binary. Redis engine, JWT channel permissions, **history and recovery on reconnect** (good on flaky shop Wi-Fi), SSE/WebSocket transports. | Another service to run. | 8 |
| Ably | Free: 6M msgs, 200 connections. Standard **$29** + $2.50 per M msgs + $1.00 per M connection-minutes (ably.com/pricing; channel-minute charges ⚠️) | Free, or 29 + 2.7 × 2.5 + 0.65 × 1 = **~$36** | 29 + 24 × 2.5 + 4.32 = **~$93** | 29 + 120 × 2.5 + 21.6 = **~$351** | Managed, global, message history, strong reliability. | Cost grows with fan-out. Data leaves your infrastructure. | 7 |
| Pusher Channels | Sandbox free (200k/day, 100 connections). Startup $49 (1M/day, 500). Pro $99 (4M/day, 2,000). Business $299 (pusher.com/channels/pricing) | 90k/day → **$0** | 800k/day → **$49** | 4M/day → **$99** (at the cap) to **$299** | Simple; widely used. | Daily message caps with fan-out counted; no replay. | 6.5 |
| Supabase Realtime | Pro $25: 500 connections and 5M msgs, then $10 per 1,000 connections and $2.50 per M msgs | **$25** | 25 + 19 × 2.5 = **$72.50** | 25 + $10 + 115 × 2.5 = **$322.50** | Broadcast and presence. | Postgres Changes needs Supabase Postgres; otherwise lock-in with no benefit. | 5 |
| Soketi (Pusher-compatible) | $0 | ~$0 | ~$0 | ~$0 | Cheap Pusher replacement. | **Last push 2025-03-03**, so looks stale. The uWebSockets dependency causes Node-version friction. | 3 |
| PartyKit | Cloudflare (acquired, ⚠️ from memory); last push 2026-01-29; 22k per week | ~$5 Workers plan + Durable Object usage (⚠️) | ~$5–20 | ~$20–50 | Stateful rooms at the edge. | Cloudflare lock-in; stagnant repository. | 4 |
| uWebSockets.js | 9.2k★ | $0 | $0 | $0 | Fastest option. | Low-level; installed from GitHub rather than npm; overkill at 1,000 connections. | 4 |
| ElectricSQL (Apache-2.0, 10.4k★, 1.02M per week) | Self-host $0; cloud ⚠️ | — | — | — | Postgres-to-client sync for live dashboards. | **Postgres RLS doesn't apply to shapes**, so tenant authorisation must happen in a proxy. More architecture than you need. | 5 |

**Recommendation:** **SSE on your API, fed by Redis pub/sub, with a Redis Stream for replay**. It costs about $0 at every tier, since 1,000 connections is trivial for one Node process, and it matches the tablets' mostly-receive traffic.
**Runner-up:** **Centrifugo** (or Socket.io), if you need bidirectional messaging or presence. Use **Ably** if you want managed realtime (about $36–351/mo).

---

## Final stack at a glance

| Area | Pick | Runner-up |
|---|---|---|
| API | Hono (Node 24) + oRPC (OpenAPI later from the same procedures) | Fastify + tRPC |
| ORM | Drizzle with `set_config(..., true)` per-transaction helper and policies in schema | Kysely |
| Jobs | BullMQ + outbox + Bull Board | Hatchet |
| Auth | Better Auth (org, 2FA, custom station+PIN plugin) | WorkOS AuthKit |
| Tooling | Zod v4, t3-env, pnpm + Turborepo, Biome, Vitest, Playwright, Node 24 | Valibot, Nx, ESLint |
| Imaging | FastAPI; BullMQ Python worker for long renders | Litestar |
| Realtime | SSE + Redis pub/sub/Streams | Centrifugo / Ably |

**Estimated monthly platform cost for the recommended stack** (jobs + auth + realtime, excluding Postgres, Next.js hosting and AI): Pilot ~$40–80, Growth ~$100–210, Scale ~$310–640. All self-hosted, so these are infrastructure estimates. The cheapest managed alternative (Hatchet Cloud + WorkOS + Ably) would be roughly $50 / $212–593 / $950–1,350+.

**Items to recheck before committing:**
- Taskforce.sh and BullMQ Pro prices
- Restate pricing and licence
- Auth0 tier prices at 3k MAU
- SQS per-request rate
- Whether Hatchet's Developer tier is allowed for production
- Ably channel-minute charges
- Inngest's exact overage tiers
- Stytch ownership
- PartyKit status
- Whether Biome's floating-promises rule is stable

**Sources:** inngest.com/pricing, inngest.com/docs/usage-limits/inngest, trigger.dev/pricing, temporal.io/pricing, docs.temporal.io/cloud/actions, hatchet.run/pricing, aws.amazon.com/step-functions/pricing, aws.amazon.com/sqs/pricing, docs.bullmq.io/bullmq-pro/introduction, worker.graphile.org/docs, clerk.com/pricing, workos.com/pricing, workos.com/docs/authkit/roles-and-permissions, auth0.com/pricing, stytch.com/pricing, kinde.com/pricing, supabase.com/pricing, zitadel.com/pricing, better-auth.com/docs/plugins/organization, better-auth.com/docs/plugins/2fa, github.com/lucia-auth/lucia, orm.drizzle.team/docs/rls, prisma.io/docs (upgrading to Prisma 7), ably.com/pricing, pusher.com/channels/pricing, centrifugal.dev/docs/pro/overview, github.com/middleapi/orpc, raw.githubusercontent.com/nodejs/Release/main/schedule.json, api.github.com (stars and licences), api.npmjs.org (downloads), registry.npmjs.org and pypi.org (versions).
