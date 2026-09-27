# InvAI handoff: resume here

Last updated: 2026-09-26, when the tech-lead session paused. A new session resumes from this file.

## How to resume
1. Start Claude Code **from `~/invai`** (`cd ~/invai && claude`). That loads the 20 team roles (`.claude/agents`), 72 playbooks (`.claude/skills`) and the guard hook.
2. Say: **"Resume the InvAI roadmap from invai-docs/HANDOFF.md"**.
3. The session then:
   - reads this file and `team/agent-brief.md`;
   - checks each repo's `git log origin/main..HEAD` and `git status` against "State at pause";
   - continues from "Next steps", in order.

## Operating rules (don't skip)
- **Process:** `team/operating-system.md` (waves of ≤5 cards, independent review, integration gate, then push). The token budget is decision 0011 (`team/agent-brief.md`).
- **Every agent prompt says "Don't push; only the tech lead pushes after the gate."** A builder once pushed 44 ungated commits because a prompt left this out.
- **Tech lead:**
  - plans, grants and pushes;
  - writes every grant into the wave file **when giving it**;
  - pushes per SHA (`git push origin <sha>:main`) when waves overlap.
- **Agents:**
  - Sonnet for most builders and reviewers; Opus for payments, security, concurrency and data-integrity cards;
  - at most 4 agents at once;
  - commands under about 2 minutes, polled inside the turn;
  - never run `git stash` or `pnpm install`, re-link shared `node_modules`, or `db:reset` the shared DB (only gates may).
- **Environment:**
  - Schema changes ship **with their migration in the same commit**.
  - Imaging needs `IMAGING_SHARED_SECRET` (see both `.env.example` files).
  - The E2E worker needs `MOCK_CARRIER_TRANSIT_HOURS=0.001`.
  - Seed with imaging up and the worker stopped.
- **Usage limits:** if a limit hits, wait for the reset, then resume agents with SendMessage (the owner asked for automatic resume).
- **The owner prefers** fast, max-efficiency work and short status updates.

## Roadmap status (see `waves/roadmap.md`)
| Wave | Theme | Status |
|---|---|---|
| 1–5 | Safety, money and accounts, integrations, floor, office orders and settings | Done and pushed |
| 6 | Inventory, production, profit, AI listings UI, demo safety | Done and pushed |
| 7 | CSV tracking export, fees and refunds, label fee, orders hardening, a11y | Done and pushed |
| 8 | AI and marketplace compliance (+ T-8-6 NUL-safe inputs) | Done and pushed |
| 9 | Imaging for print shops | Done and pushed; gate findings fixed |
| 10–11 | AWS deploy and monitoring | **Deferred by the owner** until go-live |
| 12 | Reliability (retries/DLQ, health/shutdown, rate limits, export/deletion, CSP) | Done and pushed |
| 13 | Contracts and quality | 13-1 and 13-5 done; 13-3 mostly done (review pending); 13-4 barely started; **13-2 not started** |
| 14 | Evidence and docs (B-71, B-10, B-29, B-98, B-106, B-47) | Not planned yet |
| 15 | P2 sweep (see `waves/backlog.md`) | Not planned yet |
| 16 | Team harness: edit checks, verification gate, guard, agent memory | Done 2026-09-27; hooks installed live (`sync.sh restore`) |
| 17 | Assistant as business analyst (B-113) | Done and pushed 2026-09-27 (contracts `8713a63`, backend `97780c1`, web `11ffbfe`) |

## State at pause
All code repos are **pushed and clean** as of 2026-09-26.

| Repo | Pushed HEAD |
|---|---|
| contracts | `a2ef5d7` (CONTRACT_VERSION 0.4.0) |
| backend | `2add4d6` |
| web | `c0cb568` |
| floor | `b9ef73a` |
| ui | `c29c60a` |
| imaging | `5b2c7bb` |
| infra | `148df7d` (unchanged) |

**Final gate (light, at HEAD):**
- Passed: tsc, biome and vitest in contracts, web, floor, ui and backend (97 files); imaging pytest 107/107, ruff clean.
- **Not re-run since the wave 6–9 gate:** the API golden path, browser E2E and floor E2E. Re-run them first thing (fresh reset, migrate and seed). Commands are in `waves/9/gate.md`.

**Closed at pause:**
- Wave 9 gate findings.
  - A (the header QR): imaging `ae3e3c1` and `5b2c7bb`, backend `8a23f57`. The header QR now carries the sheet id.
  - B (PDF QA): imaging `247fae1`.
- Wave 12 is fully approved (T-12-5 r2 approved, docs `8f4b79e`).
- Two test fixes:
  - a flaky auth rate-limit test, which now uses per-run IPs (`2add4d6`);
  - formatting in the T-13-3 and T-13-4 test files.

**Unfinished:**
- **T-13-3:**
  - Done and committed, with a light tech-lead review: contracts `a2ef5d7`, backend `889c5aa`, web `819cd1f`. `scanBatch` and `listing.synced` are removed and `Org.demoOwned` is added.
  - Still needs its **independent review**.
  - Left: unify the `attributes` shape. It needs a migration for the `listing_drafts.content` default first. See `waves/13/reports/T-13-3-report.md`.
- **T-13-4:**
  - Only backend `4671a1a` (Shopify race tests) is done.
  - Not started: role specs, Spanish smoke, uncovered flows, property tests (a `fast-check` install needs approval), axe, and CI. See `waves/13/reports/T-13-4-report.md`.
- **T-13-2:** not started.

## Next steps (in order)
1. Re-run the full E2E gate at HEAD, then get the T-13-3 independent review. Finish the rest of T-13-3 and T-13-4 (see their reports), then do T-13-2.
2. **T-13-2 contract CI and versioning.** The card is `waves/13/T-13-2.md`; it's sequenced after T-13-3. Then the wave 13 gate and push.
3. **Plan wave 14** (evidence and docs):
   - B-71 side-effect tests;
   - B-10 and B-29 policies and docs (incident plan, access policy, vendor list, DPA and sub-processors; fix the Amazon scan-interval doc);
   - B-98 help center en/es plus terms and privacy links;
   - B-106 runbook refresh (seed timing, `ALLOW_MOCKS`, `SMTP_URL`/`MAIL_FROM`, `STRIPE_WEBHOOK_SECRET`, `ETSY_WEBHOOK_SECRET`, `EASYPOST_WEBHOOK_SECRET`, `IMAGING_SHARED_SECRET`, `MIN_FLOOR_CONTRACT_VERSION`, `INTERNAL_ADMIN_TOKEN`, the demo notes, Better Auth secret rotation);
   - B-47 path-guard hook.
4. **Plan wave 15** (P2 sweep): B-25, B-27, B-30, B-31, B-32, B-34, B-37, B-38, B-41, B-100, B-102, B-103, B-107, B-110, B-112, plus the "Follow-ups" sections in every `waves/*/wave.md`. Rank them first (`prioritize-backlog`).
5. Waves 10 and 11 (deploy) only when the owner provides AWS, a domain and keys (see the roadmap's owner track).

## Follow-ups worth prioritizing (from reviews)
- **Security (P1):**
  - A soft-deleted company can still sign in during its 30-day window (T-12-4).
  - Deleting a company doesn't cancel its Stripe subscription.
- **Floor:** the backend doesn't close SSE streams on station revoke (T-5-4).
- **Seed:** buyer-photo upload endpoint and UI don't exist yet (T-9-4). Seed efficiency is 83% (accepted; T-13-5).
- **Migrate:** add `SET LOCAL statement_timeout = 0` plus a `lock_timeout` for the advisory lock (T-12-2).
- **Web:** `printsInHouse` has no settings toggle; `shipsSaturday` has no UI.
- **Contracts:** the TikTok `transactionPct` in `CHANNEL_RULES` should be 6 (T-7-2).

## Owner decisions pending (`owner-inbox.md`)
- **OI-1:** label fee and plan prices. The code uses $0.10/label for now.
- **OI-2:** Shopify App Store vs unlisted distribution.
- **OI-3:** build the direct Etsy API adapter now in mock mode (B-108).
- **OI-4:** download the Etsy, TikTok and Walmart tracking-upload templates into `research/templates/`.
- **Deploy prerequisites (waves 10–11):** AWS account(s), region, domain and Route53, GitHub OIDC role, and real keys.

## Where things are
- **Workspace:** `~/invai`. It moved from `~/Desktop/projects/invai` on 2026-09-26.
- **Evidence:**
  - Audit: `build/audit-2026-09-24.md`.
  - Backlog: `waves/backlog.md` (B-01 to B-112).
  - Decisions: `decisions/0001–0012`.
  - Lessons: `team/lessons.md`.
- **Each wave:** `waves/<n>/wave.md` (cards, grants, follow-ups), plus `reports/`, `reviews/` and `gate.md`.
