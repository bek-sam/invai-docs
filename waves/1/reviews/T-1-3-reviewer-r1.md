# Review of T-1-3 (round 1)

- Reviewer: reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **changes-required**

## Evidence I re-ran
Clean detached worktree at `b117997` (parent `293047b`), own DB `invai_test_r13`
(`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_r13`,
`TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_r13`).

| Command | Result |
|---|---|
| `pnpm typecheck` | clean, no errors |
| `pnpm lint` | `Checked 193 files in 96ms. No fixes applied.` |
| `pnpm test` | `Test Files 37 passed (37)`, `Tests 212 passed (212)` |
| `pnpm test src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts` | `3 passed`, `20 passed` |
| `pnpm build` | `tsup` — ESM build success, `dist/server.js` etc. written |
| `scan-test-weakening.sh /tmp/.../wt 293047b` | no deletions/skips/loosened assertions (0 removed, 73 added); the `vi.mock` hits are of `integrations/suppliers` (a real dependency, not the unit under test) and of `outbox.emit` to simulate a commit failure — both legitimate |
| New tests against base `293047b` (test files copied, base `service.ts`/`index.ts`) | `po-safety.test.ts` + `index.test.ts`: **23/25 fail** on base code (`tx.select is not a function` / signature mismatch, or missing `SupplierNotConnectedError` behavior) — proves the new tests exercise real new behavior, not vacuous |
| `grep -rn "withSystem(" <diff files>` | none added |

Cleanup: worktree removed, `invai_test_r13` dropped. (Note: an intermediate `pnpm install` attempt briefly corrupted the shared repo's `node_modules/@invai/contracts` symlink; I restored it to `../../../invai-contracts` and confirmed `pnpm typecheck` still resolves the module — no lasting damage.)

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `getSupplierAdapter`/`supplierProvider` never read `SS_ACTIVEWEAR_*`; `index.ts` only branches on tenant creds. `mock` outside prod, `CONFLICT` "Connect your S&S Activewear account…" in prod without creds (`service.ts` `supplierAdapterFor`), tested in `index.test.ts` and `po-safety.test.ts` AC1 block. |
| 2 | yes | `submitPo` (`service.ts:1116-1223`) opens its own transactions: tx1 marks `submitting`+commits, the supplier call runs with no tx/lock held (verified by a `FOR UPDATE NOWAIT` probe inside the test's `onPlace` callback), tx2 records the result. Commit-failure-after-accept test asserts `placeOrder` called once on retry. Concurrent-submit and stale-in-flight tests pass. |
| 3 | yes | `receivePo` idempotency via `purchase_order_receipts` unique `(company_id, idempotency_key)`; same key+lines → one effect (one movement row asserted); same key + different qty → `CONFLICT`; new/absent key → legitimate second delivery, tested and curl-verified. |
| 4 | yes | `cancelPo` cancels at supplier first outside a transaction, refuses with a clear message when the supplier can't/won't, accepts once a read-back shows it cancelled. |
| 5 | yes | Full suite green; `service.test.ts`'s one-line change (`svc.submitPo(ctx, po.id)` instead of `withTenant(...,(tx)=>svc.submitPo(tx,ctx,po.id))`) is a mechanical adaptation to the new signature, not a weakened assertion — the same 3 expectations on the result remain intact. |

## Blocking findings
1. `src/modules/inventory/service.ts:1149-1152` (the `if (!adapter) { await markSubmitted(tx, ctx, po, null, "manual"); ... }` branch) — **scope creep with a real correctness gap.** For SanMar and "other" suppliers, production `submitPo` now marks the PO `status: "submitted"` with `supplierOrderId: null` and *no call to anyone*, signalled only by an internal audit-log sentence. This is not in the card's AC1–AC5 (AC1 is scoped to "S&S env keys"/"tenant credentials"), it changes what `submitted` means for part of the PO state machine without a contract change or ADR, and the caller (the owner, in the UI, clicking Submit) gets an indistinguishable 200/`submitted` response whether the order was actually placed or not. Failure scenario: a shop owner submits a SanMar PO in production, sees "submitted," assumes 200 youth tees are on the way, and only discovers nothing was ordered when the shelf never restocks — with the only record of "please place this by hand" buried in an audit-log string, not the typed `PurchaseOrder` response. This is also untested at the service level: `po-safety.test.ts` has no case for `submitPo` against `sanmar`/`other` in production (only the adapter-resolution unit in `index.test.ts` checks `getSupplierAdapter` returns `null`). The author flagged this explicitly in the report as "goes slightly beyond the literal card… The reviewer should confirm" — I'm declining to confirm as-is. Needs either (a) refuse `submitPo` for no-API suppliers in production with a `CONFLICT` (symmetric with AC1's S&S behavior), or (b) an explicit decision record plus a contract-visible signal (not just an audit string) and a service-level test, with architect sign-off since it touches PO status semantics other modules read. See architect's co-review for the contract angle.

## Checks
- [x] Only owned paths changed (`git diff --stat 293047b b117997`): all 13 files under `integrations/suppliers/**`, `modules/inventory/**`, `db/schema/inventory.ts` + migration, and tests next to them.
- [x] Nothing outside scope, except the SanMar/"other" production behavior above.
- [x] Tests exercise the behavior; none weakened (scan script + base-code run confirm).
- [x] Tenancy (`withTenant`, RLS on `purchase_order_receipts`), idempotency (submit/receive/cancel all keyed and crash-tested), money untouched (still integer cents), no new user-facing strings needing es (errors stay English, matching existing convention).
- [ ] Decisions recorded where needed — missing for the SanMar/"other" behavior (blocking finding above).

## Optional notes (not blocking)
- `receivePo`'s race-loser message ("recorded with different quantities") is shown even on a true concurrent duplicate of the *same* request; harmless since a client retry then hits the success path, but slightly misleading wording.
- `env.mocks.supplier`/`SS_ACTIVEWEAR_*` are now dead code per the author's own note — fine to leave for a follow-up card (backend-foundation's path).
