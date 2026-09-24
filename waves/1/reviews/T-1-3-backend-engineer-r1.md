# Review of T-1-3 (round 1)

- Reviewer: backend-engineer (inventory) on Opus
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
Same clean worktree at `b117997` (parent `293047b`), own DB `invai_test_r13`.

| Command | Result |
|---|---|
| `pnpm vitest run src/modules/inventory src/integrations/suppliers` | `5 test files passed`, `38 passed (38)` (inventory) + `5 passed` (suppliers index) — matches the report's numbers |
| `pnpm test` (full) | `212 passed (212)` |
| Manual read of `src/modules/inventory/router.ts` diff | `submit`/`cancel` now call `svc.submitPo(tenant, input.id)` / `svc.cancelPo(tenant, input.id)` directly (no `withTenant` wrapper at the call site) — matches the service functions managing their own transactions; `create`/`update`/`receive` unchanged, still wrapped |
| Cross-module check: `grep -rn "from \"../inventory" ../*/service.ts` (other modules' calls into inventory) | no caller of `submitPo`/`cancelPo` outside `router.ts` — the signature change is fully contained |

## Acceptance criteria (module-pattern angle)
| # | Met? | Evidence |
|---|---|---|
| 2 | yes | The module's usual `(tx, ctx, input)` service-function shape is deliberately broken for `submitPo`/`cancelPo` only, and it's the right call: these are the two functions that must make an external call between two commits, which is exactly the case the pattern doesn't cover. The rest of the module (`createPo`, `updatePo`, `receivePo`, `listPos`, `listSuppliers`) keeps the standard shape. |
| 3 | yes | `receivePo` reuses `ledger.ts`'s existing `idempotencyKey` convention for movements (`receive:<receiptId>:<i>`), not a new mechanism — consistent with `reserve:order_item:…`/`release:…`/`consume:…` already in that file. |
| all | yes | Errors use `lib/errors.ts` helpers (`conflict`, `invalidTransition`, `notFound`, `badRequest`) plus the two new `ORPCError` codes (`UPSTREAM_FAILED`, `SUPPLIER_REJECTED`) already declared in the contract's `COMMON_ERRORS`/per-procedure errors — no off-contract error code introduced. |

## Blocking findings
None on module patterns, cross-module usage, or the inventory functions other modules call (`reserveForItems` etc. are untouched by this diff — confirmed no edits outside `submitPo`/`receivePo`/`cancelPo`/`cancelPo`'s helpers and supplier plumbing). I concur with `reviewer`'s and `architect`'s blocking finding on the SanMar/"other" production behavior in `submitPo`'s `if (!adapter)` branch — as the module's co-reviewer I'd add one point: this also means `incoming` stock and `listPos` will start showing SanMar/"other" POs as `submitted` with `supplierOrderId: null` in production once this ships, which is a UI-visible change to how those suppliers already behaved (previously fake-but-populated `MOCK-SAN-…` ids) that no inventory-module test or UI consumer has been checked against. Not duplicating as a separate blocking item — same root cause as the reviewer/architect finding; fixing it fixes this too.

## Checks
- [x] `withTenant` used on every request path except the two functions the card explicitly requires to manage their own transactions, and that's documented in a code comment (`router.ts`'s "submit and cancel open their own short transactions" comment).
- [x] New tenant table only via the shared schema conventions (not this reviewer's ownership, but consistent with the module's other tables).
- [x] Idempotent submit/receive/cancel, each with a run-twice test.
- [x] Cross-tenant isolation for the new table exercised (`po-safety.test.ts`'s "reports live only once the tenant's own credentials exist" test uses a second company).
- [x] No new `NOT_IMPLEMENTED` stubs in the inventory namespace.

## Optional notes (not blocking)
- `supplierStock`'s refactor to look up `supplierRows` once instead of per-supplier via `supplierAdapterFor` (avoiding a caught-and-swallowed `CONFLICT` per no-creds supplier) is a nice incidental fix — confirmed it still `continue`s cleanly for `provider === "none"` without throwing into the `catch` block.
