# Review of T-4-1 (round 1): qa-engineer co-review

- Reviewer: qa-engineer co-review, run by the reviewer agent on Claude Opus 5.5
- Author: backend-engineer (production) on Claude Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| backend `vitest run` (full suite, `invai_test_r41`, Redis db 9) | 63 files, 447 passed |
| `vitest run src/modules/production src/modules/orders src/db src/api` | 17 files, 95 passed |
| `scan-test-weakening.sh invai-backend f036fbd` / `invai-contracts 11f53f5` | no hits / no hits |
| `pack.test.ts` at `bdffe6f` against the `d45e155` code | 2 failed, 10 passed: the hand-off and status tests catch the round-1 behavior |
| live API :3191 on `invai_r41_copy` | every row in `T-4-1-reviewer-r1.md`: refuse, then pack, then replay; `CONFLICT`s; hand to lead as packer (403) and admin (200); status unchanged; tote released; receiver/office/presser on sheets; `wrong_style`; the receiving scan |
| `GET /today` before and after packing a 3-unit order that had no per-unit pack scans | pack `itemsDoneToday` 0 → 3; pack-station `doneToday` 3 |
| then one per-unit pack scan of an already packed-out unit | `ok:true` "Packed"; Today pack 3 → **4**; the pack station's `doneToday` stays 3 (`count(distinct)`) |

## Test quality
- They cover: refuse with exact `missing[]` and no side effects (no stored row, no scans, status unchanged); a refused key isn't burned; replay with byte-equal result and one row, one scan per unit and one audit; same key on another order gives `CONFLICT` with nothing stored; the override matrix by role through the router (`packer`, `office`, `receiver` FORBIDDEN; `owner`, `admin` OK); held and fully cancelled orders; cross-tenant `NOT_FOUND`; the hand-off (tote released, no scans, status `in_production`, the marker survives a transition and clears once packed, then a normal pack goes through); bin double taps; the receiving queue and scan; the `markReceived` matrix, including `sheets.cancel` refused for the receiver.
- The tests assert behavior through the service and router against `invai_test`, with no mocks of the unit under test.
- Round-2 assertion changes follow decision 0010 (`packed:false`, `in_production`). Nothing was deleted or loosened without a stronger replacement: the hand-off test gained tote and scan assertions.

## The pack scans `packOrder` adds (the Today question)
- `packOrder` adds one `pack` scan only for a packed unit with **no** ok pack scan (`floor.ts:1089-1115`), and none on a hand-off. So `packOrder` itself never double-counts: 3 units gave 3 on Today, and a replay added nothing (`pack.test.ts:128`).
- Today can still over-count, but not because of this card:
  - `today/service.ts:117` counts `count(*)` of ok pack scans.
  - The matcher accepts any repeat pack scan of a packed unit as `ok:true` (`matcher.ts:193-197`).
  - So a second scan of the same unit, whether a re-scan, a late offline replay, or a scan that races `packOrder`, since `scan` doesn't lock the order, counts twice.
  - This happened before the card whenever a packer re-scanned a unit.
- Filed as a follow-up below, not blocking: the pack-station counter (`count(distinct order_item_id)`) and `staffOutput` are already correct.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed. No `e2e/**` or `*.acceptance.test.ts` was touched.
- [x] Nothing outside scope.
- [x] Tests exercise the behavior and none were weakened (scan: no hits; the round-2 test fails on round-1 code).
- [x] Tenancy and idempotency: tested (`pack.test.ts:291`, `:257`, `:92`).
- [x] Decisions recorded (0010).

## Optional notes (not blocking)
1. **Follow-up for the Today owner:** make `today/service.ts:117-118` count `count(distinct order_item_id)` per action, as the station queue already does. Otherwise Today's "pack done" can exceed units packed. The same applies to pick and press re-scans.
2. **Integration gate:** this card changes pack semantics (a golden-path area). I didn't run the API, browser or floor E2E suites, because they need a fresh-seed slot on the shared DB. The wave gate must run them. The floor `press.spec.ts` pack step and the API golden path's floor step still use the per-unit flow; T-4-4 should add a "Mark packed" step (refused, then packed) and a "Hand to lead" step.
3. Missing tests worth adding: same-key concurrency on two orders; a `floor_requests` `WITH CHECK` violation; a `wrong_style` press test at the router level (today it's `matcher.test.ts` only, plus my live check).
4. For T-4-4 and T-4-2: a hand-off result is stored under its key, so the tablet needs a new key for the later "Mark packed". Reusing it gives `CONFLICT` (verified live).
