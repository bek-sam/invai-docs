# Review of T-1-3 (round 2)

- Reviewer: architect on Fable
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran
Same clean worktree at `ed8a300`, own DB `invai_test_r13`, toolchain binaries run directly via the symlinked
`node_modules/` (no `pnpm install`, `node_modules/@invai/contracts` left untouched at `../../../invai-contracts`).

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | clean |
| `./node_modules/.bin/vitest run --passWithNoTests` | `228 passed (228)` |
| `git diff b117997 ed8a300 -- invai-backend/src/modules/inventory/service.ts` (contract-boundary check) | the change is entirely inside `submitPo`'s tx 1, before any DB write — no new state, no new procedure, no contract-visible field touched |
| `grep -n "submitting\|PO_STATES" invai-contracts/src/schemas/inventory.ts` | unchanged since round 1: `submitting` still absent from the contract; `toPurchaseOrders`'s internal `submitting → draft` mapping (round 1) is untouched by this diff |

## Round-1 blocking finding — resolved
My round-1 concern was that a PO could reach the contract's `submitted` state without ever being sent to a supplier, with no ADR and no contract-visible signal. Round 2 removes that path entirely rather than adding a signal for it: `submitPo` now refuses (`CONFLICT`) before any state change when there's no adapter, so `submitted` keeps its one meaning — "the supplier has the order" — for every PO, on every supplier, in every environment. That's a cleaner resolution than the alternative I offered (a typed "needs manual placement" flag), because it doesn't need a contract change or an ADR: the state machine's existing meaning is simply preserved, and the gap (no way to move a SanMar/"other" PO past `draft` in production yet) is explicitly filed as B-86 rather than shipped half-built.
- `markSubmitted`'s `result` parameter changed from `SupplierOrderResult | null` to `SupplierOrderResult` (compiler-enforced: no caller can mark a PO submitted without a real supplier result) — confirmed only one call site remains, in the success branch after a real `placeOrder`/read-back.
- The commit message and code comment ("Marking a PO as placed by hand is B-86") match the tech lead's decision exactly; no scope crept back in.

## Acceptance criteria (contract angle)
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `submitPo` now refuses symmetrically for both "no tenant credentials" (S&S) and "no ordering API" (SanMar/other) in production — one consistent rule: a PO only reaches `submitted` with a real supplier order id. |

## Blocking findings
None.

## Checks
- [x] No `invai-contracts/**` changes in this commit — correctly stayed on the backend side of the boundary, consistent with round 1.
- [x] No new procedure, no new enum value, no schema change — round 2 is a pure behavior tightening inside an already-reviewed function.
- [x] PO state machine invariant restored: `submitted` now always implies a real supplier order id, everywhere in the codebase (verified via the `markSubmitted` signature change, not just by reading the new branch).
- [x] Decision recorded: the tech lead's message is the decision record for this scope question; B-86 captures the deferred feature. No ADR needed since no contract or cross-cutting design changed — this is a bug-fix-shaped correction, not a new design.

## Optional notes (not blocking)
- Once B-86 is picked up, it will need a contract change (a way to record "placed by hand" — likely a `placedManuallyAt` field or similar, additive) and should come back through architect review at that time. Flagging so the eventual card scopes it correctly rather than reaching for `submitting`/`PO_STATES` first, per my round-1 note.
