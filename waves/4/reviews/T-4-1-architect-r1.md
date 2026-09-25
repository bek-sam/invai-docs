# Review of T-4-1 (round 1): architect co-review (contract stubs and contract fit)

- Reviewer: architect co-review, run by the reviewer agent on Claude Opus 5.5 (a different model from the stub author)
- Author: architect on Claude Sonnet 5 (contracts `c181abf`, backend stub `e427b8f`); backend-engineer on Claude Opus 5.5 (implementation)
- Verdict: **changes-required**. One blocking finding: doc comments only, no shape change.

## Evidence I re-ran
| Command | Result |
|---|---|
| contracts `vitest run` | 4 files, 31 tests passed |
| contracts `tsc --noEmit` / `biome check .` | exit 0 / 46 files clean |
| `scan-test-weakening.sh invai-contracts 11f53f5` | no hits |
| backend `tsc` / `vitest` / build at `bdffe6f` | clean / 63 files, 447 passed / success |
| web `tsc --noEmit`, floor `tsc --noEmit` against the stubs | clean, clean. No consumer builds an `Order` literal (`grep "hold: null"` in web/floor src: none). |
| live, API :3191: `markReceived` as receiver / office / presser; `sheets.cancel` and `regenerate` as receiver | 200 / 200 / 403 `production.receive`; 403 / 403 `production.build` |
| live: `packOrder` with override as packer / admin | 403 `production.override` / 200 |
| live: refusal body | `{"defined":true,"code":"PACK_INCOMPLETE","status":409,"data":{"missing":[…]}}`. The declared error matches the contract. |

## Stub review
- **Additive?** Mostly yes:
  - a new procedure;
  - new schemas;
  - two permissions appended in the production section;
  - `receiving` appended to the end of `STATIONS`;
  - a new output field `Order.packOverride`. It's required-nullable, which is additive for readers. Only `schemas.test.ts` builds an `Order` literal, and it was updated.

  One exception: **`sheets.markReceived` moves from `production.build` to `production.receive`**. The commit message and wave.md §5 state this. I checked that nobody lost access: owner, admin (`SHOP_ALL`), office (new grant) and receiver are allowed; presser, packer and designer never had `production.build`. Verified live and in `pack.test.ts:436`.
- **New enum value `receiving`:** consumers with exhaustive `Record<Station, …>` maps must handle it. Backend `DEFAULT_ACTION` and `STATION_KINDS` handle it (`c839e93`). Web and floor typecheck clean.
- **Permission choice:** `packOrder` declares `production.scan`, and `production.override` is checked in the handler (wave.md §3). This works, and the error names the permission. `PROCEDURE_PERMISSIONS` can't show the override gate, so `authz.test.ts` doesn't see it. `pack.test.ts:410` is the only guard. Acceptable.
- **State machine:** no `ORDER_STATUSES` change. `packOverride` is metadata, and `deriveOrderStatus` stays the only source of status (checked in `orders/state-machine.ts` after `bdffe6f`). This matches decision 0010.
- **Backend stub `e427b8f`:** a throwaway `notImplemented` handler, fully replaced in `d45e155`. No `NOT_IMPLEMENTED` is left in the production namespace.

## Blocking findings
1. **Stale contract comments contradict decision 0010 and the implemented idempotency.** The shape is right; the comments are the spec T-4-4 builds from next.
   - `invai-contracts/src/schemas/production.ts:319-320` (`PackOrderInput.idempotencyKey`): "A retry with the same key returns the original result rather than re-evaluating completeness."
     - The backend deliberately does **not** store refusals: `PACK_INCOMPLETE` is re-evaluated on retry (`pack.test.ts:139`, verified live).
     - Failure scenario: a floor engineer trusts the comment and treats a stored `PACK_INCOMPLETE` as final. The tablet then never retries "Mark packed" with the same key, or it mints a new key per retry and breaks the one-intent-one-key model.
     - Fix: "Only calls that changed something are stored. A refused call (`PACK_INCOMPLETE`, `FORBIDDEN`, `CONFLICT`) has no effect, and a retry re-evaluates."
   - `schemas/production.ts:322`: "pack anyway" should be "hand to lead" (0010).
   - `schemas/production.ts:339` (`missing`): "…or when packed was reached via override". After 0010, `packed` is never true via override. Fix: "non-empty whenever `packed` is false; empty when `packed` is true".
   - `schemas/production.ts:341` (`override`): "…or an earlier replay under the same order". Replays are scoped by key, not by order. Fix: "non-null when this call (or the stored call under this key) handed the order to a lead; `packed` is then false".
   - `schemas/orders.ts:176-177` (`Order.packOverride`): "packed with units still missing". Fix: "handed to a lead with units missing (0010); cleared once every non-cancelled unit is really packed".
   - `roles.ts:66`: `"production.override", // pack an order anyway…` should read "hand a short order to a lead".
   - `contract/production.ts:198-201` (the `packOrder` doc): add that an override returns `packed:false` with `missing[]` and `override`, releases the tote, and leaves the status alone (0010).

   The wave.md build log already assigns this to the architect. It must land before the T-4-1 push, because T-4-4 starts from it.

## Checks
- [x] Only owned paths changed. Architect: `invai-contracts/src/**`. The stub `e427b8f` touched `invai-backend/src/modules/production/router.ts`, which the build log grants for stubs.
- [x] Nothing outside scope.
- [x] Tests: nothing weakened. There is no contract test asserting that `production.override` is owner/admin only, or that `receiver` and `office` have `production.receive`. The generic role tests pass, and the backend tests cover the behavior. See note 1.
- [x] Tenancy and idempotency: not applicable to the contract, except the idempotency wording in finding 1.
- [x] Decisions: 0010 is written. It is still uncommitted in `invai-docs`.

## Optional notes (not blocking)
1. Add to `roles.test.ts`: `production.override` only for owner and admin; `production.receive` for receiver, office, owner and admin; no `production.build` for receiver. wave.md §5 asked for `contract.test.ts`/`roles.test.ts` updates "in the same commit"; only `schemas.test.ts` changed.
2. `c181abf`'s message says "All additive". Next time, say "additive except the documented `markReceived` permission reassignment".
3. B-27 follow-up: when QC and bins get `idempotencyKey`, reuse `floor_requests` (`kind`) as the report suggests.
