# Review of T-1-3 (round 2)

- Reviewer: reviewer on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
Clean detached worktree at `ed8a300` (single-commit review; its true git parent is `8becdb5`/T-1-5, but T-1-3's own files were last touched at `b117997`, so `git diff b117997 ed8a300 -- <T-1-3 owned paths>` reproduces the same 3-file diff as `git show --stat ed8a300`). Own DB `invai_test_r13`
(`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/invai_test_r13`,
`TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/invai_test_r13`).

Per the tech lead's instruction I did **not** run `pnpm install` and left `node_modules/@invai/contracts` alone: I symlinked the shared repo's top-level `node_modules/` into the worktree and ran the toolchain binaries directly (`./node_modules/.bin/tsc`, `.../biome`, `.../vitest`) to avoid pnpm's auto-install-on-run behavior, which corrupted that symlink last round.

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | clean, no errors |
| `./node_modules/.bin/biome check .` | `Checked 197 files in 127ms. No fixes applied.` |
| `./node_modules/.bin/vitest run --passWithNoTests` | `Test Files 39 passed (39)`, `Tests 228 passed (228)` (was 226 before this round's 2 new tests) |
| `./node_modules/.bin/vitest run src/modules/inventory/po-safety.test.ts src/db/rls-coverage.test.ts src/db/rls.test.ts src/api/authz.test.ts` | `4 passed`, `38 passed` |
| `git diff b117997 ed8a300 -- src/modules/inventory/service.ts src/integrations/suppliers/index.ts src/modules/inventory/po-safety.test.ts` | 3 files, matches `git show --stat ed8a300` exactly — confirms only T-1-3's owned paths changed |
| `grep -n "markSubmitted(" src/modules/inventory/service.ts` | one caller left (`submitPo`'s success path, with a real `result` from the supplier), and `markSubmitted`'s `result` parameter is now typed `SupplierOrderResult` (not `| null`) — the compiler now enforces that no code path can reach `submitted` without a real supplier order id |

Cleanup: worktree removed, `invai_test_r13` dropped, `node_modules/@invai/contracts` left exactly as found (`-> ../../../invai-contracts`, verified after).

## Round-1 blocking finding — resolved
`service.ts:1149-1152`'s "mark submitted, no supplier call" branch for SanMar/"other" in production is gone. `submitPo` now throws `conflict("This supplier has no connection yet. Place the order with the supplier directly.")` when `supplierAdapterFor` returns null, **before** any write in tx 1 (the throw is ahead of the `status: "submitting"` update), so the PO stays exactly `draft`: no `submitAttemptedAt`, no `supplierOrderId`, no `po.submitted` outbox event, no audit row. Verified in the new test `"refuses in production for a supplier with no ordering API, and fakes nothing"` (both `sanmar` and `other`, asserting the row and that `outbox.emit` was never called with `po.submitted`), and confirmed dev/test behavior is unchanged by `"outside production a supplier with no API still uses the mock"` (`MOCK-SAN-…`).

## Acceptance criteria
Unchanged from round 1 except AC1, which is strengthened: `submitPo` (not just `listSuppliers`/`supplierAdapterFor`) now refuses cleanly for a no-API supplier in production, matching the S&S "not connected" refusal symmetrically. AC2–AC5 re-verified green with the full suite; nothing else in the round-2 diff touches them.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`service.ts`, `integrations/suppliers/index.ts` doc comment, `po-safety.test.ts`).
- [x] Nothing outside scope — this is exactly the tech lead's decision, nothing more.
- [x] Tests exercise the new behavior and none were weakened: both new tests are additive (no assertion removed anywhere in the round-2 diff), and the second one guards against a regression to the mock-outside-production path silently breaking.
- [x] Money, tenancy and idempotency: untouched by this round; still integer cents, `purchase_order_receipts` RLS unchanged, `submitPo`'s crash-safety mechanics unchanged (this diff only adds an earlier refusal for a case that previously reached the supplier-call branch with `adapter === null`).
- [x] Decision recorded: the tech lead's message states the decision (refuse with CONFLICT; "mark placed manually" deferred to B-86) and the code/tests/commit message all match it exactly.

## Optional notes (not blocking)
- The report notes the production refusal path wasn't curled (booting with `NODE_ENV=production` needs secure cookies over plain HTTP, per T-1-1's guard) — service-level test coverage plus the code-level `throw` placement (verified above, ahead of any write) is sufficient evidence for a pure-refusal path with no side effects to hide.
- B-86 ("mark PO as placed by hand" for no-API suppliers) is correctly filed as a follow-up rather than smuggled into this card.
