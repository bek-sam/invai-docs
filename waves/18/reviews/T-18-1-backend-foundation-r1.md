# Review of T-18-1 (round 1)

- Reviewer: backend-foundation on Sonnet 5
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show --stat 92b9260` | 11 files, all inside T-18-1's owned paths (`contract/market.ts`, `schemas/market.ts`, `contract.ts`, `index.ts`, `schemas/ai.ts`, `roles.ts`+test, `market.test.ts`, `compat.ts`, `package.json`, `CHANGELOG.md`) |
| `git -C invai-docs show --stat e13cdda` | 2 files: `decisions/0015-global-market-cache.md` (new) + one-line `decisions/README.md` row, both owned |
| `invai-contracts`: `pnpm typecheck` | clean |
| `invai-contracts`: `pnpm lint` | `Checked 52 files in 45ms. No fixes applied.` |
| `invai-contracts`: `pnpm test` | `Test Files 6 passed (6)`, `Tests 52 passed (52)` |
| `invai-backend` worktree at `7ed3b4f` (symlinked `node_modules`, real link resolves to `../../../invai-contracts` = current `invai-contracts` HEAD `92b9260`, 0.6.0), `node_modules/.bin/tsc --noEmit` | clean, no output |
| `invai-backend` (current HEAD `4a76268`, past T-18-2/3/4) `src/api/router.ts`, `src/db/rls-coverage.test.ts` inspection | `market: marketRouter` registered; `PUBLIC_READ_TABLES` and the app-role-cannot-write set both already include `market_series_cache`, matching ADR 0015 §3/§4 exactly |
| `invai-backend/src/db/schema/market.ts` inspection | `marketSeriesCache`: columns `source, query, granularity, period, value, asOf, fetchedAt, licence, mock` + `id`/timestamps only — matches ADR 0015 Decision §2 verbatim; `uniqueIndex().on(source, query, granularity, period)`; `publicReadPolicy("market_series_cache")` + `.enableRLS()` in the same file that creates the table |
| `invai-backend/drizzle/meta/_journal.json` | 28 entries; only one new migration since wave 17 (`0027_market_signals`, T-18-3). No journal collision; T-18-1 generated none (contracts-only card, correct) |
| `invai-backend/src/db/schema/_shared.ts`, `src/db/schema/ai.ts` (`trademarkMarks`) | `publicReadPolicy` helper exists exactly as ADR cites; `trademark_marks` precedent matches (`publicReadPolicy` + `.enableRLS()`, no tenant column) |
| `invai-backend/src/api/orpc.ts:127` | `if (meta.permission !== "none" && !context.permissions.has(meta.permission)) throw forbidden(...)` — generic; a new `Permission` string flows through with zero foundation-code change |
| `invai-backend/src/lib/pagination.ts` | cursor helper shape (`{cursor?, limit} -> {items, nextCursor}`) matches `paginated()`/`Page` used by `market.recommendations.list` |

## Acceptance criteria (my lens only: foundation-pattern fit)
| # | Met? | Evidence |
|---|---|---|
| Backend can implement cleanly with existing router/permission-guard, pagination, withTenant/withSystem, RLS helper patterns | yes | `proc("market.niches.manage")`/`proc("finance.read")` need no `orpc.ts` change (guard is generic on `Permission`); `Page.extend({...}).output(paginated(MarketRecommendation))` matches `src/lib/pagination.ts`'s existing cursor contract, and T-18-3's router already implements it against this exact contract |
| ADR 0015 table shape is consistent with `trademark_marks`/RLS-coverage precedent | yes | same helper (`publicReadPolicy`), same enable pattern, same "app role select-only" enforcement list; T-18-3's actual `marketSeriesCache` table (already committed) matches the ADR's column list and unique index exactly, with no drift |
| Migration story holds: no journal conflicts, T-18-3 the only migration for the wave | yes | journal has exactly one new entry (`0027_market_signals`), authored by T-18-3; T-18-1 (contracts-only) added none |
| New permission `market.niches.manage` needs no foundation change | yes | `PERMISSIONS` array + `ROLE_PERMISSIONS` entries are contract-owned; `orpc.ts`'s guard reads `context.permissions.has(meta.permission)` generically, so a brand-new permission string requires zero backend-foundation edits |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`) — confirmed both repos above
- [x] Nothing outside scope — no backend/web implementation touched, digest procedures correctly deferred to wave 19
- [x] Tests exercise the behavior, none weakened — new `market.test.ts`/`roles.test.ts` additions only; no `.skip`, no loosened assertion found in the diff
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — ADR correctly scopes the one non-`company_id` table with public-read RLS + `withSystem`-only writes; `vote` documented idempotent (latest wins, stored result returned); money/ratio/date conventions asserted by contract tests
- [x] Decisions recorded where needed — ADR 0015 written, `accepted` pending security-reviewer's confirming co-review as the card specifies (correct interim status, not a defect)

## Optional notes (not blocking)
- ADR 0015 §"Consequences" correctly assigns the `market.ts` schema/migration enforcement to backend-engineer with backend-foundation co-review — noted for my own co-review queue when T-18-3's card comes up; already spot-checked here for consistency and found no drift from the ADR.
- The README namespace-table gap (T-18-1's own "Known gaps") and the wave.md ADR link are tech-lead/docs housekeeping, not blocking for this card.
