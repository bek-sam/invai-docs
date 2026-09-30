Verdict: approve
# Review of T-A2 (round 1): reviewer on opus; author architect on fable. Commits: contracts `f466088`, backend `9228343` (backend HEAD `95e9d69` is T-A3's migration, not reviewed here).

## Evidence I re-ran
| Command | Result |
|---|---|
| contracts `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome 59 files, no fixes; `Test Files 9 passed, Tests 105 passed` |
| backend `pnpm typecheck && pnpm lint` | tsc clean; biome 425 files, no fixes |
| web / floor `pnpm typecheck` | both clean (consumers via symlinked `@invai/contracts`) |
| backend `REDIS_URL=…/11 vitest run src/api/authz.test.ts` | 7/7 passed: its `listProcedures(contract)` walk includes all 11 `analytics.*` stubs as no-permission → FORBIDDEN (scratch Redis DB 11 was empty before; flushed after) |
| mutation in a scratch copy of `f466088` (`export` → `orders.read`, `destZone` min 0, leakage `channel` → `z.string()`, extra tool name) | 4 targeted tests fail as they should (AC-E5 permission, channel enum, destZone 1..9, full tool enum) |
| `scan-test-weakening.sh` contracts / backend | 2 removed assertions (below); backend: no hits |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | typecheck green in contracts, backend (with stub router), web, floor |
| 2 | yes | all 11 `proc("finance.read")`, default user auth (`contract/analytics.ts`); test + authz walk; mutation caught |
| 3 | yes | `schemas/shipping.ts:55` int 1..9 nullish; test rejects 0/10/2.5/"3", no address-like key, absent from every input |
| 4 | yes | `schemas/ai.ts:170-177` five names at the end; test pins all 19 in order; web/floor/backend typecheck green (no exhaustive switch) |
| 5 | yes, with accepted deviation | range reads share `finance.profit`'s `Period` object (required); `days` 7..365 default 90; `asOf` optional DateOnly; new fields nullish. `channel?` is on 7 sales-based reads, not on inventoryHealth/supplierTrends/breakEven: I accept this. The "Interfaces promised" list itself gives `channel?` only where sales are the base, and a filter the handler must ignore would be a false promise. Tested both ways. Tech lead: note it on the card. |

## Blocking findings
none

## Judgement on the two relaxed tests (not weakening)
- `src/market.test.ts:313` "last four" → "contiguous, in order, after wave 17": an additive append necessarily breaks "last four". The full, ordered 19-name pin in `src/analytics.test.ts` is strictly stronger, so the "nothing else changed" check still holds.
- `src/p2-sweep.test.ts:340` `toBe("0.8.0")` → `≥ 0.8.0`: `analytics.test.ts` pins `0.9.0` exactly and `FLOOR_COMPAT_BASELINE` stays pinned in both tests. Same strength, and a future bump now touches one file.

## Checks
- [x] Only owned paths changed: the card's contracts files, plus `src/compat.ts`/`CHANGELOG.md`, which are part of the version bump (a test ties `CONTRACT_VERSION` to package.json). Backend: stub `modules/analytics/router.ts` (14 lines, `stubRouter` only) + import and one line in `api/router.ts`, exactly the grant.
- [x] Nothing outside scope: no handlers and no Track D procedures.
- [x] Tests exercise the behavior, none weakened (see above); no skip/only/mocks/snapshots.
- [x] Tenancy/idempotency: read-only contract, no tables. Money: `Cents` (int) everywhere except the note below; percents are `*Pct`; shares are `Ratio`. No PII fields (orderNo is the shop's own number). No UI strings.
- [x] Decisions: none cross-cutting beyond the card; the namespace rule is in the README and a doc comment.

## Optional notes (not blocking)
1. `src/schemas/analytics.ts:556` `avgUnitCost: z.number()` is fractional cents (documented). This departs from the integer-cents rule. T-A5 should round it, or the tech lead should accept it as a derived average.
2. `src/schemas/finance.ts:114` `CostSettingsInput` now accepts `fixedMonthlyCents`, but `finance/service.ts:147` `updateCostSettings` drops it without a word until T-A3 persists it. T-A3 must land that before any web settings field ships.
3. The five new tool names have no web i18n labels yet (`assistant.tool.*`); T-A8/web must add en+es labels before the backend emits them.
