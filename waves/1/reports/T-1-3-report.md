# Report: T-1-3 Tenants never order on InvAI's supplier account, and POs are crash-safe
Author: integrations-engineer on Opus 5.5

```
Card: T-1-3  Owner: integrations-engineer  Scope ref: always-in-scope: security (money); product/scope.md#mvp-in item 6
Owned (edit): invai-backend/src/integrations/suppliers/**, src/modules/inventory/**, src/db/schema/inventory.ts + its migration, tests next to these
Read-only: invai-contracts/** (used the architect's stub 1a22b29), the rest of src/**
Risk flags -> co-reviewers: payments, migration -> security-reviewer, backend-foundation, backend-engineer (inventory), architect (contract field)
```

## Commits
- invai-backend `b117997` (not pushed): "Suppliers use only the tenant's own account; PO submit, receive and cancel are crash-safe (T-1-3)". 13 files, all in T-1-3's owned paths, including migration `0008_inventory_po_idempotency` (journal entry idx 8, on top of T-1-2's committed 0006/0007).
- Correction: the first commit `a2a0807` accidentally included another agent's staged deletion of `src/db/seed/trademarks.ts`, because `git commit` took the shared index. I soft-reset that unpushed commit, which left their deletion staged for them exactly as before, and recommitted with `git commit -- <my paths>`. `git show --stat HEAD` now lists only my 13 files. `a2a0807` no longer exists on `main`.

## Built
- **AC1: no platform-key fallback.** `getSupplierAdapter(supplier, companyCreds, { account, production })` never reads `SS_ACTIVEWEAR_*`. You get `live` only with the tenant's own credentials. Without them, dev and test get the mock (scoped per company). In production, S&S throws `SupplierNotConnectedError`, and a supplier with no API returns `null`. New `supplierProvider()` backs `listSuppliers` (`live` only with tenant creds; `none` in production without creds). `supplierAdapterFor` maps the error to `CONFLICT`: "Connect your S&S Activewear account (account number and API key) in Inventory settings before ordering from S&S Activewear." (files: `integrations/suppliers/index.ts`, `types.ts`, `modules/inventory/service.ts`)
- **AC2: crash-safe `submitPo(ctx, id)`.** It now manages its own transactions, and the router no longer wraps it.
  1. Tx 1 locks the PO, sets `status = 'submitting'` and `submit_attempted_at = now()`, and commits.
  2. With no transaction or lock held, it reads back first when resuming (`adapter.findOrder(poNo)`), then calls `placeOrder` with `poNo` as the idempotency key.
  3. Tx 2 records `supplier_order_id` and `submitted`, and emits and audits.

  Retry rules:
  - A submitted PO returns its stored result.
  - A `submitting` PO younger than `SUBMIT_IN_FLIGHT_MS` (2 min) returns `CONFLICT` ("being sent right now").
  - An older one, or one whose last call ended unknown (`submit_attempted_at` null), reads back before ordering.
  - A clear supplier rejection (4xx, or nothing sent) goes back to `draft` with `SUPPLIER_REJECTED`.
  - An unknown outcome (timeout, network, 5xx) stays `submitting` and returns `UPSTREAM_FAILED`, with "Submit again to check; it won't be ordered twice".
  - A failed Tx 2 clears the in-flight mark so the next submit reads back at once.

  (files: `modules/inventory/service.ts`, `router.ts`)
- **AC3: idempotent `receivePo`.** It uses the contract's optional `idempotencyKey`. New tenant table `purchase_order_receipts`, unique on `(company_id, idempotency_key)`, with RLS. The same key with the same lines returns the PO unchanged, and the same key with different lines or a different PO returns `CONFLICT`. A new key, or no key, is a legitimate second delivery. Keyed movements also get `receive:<receiptId>:<i>` ledger keys.
- **AC4: `cancelPo(ctx, id)`.**
  - Drafts, and POs never sent through an API, cancel locally.
  - A submitted PO is cancelled at the supplier first, outside any transaction, via `adapter.cancelOrder`.
  - If the adapter has no cancel or the supplier refuses, it reads back. If the supplier shows the order cancelled, it cancels locally. Otherwise it returns `CONFLICT`: "S&S Activewear still has order X for PO-… Cancel it with S&S Activewear first, then cancel it here."
  - A `submitting` PO is refused until it settles, and an already-cancelled PO returns as is.
- **S&S adapter** (docs checked 2026-09-24: Orders.aspx, Orders_Post.aspx, Orders_DELETE.aspx):
  - `rejectLineErrors: true`.
  - Split orders (one per warehouse) are joined as `"111,112"`.
  - `findOrder` uses `GET /v2/orders/{poNo}`, filtered to rows whose `poNumber` matches, and detects cancelled orders.
  - `cancelOrder` uses `DELETE /v2/orders/{orderNumber}` for each split order. S&S allows it only within 10 minutes.
  - `SupplierError.outcome` is `not_placed` or `unknown`.
  - `redirect: "error"`.
  - A rate-limit wait timeout is mapped to `not_placed`.
- **Mock supplier:** in-process `findOrder`/`cancelOrder`, keyed per company. `placeOrder` logs `mock supplier order placed`. It stays deterministic and keyless.
- **Schema and migration** `drizzle/0008_inventory_po_idempotency.sql`:
  - New table `purchase_order_receipts` with RLS policy `purchase_order_receipts_tenant`.
  - Nullable `purchase_orders.submit_attempted_at` (additive; `purchase_orders` is a small table).
  - `submitting` added to backend `PO_STATUSES`. It's a text column with no DB constraint, so no SQL was needed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `integrations/suppliers/index.test.ts` (live only with tenant creds; mock outside prod; prod throws / `none`; no-API supplier null in prod). `po-safety.test.ts` AC1 block (listSuppliers mock→live with tenant creds; production submit → `CONFLICT` "Connect your S&S Activewear account", PO stays draft). curl: `suppliers.list` → ssactivewear `mock` (dev, no creds). |
| 2 | yes | `po-safety.test.ts` AC2 block: supplier called with the PO committed as `submitting` and **not locked** (`FOR UPDATE NOWAIT` from inside `placeOrder` succeeds); twice → 1 call; **commit failure after supplier accepted** (emit throws in tx 2) → retry reads back, `placeOrder` count stays 1; in-flight crash → CONFLICT, then read-back after the window, 0 new orders; rejection → draft; unknown → retry reads back. Mutation check: disabling read-back makes 4 of these tests fail. curl: 3 submits (2 concurrent) → 1 supplier order. |
| 3 | yes | `po-safety.test.ts` AC3 block (same key twice → counted once, one movement; changed qty → CONFLICT; new key / no key → second delivery counted). curl below. |
| 4 | yes | `po-safety.test.ts` AC4 block (draft local; submitted → cancelled at supplier; no cancel API → refused with "Cancel it with S&S Activewear first", then allowed once the supplier shows it cancelled; supplier cancel fails → refused, stays submitted). S&S `cancelOrder` fixture test. curl below. |
| 5 | yes | Existing `service.test.ts` passes (only the `submitPo` call signature changed); full suite green. |

## Checks I ran (invai-backend, own test DB `invai_test_t13`)
```
export TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_t13 TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_t13
```
| Command | Result (last lines) |
|---|---|
| `pnpm typecheck` | `tsc --noEmit`, no errors |
| `pnpm lint` | `Checked 196 files in 83ms. No fixes applied.` |
| `pnpm test` | `Test Files 38 passed (38)`, `Tests 220 passed (220)` |
| `pnpm vitest run src/modules/inventory src/integrations/suppliers` | `5 passed (5)`, `38 passed (38)` |
| Mutation check: read-back removed from `submitPo` | `4 failed / 12 passed` in `po-safety.test.ts` (file then restored and `diff -q` against the backup was clean) |

These runs used the shared working tree, so they include other cards' uncommitted work (T-1-1, T-1-2, T-1-4, T-1-5) as it stood at the time. After regenerating the migration on T-1-2's committed journal, I recreated `invai_test_t13` and re-ran everything: `pnpm typecheck` clean, `pnpm lint` `Checked 198 files … No fixes applied.`, `pnpm test` `Test Files 39 passed (39)`, `Tests 226 passed (226)`. I also typechecked a clean detached worktree of `b117997` alone (`tsc --noEmit`: no errors; biome on my paths: `Checked 19 files … No fixes applied.`), so the commit doesn't depend on anyone's uncommitted work.

## Exercised for real
The API ran on `PORT=3130` against a **scratch clone of the dev DB** (`invai_dev_t13`, made with `pg_dump invai | psql`, migrated to 0008, dropped afterwards). The shared dev DB was not migrated, because that would also have applied T-1-2's then-uncommitted 0006/0007. The script is `/tmp/t13-exercise.sh` (REST `/api/v1`, Better Auth cookie sign-in).
- Signed in as `owner@desertbloom.test`, got `200`.
- `GET /inventory/suppliers` returned `ssactivewear: mock`, `sanmar: mock`, `other: none`.
- Stock before: `{"onHand":17,"incoming":0}`. Created PO-20260924-01 for 24 units.
- **Refused case:** `packer@` `POST …/submit` returned `{"code":"FORBIDDEN","status":403}`.
- Submit ×2 concurrently returned `submitted MOCK-SSA-15762874` for one request and `409 CONFLICT "This purchase order is being sent to the supplier right now…"` for the other. A 3rd submit returned `submitted MOCK-SSA-15762874` (stored result).
- The API log has exactly **one** `mock supplier order placed … PO-20260924-01` line. There's one `purchase_order.submit` audit row, and `submit_attempted_at` is null afterwards.
- Receive 10 with key `curl-receipt-<id>`, twice: both returned `received: 10`. The same key with qty 11 returned `CONFLICT "This receipt was already recorded with different quantities"`. Stock after: `{"onHand":27,"incoming":14}` (+10 once). There's one `purchase_order_receipts` row and one `purchase_order.receive` audit row.
- Cancel of the partially received PO returned `INVALID_TRANSITION`.
- PO-20260924-02: submit returned `MOCK-SSA-50402693`. Cancel returned `cancelled`, with the log line `mock supplier order cancelled` and the audit line "cancelled (cancelled at S&S Activewear, MOCK-SSA-50402693)". A 2nd cancel returned `cancelled` with no second supplier call.

## Decisions
- **`submitting` is DB-only for now.** Contracts `PO_STATES` doesn't have it, and contracts belong to the architect, so the API shows a `submitting` PO as `draft` (nothing is confirmed yet). `listPos` treats a `draft` filter as including `submitting`. Pressing Submit again from the UI is exactly the safe retry path. **Follow-up for the architect:** add `submitting` to `PO_STATES` (additive), then drop the mapping in `toPurchaseOrders`.
- **The in-flight window is 2 minutes.** The worst case for one resume is two S&S calls, each up to a 30 s rate-limit wait plus a 20 s fetch timeout, which is about 100 s. A crashed process's PO can be retried after 2 minutes. An explicit failure clears the mark immediately.
- **Suppliers with no ordering API in production** (SanMar until B-36, and "other") get no adapter. `submitPo` marks the PO submitted with no supplier order id, and the audit says to place the order with the supplier. The old code would have produced a fake `MOCK-SAN-…` order id in production. This goes slightly beyond the literal card, but the alternative was either faking success or blocking manual POs. The reviewer should confirm. **Superseded in Round 2:** production now refuses with CONFLICT (see below).
- **Errors:** "not connected" and "cancel with the supplier first" are `CONFLICT` (declared in `COMMON_ERRORS`). An unknown outcome is `UPSTREAM_FAILED` with `{service:"supplier"}`. A clear rejection keeps the contract's `SUPPLIER_REJECTED`.
- **Idempotency keys:** the supplier key is `po.poNo` (unique per company, immutable, and sent as S&S `poNumber`). The receipt key is the client's `idempotencyKey`, unique on `(company_id, idempotency_key)`, with the first request stored in `purchase_order_receipts.lines`.

## Known gaps and follow-ups
- **Real S&S sandbox run: not done.** No S&S credentials exist, and S&S has no separate sandbox host; `testOrder: true` requires a real account. The adapter is covered by stubbed-fetch fixture tests only. Response field names (`poNumber`, `orderStatus` "Canceled"/"Cancelled", the GET-by-PO identifier) come from the S&S docs pages above and must be confirmed with the owner's account (owner inbox / runbook row, with docs-writer).
- **S&S doesn't document POST dedupe.** Safety relies on read-back by PO number. Two InvAI processes can't both place, because Tx 1 serializes on the row and the in-flight window blocks a second caller.
- A `submitting` PO stuck longer than the window (for example, S&S down for a day) isn't surfaced to a person yet. It would be good to `raiseAlert` it in `modules/today` (backend-engineer).
- `env.mocks.supplier` and `SS_ACTIVEWEAR_*` in `src/env.ts` (backend-foundation) are now unused by supplier code. They can be removed, along with their `.env.example` and runbook rows, in a later card.
- Production with `ALLOW_MOCKS=true` (T-1-1) still refuses supplier orders without tenant creds. That's deliberate: this code reads `env.isProd` only, so a demo stage never fakes a supplier order. If the owner wants mock POs on a demo stage, pass `production: env.isProd && !env.allowMocks` in `supplierProvider`/`getSupplierAdapter`.
- User-facing error messages are English only, like every other backend error. Web translation of error messages is a separate concern.
- `incoming` doesn't count `submitting` POs until they are confirmed. That's fine at a 2-minute scale.
- Web: `po-badge.tsx` needs no change, since the API never returns `submitting`. When the architect adds the state, web must add a badge.

## Blocked by other owners
- None blocking. Migration sequencing: my migration had to be generated on top of T-1-2's 0006/0007, which were uncommitted when I finished. I waited for T-1-2's commit (`90657ac`), then regenerated mine with `pnpm db:generate --name inventory_po_idempotency`. The SQL was byte-identical to the first generation, and the journal diff adds only idx 8.

## Processes and data
- Stopped: the API on :3130 (PID 92462); port free afterwards. The background git-watch loop ended.
- Scratch DB `invai_dev_t13` dropped. `invai_test_t13` left in place (test DB for this card).
- Shared dev DB `invai`: untouched (still at migration 0005; needs `pnpm db:migrate` at the integration gate).

## Round 2 (after review r1)
Blocking finding: reviewer and architect (`reviews/T-1-3-reviewer-r1.md`, `T-1-3-architect-r1.md`), with backend-engineer, backend-foundation and security-reviewer concurring. In production, `submitPo` marked SanMar and "other" POs `submitted` with no supplier call (`service.ts:1149-1152`).

**Tech lead's decision, implemented:** in production, `submitPo` refuses suppliers that have no API adapter.

### Changed (commit `ed8a300`, not pushed; 3 files)
- `src/modules/inventory/service.ts`:
  - When `supplierAdapterFor` returns null (production, supplier with no ordering API), `submitPo` now throws `CONFLICT`: "This supplier has no connection yet. Place the order with the supplier directly." Tx 1 rolls back, so the PO stays `draft` with no `submit_attempted_at`, no outbox event and no audit row.
  - The manual `markSubmitted(…, null, "manual")` branch is gone, and `markSubmitted` now requires a supplier result. No code path can produce `submitted` without a supplier order id any more.
  - A "mark PO as placed by hand" action is not built; it's planned for B-86.
- Development and tests are unchanged: without production, SanMar and "other" still use the mock (`MOCK-SAN-…`).
- `src/integrations/suppliers/index.ts`: doc comment only ("callers refuse to order; nothing is faked").
- `src/modules/inventory/po-safety.test.ts`, two new service-level tests:
  - "refuses in production for a supplier with no ordering API, and fakes nothing": for `sanmar` and `other` in production, `CONFLICT` with the exact message. The DB row stays `draft` with `supplier_order_id`, `submitted_at` and `submit_attempted_at` all null, and no `po.submitted` event is emitted.
  - "outside production a supplier with no API still uses the mock": a SanMar PO is submitted as `MOCK-SAN-…`.

### Checks (invai-backend, `invai_test_t13`)
The `node_modules/@invai/contracts` symlink was checked first: `../../../invai-contracts`.

| Command | Result |
|---|---|
| `pnpm typecheck` | `tsc --noEmit`, no errors |
| `pnpm lint` | `Checked 198 files in 86ms. No fixes applied.` |
| `pnpm test` | `Test Files 39 passed (39)`, `Tests 228 passed (228)` (was 226, +2 new) |
| `pnpm vitest run src/modules/inventory/po-safety.test.ts` | `Tests 18 passed (18)` |
| Mutation check: the refusal replaced by a silent `return { kind: "done" }` | `1 failed / 17 passed`; the new production test fails. `service.ts` restored from backup. |

### Exercised
The production path is exercised at service level against the real test DB, with `getSupplierAdapter` in production mode. I didn't curl it: the API would have to boot with `NODE_ENV=production` (T-1-1 key guard, secure cookies over plain HTTP). The dev path the API serves is unchanged from round 1's curl run.

### Commit hygiene
`git commit -m … -- <3 paths>`. `git show --stat HEAD` lists only these 3 files, and nothing staged by other agents was included. No amend, no push.

### Remaining follow-ups (unchanged, plus one)
- B-86: "mark PO as placed by hand" for suppliers with no API (and a UI hint for this CONFLICT). Until then, production shops can't move SanMar or "other" POs past draft in InvAI.
- Architect: add `submitting` to contracts `PO_STATES` (round 1 follow-up; the architect's review notes it as unchanged).

