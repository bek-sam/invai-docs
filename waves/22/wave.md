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
