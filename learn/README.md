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
| 03 | The stack — each tool and why, over the alternatives | Not started | — |
| 04 | Data and tenancy — schema, migrations, `company_id` + RLS, `withTenant`, money in cents | Not started | — |
| 05 | Core flows — order import → SKU map → gang sheet → floor scans → label → profit | Not started | — |
| 06 | Reliability — idempotency, the outbox, jobs and retries, rate limits, mocks vs real | Not started | — |
| 07 | AI features — the gateway, prompts, validators, evals, cost, trademark check, assistant | Not started | — |
| 08 | Quality — tests in layers, E2E, the gate, CI, reviews, catching weakened tests | Not started | — |
| 09 | Security — auth, PII, webhooks, the findings log, how fixes are proved | Not started | — |
| 10 | The AI team — roles, waves, reviews, hooks, token budget, decisions, lessons | Not started | — |
| 11 | Deploy and ops — environments, SST, costs, monitoring, what's still paused | Not started | — |
| 12 | Product and business — scope, fences, pricing, research, growth ideas, "don't build" | Not started | — |
| — | `diary/` — one short lesson per wave (what, why, what went wrong, what to look at) | Not started | — |

**Suggested next lesson:** Module 03, "the stack" — now that you've seen *where* each
tool sits (module 02), module 03 covers *why* each one was picked over its alternatives
(TanStack Table v9, oRPC 1.15, Better Auth 1.7, drizzle 0.45, TypeScript 7, Zod 4,
pyvips, SST, and the rest).

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

Created as a private draft page (no destination was named); move it under a shared
space if you'd like it visible to others. Update a page's markdown here first, then
re-run the mentor to push the matching Notion page — never edit Notion directly as the
source of truth.
