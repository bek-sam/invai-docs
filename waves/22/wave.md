# Wave 22: P2 sweep, part 1: contracts and backend correctness

- Dates: planned 2026-09-28; starts after the wave 20 gate (wave 21 docs cards can overlap)
- Goal (user outcome): the remaining P2 correctness gaps close on the backend: imports never double-create under concurrent runs, vendor sheet emails go out once and only after the commit (with a resend), USPS end-of-day SCAN forms and address checks work in mock mode, tenant foreign keys can't cross shops, the Amazon CSV brings shipping credits into profit, and floor/production get QC fail reasons, a transfer-age warning, a maintenance block and bin locations in the pick list. Web and floor screens for these come in wave 23.
- Sources (backlog): B-25, B-30, B-32, B-35 rest, B-37 (indexes), B-99 rest, B-102, B-139, B-162 (contract part), B-163, B-164, B-166, B-167, B-183 (Amazon $0 shipping; always in scope: bug). B-36 (SanMar) stays out of scope (`scope.md` "MVP: out"). B-49 folds into analytics A1 (B-182).
- Rules: `team/agent-brief.md`; every prompt: "Don't push", absolute memory path, record PIDs.
- Plan reviewed by: product-manager (2026-09-28, approve with changes: T-22-1 scope ref fixed), architect (2026-09-28, approve with changes A1–A6, applied to the cards).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-22-1 Contract additions for the P2 sweep | architect | fable | reviewer (opus) + backend-foundation, web-engineer, floor-engineer (consumers) | contract | planned |
| T-22-2 Tenant FKs, migrate lock, queue stall settings, trigram indexes (B-30, B-163, B-166, B-37 indexes) | backend-foundation | fable | reviewer (opus) + security-reviewer (tenancy) | tenancy, migration | planned |
| T-22-3 USPS SCAN form, address check, rate TTL; Amazon CSV shipping; mailer subject log (B-25, B-183, B-139) | integrations-engineer | opus | reviewer (sonnet) + security-reviewer (pii), backend-engineer (shipping, consumer) | pii, payments | planned |
| T-22-4 Production and inventory: QC fail reasons, transfer age, maintenance block, bin locations in pick list (B-35, B-32) | backend-engineer (production, inventory) | opus | reviewer (sonnet) + backend-foundation (migration), qa-engineer (floor golden path) | floor-correctness, migration | planned |
| T-22-5 Orders and vendors: import races, channel line edits, vendor email after commit + resend, TikTok fee, listing attributes (B-99, B-102, B-164, B-167) | backend-engineer (orders, vendors, finance, ai-listing attributes by grant) | opus | reviewer (sonnet) + architect (cross-module), backend-foundation (migration), ai-engineer (attributes hunk) | data-integrity, migration | planned |

## Order and ownership
1. T-22-1 first (stubs day 1: every new procedure returns `NOT_IMPLEMENTED` in the backend router until its card lands, committed by the card owner on day 1). T-22-2 starts in parallel (no contract dependency).
2. T-22-3, T-22-4, T-22-5 after T-22-1 lands; at most 3 builders at once.
3. **Schema-file order (architect A1):** T-22-4 and T-22-5 start editing `src/db/schema/{production,inventory,orders,vendors}.ts` only after T-22-2's schema commit lands (not just its migration). Migration order: T-22-2 first (it touches many schema files through a composite-FK migration), then T-22-4, then T-22-5; the later card regenerates on a journal collision.

| Card | Owns (exclusive) |
|---|---|
| T-22-1 | `invai-contracts/src/**` (additive only; version bump + CHANGELOG) |
| T-22-2 | `invai-backend/src/db/**` (schema files for FK constraints only, plus its migration), `src/db/migrate.ts`, `src/lib/queues.ts`, `src/worker/**` (worker options only) |
| T-22-3 | `invai-backend/src/integrations/{carriers,channels/csv}/**`, `src/integrations/vendors/mailer.ts` (subject log line only), shipping module router/service hunks for the SCAN form by grant |
| T-22-4 | `invai-backend/src/modules/{production,inventory}/**`, `src/db/schema/{production,inventory}.ts` columns + migration |
| T-22-5 | `invai-backend/src/modules/{orders,vendors,finance}/**`, `src/db/schema/{orders,vendors}.ts` columns + migration; grant: `src/modules/ai/service.ts` attributes mapping only |

## Integration gate
- [ ] Fresh reset, migrate, seed; `run-golden-path`
- [ ] RLS coverage and tenant-isolation tests green; a cross-tenant FK insert is refused
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Retro
- 2026-09-28 Grant T-22-1: backend router stub lines in `src/modules/{shipping,production,inventory,vendors,tenancy}/router.ts` (NOT_IMPLEMENTED stubs only; backend-foundation co-reviews). T-22-1 started.
- 2026-09-29 T-22-1 built: contracts `f519085` (0.8.0), gated commits `83013af` (REPRINT_REASONS under_cure/cracking) and `81afad4` (TikTok 6%) reverted on main by `78d2469`/`184149c` to keep consumers green; T-22-4 re-applies the first (`git cherry-pick 83013af`, patch in `waves/22/patches/`) with its backend mirror, T-22-5 the second with `fees.test.ts:90` and a backfill of cost-settings rows at 8. Backend stubs `2cda6e2`. ADR 0017 (listing attributes stay a map). Floor consumer review approve.
- 2026-09-29 Grants from T-22-1's findings: T-22-2 (backend-foundation, its own module) implements the `src/modules/tenancy/service.ts` `updateOrg` hunks for `shipsSaturday` and `transferAgeWarnDays` (added to its card); T-22-4 gets the contracts cherry-pick of `83013af`; T-22-5 gets the cherry-pick of `81afad4`. Web `keysForEvent` case for `station.maintenance_changed` goes to wave 23 T-23-1.
- 2026-09-29 T-22-2 schema commit `3b50fb8` (composite tenant FKs) landed; T-22-4/T-22-5 may edit schema files. T-22-3 commits `faff2b9`, `d5a7312`, `3bd775d`, `044c3af` (scan_forms, address_verifications tables), `acd1dbf`. PM's B-131 spec step `9c7e33c` (for wave 23 T-23-4).
- 2026-09-29 T-22-3 built (+ `0720eaa`; migration `0032_shipping_scan_forms`). Tech lead decisions: the extra `address_verifications` table in the same migration is accepted after the fact (grant widened; backend-foundation co-reviews the migration); the change to backend-engineer's `label-safety.test.ts` (old "expired quote refused" behaviour) goes to the backend-engineer (shipping) co-review. B-183 closed as "no parser bug": Amazon's Unshipped report has no prices; the Order Report credit is now tested. New: re-importing an Unshipped file after an Order Report overwrites real totals with 0 (`orders/import.ts:396-406`) → added to T-22-5 as AC7 (B-197); the seed's Amazon shipping 0 → B-198.
- 2026-09-29 (fresh tech lead, resume from disk) State: T-22-1 built, reviews reviewer/backend-foundation/floor approve, web-engineer consumer review missing. T-22-2 schema+migrations `3b50fb8` committed; second half (migrate.ts, queues, worker, tenancy settings, README, tests) uncommitted in the tree, report has no full-suite result, no reviews yet. T-22-3 built (6 commits, report with final suite green), no reviews on disk (earlier reviewers stalled before writing). T-22-4, T-22-5 not started. Decision: T-22-2 AC5 (tenant-leading trigram indexes) is descoped by evidence (RLS blocks non-leakproof index conditions); search strategy goes to the architect as B-199 in wave 23. Models per decision 0018: builders of migration/money cards opus, primary reviewers opus, consumer co-reviewers sonnet. Leftover dir `invai-backend-T-22-1-rev` (empty node_modules link) could not be removed by the tech lead (permission); owner to delete.
- 2026-09-29 Wave 24 note (runs in parallel, not this tech lead's wave): T-24-1 reviewer r1 approve (docs `5f2ed51`); still needs security-reviewer and web-engineer (CSP hunk) co-reviews before infra `3dbb899` and web `c1d53a8` can be pushed. Docs `5f2ed51` is pushed with wave 22's docs.
- 2026-09-29 T-22-3 reviews: reviewer r1 approve (`8897b85`; optional: 0032 lacks lock_timeout, one refused label rejects the whole SCAN form, raw carrier error text in a log line); security-reviewer r1 changes-required (S-38 Medium: unkeyed subject hash in mailer) -> integrations-engineer r2 fix (sonnet) in progress; backend-engineer shipping co-review in progress; backend-foundation migration co-review queued.
- 2026-09-29 T-22-2 second half committed `6a8856c` (full suite 1157 pass, 2 order-dependent flakes outside its paths: `mailer-subject.test.ts` S-38 test -> integrations-engineer after security r2; `market/service.test.ts` -> B-201). AC5 descoped -> B-199. T-22-3: backend-engineer co-review approve; S-38 fix `2466954`, security r2 running. Started: T-22-2 reviewer (opus), T-22-4 builder (opus). Queued: T-22-3 backend-foundation migration co-review (sonnet), T-22-2 security co-review, T-22-1 web-engineer consumer review, T-22-5 builder.
- 2026-09-29 T-22-3 security r2 approve (`3e0303d`, S-38 fixed in `2466954`). The mailer-subject 'flake' in T-22-2's suite matched the old-code value exactly: the suite ran while the fix was half-written in the shared tree, not a flake; the gate's full suite confirms. B-202 (toHash unkeyed, Low).
- 2026-09-29 T-22-2 reviewer r1 approve (`c788fe4`; notes: fk-coverage doesn't check the SET NULL column list, stall test doesn't cover worker/index.ts wiring). Security tenancy co-review running.
- 2026-09-29 T-22-2 relaunch confirmed full suite at `2466954`: 1159 passed, 0 failed. An earlier 'stalled' T-22-2 instance was in fact still live (it made `6a8856c`); lesson logged.
- 2026-09-29 T-22-3 all reviews approve: reviewer r1, security r2, backend-engineer r1, backend-foundation r1 (`793a8b6`). T-22-3 done pending gate. T-22-5 builder (opus) started.
- 2026-09-29 T-22-2 security r1 approve (`b6a1671`): S-26 closed for FKs at `3b50fb8`; new S-39 Low -> B-203. T-22-2 done pending gate.
- 2026-09-29 T-22-1 web-engineer consumer review approve (`4d5b0ec`). T-22-1 fully approved. Note for wave 24: with the unpushed web commit `c1d53a8` (T-24-1 CSP), plain `pnpm build` in invai-web fails unless VITE_API_URL is set: T-24-1's co-reviews must judge this.
- 2026-09-29 T-22-4 built: contracts `0f2f413` (cherry-pick 83013af), backend `08d1eba` (migration 0033), `1f39aaa`. Full suite 1166 pass, 1 fail `finance/fees.test.ts:91` from T-22-5's in-progress TikTok-fee change. Floor E2E not run: QA covers it at the gate and writes the T-22-4 qa-engineer co-review there. Seed gap -> B-204. Reviews started: reviewer (opus), backend-foundation (sonnet).
- 2026-09-29 Root cause of recurring backend 'flakes': tests use Redis DB 0 (B-205, backend-foundation, first card of wave 23; too late for wave 22's 5-card cap). Gate runs the backend suite with REDIS_URL=redis://localhost:6379/14 and no dev worker. Stale `pnpm dev:all` stack from 2026-09-28 10:08 (no current owner) stopped by the tech lead. Still running, owner unknown: API :3142 (tsx watch since 2026-09-26) and web vite :5183 (since 2026-09-28): left alone, listed for the owner. Suite failures to route: `finance/fees.test.ts` (T-22-5, in progress), `production/maintenance.test.ts` tenant-isolation scan insert (T-22-4, reviewer re-runs it).
- 2026-09-29 T-22-4 backend-foundation migration co-review approve.
- 2026-09-29 T-22-4 reviewer r1 changes-required (`00b40b9`): offline scan made during maintenance and replayed after it ended still presses (`floor.ts:473` ignores scannedAt). Round-2 fix (opus) running. Reviewer confirmed `fees.test.ts` fails on committed code (T-22-5's cherry-pick, not T-22-4).
- 2026-09-29 T-22-4 reviewer r2 approve (`2a4d2f4`, fix `03d780e`). Remaining for T-22-4: qa-engineer floor co-review at the gate.
- 2026-09-29 T-22-5 built: contracts `9e8ea0c`; backend `f6725b8` `159c7da` (0034 vendor_sheet_deliveries, 0035 TikTok 8->6), `a6fb254` `fb8aa0a` `19c16a5` `147a2bf` `b90157c`; full suite 1186 pass. Author decision to review: interrupted vendor send is never auto-retried (delivery 'unknown', office resends); a kill before send gave 0 emails. Reviews: reviewer (opus), backend-foundation (sonnet), architect (sonnet); ai-engineer (sonnet) after.
- 2026-09-29 T-22-5 architect r1 approve (`14560f8`), backend-foundation r1 approve.
- 2026-09-29 T-22-5 ai-engineer r1 approve. Waiting on T-22-5 reviewer r1.
- 2026-09-29 T-22-5 reviewer r1 changes-required (`97caf13`): a vendor email could be lost silently (worker death after claim -> 'unknown', 0 emails, no alert). Round-2 fix (opus) running: claim just before SMTP, raiseAlert on unknown/failed, advisory-lock test.
- 2026-09-29 T-22-5 round 2 `04e72a0` (claim before SMTP, office alert on unknown/failed, lock test; full suite 1188 pass). Interim alert kind tracking_push_failed -> B-206 (wave 23 T-23-1). Reviewer r2 running.
- 2026-09-29 T-22-5 reviewer r2 approve (`2a6337c`). All cards approved except T-22-4's qa-engineer floor co-review (at the gate). Gate started (qa-engineer, sonnet).
