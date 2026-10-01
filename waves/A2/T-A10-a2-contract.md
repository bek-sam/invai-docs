# T-A10: A2 contract: digest D9–D13, Today actions, recordActionClick (contract 0.10.0)

| Field | Value |
|---|---|
| Wave | A2 |
| Scope ref | `product/scope.md#mvp-in` items 14, 17 (`waves/analytics-scope-check.md`, B-176, B-177) |
| Spec | `specs/business-analytics-v2.md` Track E, AC-E1..E1f, AC-E2, AC-E5 |
| Owner | architect |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (the architect is the contract co-reviewer by role) |
| Risk flags | contract |
| Model | opus |

Note: the spec numbers T-A10 as the Today card. In this wave T-A10 is the contract both backend and web need, and B-177 (Today) is split into T-A9 (backend) and T-A7 (web), so the wave stays at 5 cards.

## Owned paths (edit)
- `invai-contracts/src/**` (schemas `digest.ts`, `today.ts`, contract `today.ts`, permissions map, tests), `invai-contracts/package.json` (version only), `invai-contracts/CHANGELOG*` if present
- Stub grant: `invai-backend/src/modules/today/router.ts`, only to register the two new procedures as throwing stubs (`NOT_IMPLEMENTED`) so the backend root router typechecks. T-A9 replaces them.

## Read-only paths
- `invai-backend/src/modules/digest/**`, `invai-backend/src/modules/today/**` (other than the stub grant), `invai-web/**`, `invai-floor/**`

## Architect plan-review rulings (binding, `reviews/plan-architect.md` 1–3): `today.recordActionClick` (POST `/today/actions/clicks`), D11 split into `review_dead_stock` and `restock_size_gap` (six kinds), new optional params `style`, `color`, `size`, `supplierId`, `supplierName`, `points`, `deltaCents`, `TodayAction` reuses `DigestAction`, `auth: "user"`, `generatedAt` nullable (null = not built yet), `ACTION_NOT_FOUND` for an unknown key, `shipmentsWithoutZone` fixed in contract text only. These override the proposals below.

## Interfaces promised (names fixed by this card; change them only with the tech lead)
- `DIGEST_DETECTORS` gains `"D9" | "D10" | "D11" | "D12" | "D13"` (append, keep order).
- `DIGEST_ACTION_KINDS` gains one kind per new detector. Proposed: `review_shipping_prices` (D9), `review_losing_orders` (D10), `review_stock_health` (D11: dead stock or size gap, params say which), `review_blank_cost` (D12), `see_break_even` (D13). Params carry `channel`, `style`, `color`, `size`, `supplier`, cents and points, never buyer data.
- `today.actions({ date?: DateOnly }) -> TodayActions` with `{ date, windowStart, windowEnd, actions: TodayAction[] (max 5, ranked), steady: boolean, generatedAt }`; `TodayAction = { key: string (stable per date + detector + subject), rank, detector, kind, params, href, impactCents: int | null, clickedAt: Timestamp | null }`. Permission `finance.read` (dollar impacts; AC-E5).
- `today.actionClick({ date, key }) -> { clickedAt }`: first click wins, repeats return the same `clickedAt` (the `digest.clicks` pattern). Permission `finance.read`.
- Decide and record in the report: whether actions are stored by a daily job (rule 9: heavy work in the queue) or computed on read with a cache; T-A9 implements what you decide. Also rule on A1's note: `shipmentsWithoutZone` counts orders, the contract text says shipments. Fix the text here, or name the backend change for T-A9.

## Acceptance criteria
1. The additions above are additive only: no removed or renamed procedure, field or enum value; existing consumers (backend, web, floor) typecheck unchanged against the linked package.
2. Contract tests cover: the new enum values, the two procedures' permission `finance.read`, `actions` max 5, `impactCents` integer cents, `key` required.
3. Version 0.10.0, with a changelog line if the repo keeps one.
4. The backend stub compiles; calling either procedure returns a clean `NOT_IMPLEMENTED` style error, not a crash.

## Verification
- `cd invai-contracts && pnpm typecheck && pnpm lint && pnpm test`
- `pnpm typecheck` in `invai-backend`, `invai-web`, `invai-floor` (consumers unchanged)

## Out of scope
- Detector logic, the Today service, any web code. Track D (B-178..B-181).

## Budget
- About 1 hour. Escalate to the tech lead if blocked for more than about 30 minutes.
