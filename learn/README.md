# InvAI course — a mentor's guide to this codebase

Written and kept up to date by the `mentor` role. Plain English, cited to real files
(`file:line`), for the owner learning how InvAI actually works and why. Read-only on
code — this folder and the Notion mirror below are the only things the mentor writes.

**How to read this course:** go in order the first time (01 → 12); each module assumes
the ones before it. Once you've done 01–09, the `diary/` entries (one per wave) make
sense as "here's what changed and why." Every lesson follows the same 9-part format —
in one sentence, why it exists, how it works, in our code, what it uses, try it
yourself, common mistakes, check yourself, words to know — so you always know where to
look for the thing you need.

New terms are defined the first time they're used and added to `glossary.md`. If a
lesson uses a term you don't recognize, check there first.

## Course map and progress

| # | Module | Status | Lessons |
|---|---|---|---|
| 01 | Big picture — the business, the user journey, what InvAI solves | **Done** | [1. The DTF business](01-big-picture/01-the-dtf-business.md), [2. The user journey](01-big-picture/02-the-user-journey.md) |
| 02 | Architecture — the 8 repos, how a request travels, with a diagram | **Done** | [1. The 8 repos](02-architecture/01-eight-repos.md), [2. The request journey](02-architecture/02-request-journey.md) |
| 03 | The stack — each tool and why, over the alternatives | **Done** | [1. TypeScript, Zod, oRPC and Biome](03-stack/01-typescript-zod-and-the-contract.md), [2. drizzle + Postgres RLS, and Valkey/BullMQ](03-stack/02-database-and-jobs.md), [3. S3/MinIO and Better Auth](03-stack/03-storage-and-auth.md), [4. React, TanStack, Vite, Vitest and Playwright](03-stack/04-frontend-stack.md), [5. Python/pyvips, Docker/OrbStack, SST, GitHub Actions](03-stack/05-imaging-and-infrastructure.md) |
| 04 | Data and tenancy — schema, migrations, `company_id` + RLS, `withTenant`, money in cents | **Done** | [1. Schema and migrations](04-data-and-tenancy/01-schema-and-migrations.md), [2. Tenancy, `company_id` and RLS, in full](04-data-and-tenancy/02-tenancy-company-id-and-rls.md), [3. Money, units, and one item = one unit](04-data-and-tenancy/03-money-units-and-one-item-one-unit.md) |
| 05 | Core flows — order import → SKU map → gang sheet → floor scans → label → profit | **Done** | [1. Order import and the SKU map](05-core-flows/01-order-import-and-sku-map.md), [2. Gang sheet and the floor](05-core-flows/02-gang-sheet-and-floor.md), [3. Label and profit](05-core-flows/03-label-and-profit.md) |
| 06 | Reliability — idempotency, the outbox, jobs and retries, rate limits, mocks vs real | **Done** | [1. Idempotency and the outbox](06-reliability/01-idempotency-and-the-outbox.md), [2. Jobs, retries and rate limits](06-reliability/02-jobs-retries-and-rate-limits.md), [3. Mocks vs. real providers](06-reliability/03-mocks-vs-real-providers.md) |
| 07 | AI features — the gateway, prompts, validators, evals, cost, trademark check, assistant | **Done** | [1. The gateway and providers](07-ai-features/01-the-gateway-and-providers.md), [2. Prompts, validators and cost](07-ai-features/02-prompts-validators-and-cost.md), [3. The trademark check and the assistant](07-ai-features/03-trademark-check-and-the-assistant.md) |
| 08 | Quality — tests in layers, E2E, the gate, CI, reviews, catching weakened tests | **Done** | [1. Tests in layers](08-quality/01-tests-in-layers.md), [2. E2E, the gate and CI](08-quality/02-e2e-the-gate-and-ci.md), [3. Reviews and weakened tests](08-quality/03-reviews-and-weakened-tests.md) |
| 09 | Security — auth, PII, webhooks, the findings log, how fixes are proved | Not started | — |
| 10 | The AI team — roles, waves, reviews, hooks, token budget, decisions, lessons | Not started | — |
| 11 | Deploy and ops — environments, SST, costs, monitoring, what's still paused | Not started | — |
| 12 | Product and business — scope, fences, pricing, research, growth ideas, "don't build" | Not started | — |
| — | `diary/` — one short lesson per wave (what, why, what went wrong, what to look at) | Not started | — |

**Suggested next lesson:** Module 09, "security" — modules 06–08 covered reliability
(idempotency, jobs, mocks), AI features (the gateway, decision 0021's OpenAI provider,
evals) and quality (test layers, the gate, CI, independent review); module 09 goes
deeper on auth, PII handling and webhook verification that this run's lessons touched
on (the gateway's PII scrub, webhook dedupe) but didn't cover as their own topic.

## Where things are
- Modules live one folder per module, one file per lesson, named
  `0N-<lesson-slug>.md`.
- `glossary.md` — every term, once, in plain words, with where it appears in InvAI.
  Add a new term the first time a lesson uses it.
- `diary/wave-<n>.md` — a short lesson per wave once waves resume being summarized here.

## Notion mirror
The markdown in this folder is the source of truth; Notion is a read-along mirror kept
in the same order, one child page per module and per lesson, under one parent page
called **"InvAI Course."** Never published there: secrets, passwords, PINs, tokens, seed
logins or customer data — the markdown above never has any of these either.

| Page | Notion URL |
|---|---|
| InvAI Course (parent) | https://app.notion.com/p/3ecb5391545a813581dae9589645c7e1 |
| README — Course Map | https://app.notion.com/p/3ecb5391545a812bad40ccdf0906c826 |
| Glossary | https://app.notion.com/p/3ecb5391545a8143b197caea2d328d22 |
| 1.1 The DTF Business | https://app.notion.com/p/3ecb5391545a81d884ebe2a4e5b45532 |
| 1.2 The User Journey | https://app.notion.com/p/3ecb5391545a816fb51cd02a3d8fbd65 |
| 2.1 The 8 Repos | https://app.notion.com/p/3ecb5391545a81ddb83df0026ec5cf4d |
| 2.2 The Request Journey | https://app.notion.com/p/3ecb5391545a81eeb027d821c9b866cb |
| 3.1 TypeScript, Zod, oRPC and Biome | https://app.notion.com/p/3edb5391545a819e86a4d6252f70dcee |
| 3.2 Drizzle, Postgres RLS and Valkey/BullMQ | https://app.notion.com/p/3edb5391545a81c8ab26f833300302b0 |
| 3.3 S3/MinIO for Files, Better Auth for Sign-in | https://app.notion.com/p/3edb5391545a816ba6e1c0e41b733dec |
| 3.4 React, TanStack, Vite, Vitest and Playwright | https://app.notion.com/p/3edb5391545a8134b342f64019f7033d |
| 3.5 Python/pyvips, Docker/OrbStack, SST, GitHub Actions | https://app.notion.com/p/3edb5391545a81b2839fdaca0464c74d |
| 4.1 Schema and Migrations | https://app.notion.com/p/3edb5391545a8171a224c3a4074e40c4 |
| 4.2 Tenancy, Company ID and RLS, in Full | https://app.notion.com/p/3edb5391545a819ba3d2ec1a02dabd84 |
| 4.3 Money, Units, and One Item = One Unit | https://app.notion.com/p/3edb5391545a8141a1efe93228f58919 |
| 5.1 Order Import and the SKU Map | https://app.notion.com/p/3edb5391545a81ba9af3ffdeec8f177a |
| 5.2 Gang Sheet and the Floor | https://app.notion.com/p/3edb5391545a812bb385dd6dc3267ed7 |
| 5.3 Label and Profit | https://app.notion.com/p/3edb5391545a813c88cad55ad4168981 |
| 6.1 Idempotency and the Outbox | https://app.notion.com/p/3edb5391545a81bca2d8c11b94705d7c |
| 6.2 Jobs, Retries and Rate Limits | https://app.notion.com/p/3edb5391545a813c8043f4859e63577d |
| 6.3 Mocks vs. Real Providers | https://app.notion.com/p/3edb5391545a81bebe1cc7f0a2f9b0c3 |
| 7.1 The Gateway and Providers | https://app.notion.com/p/3edb5391545a816e8d86d3a6644d5d1e |
| 7.2 Prompts, Validators and Cost | https://app.notion.com/p/3edb5391545a81a8af53e349953c758c |
| 7.3 The Trademark Check and the Assistant | https://app.notion.com/p/3edb5391545a81f0a014df002a5237fb |
| 8.1 Tests in Layers | https://app.notion.com/p/3edb5391545a8194b371d8053bf58140 |
| 8.2 E2E, the Gate and CI | https://app.notion.com/p/3edb5391545a811d829ae62eee2b7379 |
| 8.3 Reviews and Weakened Tests | https://app.notion.com/p/3edb5391545a81b7a881dba2b1eaa039 |

Created as a private draft page (no destination was named); move it under a shared
space if you'd like it visible to others. Update a page's markdown here first, then
re-run the mentor to push the matching Notion page — never edit Notion directly as the
source of truth.
