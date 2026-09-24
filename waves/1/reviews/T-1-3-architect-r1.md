# Review of T-1-3 (round 1)

- Reviewer: architect on Fable
- Author: integrations-engineer on Opus 5.5
- Verdict: **changes-required**

## Evidence I re-ran
Same clean worktree at `b117997` (parent `293047b`) as the primary reviewer, own DB `invai_test_r13`.

| Command | Result |
|---|---|
| `pnpm typecheck` | clean |
| `pnpm test` | `212 passed (212)` |
| Contract check: `grep -n "idempotencyKey" invai-contracts/src/schemas/inventory.ts` | `184: idempotencyKey: z.string().min(8).max(128).optional()` — additive, matches the stub `wave.md` committed for this card |
| `grep -rn "PO_STATES" invai-contracts/src/schemas/inventory.ts` | unchanged: `draft, submitted, partially_received, received, cancelled` — no `submitting` |
| `git diff 293047b b117997 -- invai-backend/src/db/schema/inventory.ts` (read via `invai-backend` repo) | `submitting` added to backend-only `PO_STATUSES`; `toPurchaseOrders` maps it back to `draft` before it reaches the API — confirmed the contract boundary is respected |

## Acceptance criteria (contract angle)
| # | Met? | Evidence |
|---|---|---|
| 3 | yes | Uses the `idempotencyKey` stub exactly as agreed in `wave.md`'s "Agreed interfaces"; optional, additive, no other field shape changes. `ReceiveInput` round-trips fine. |
| 2 | yes (mechanism) | The transaction-boundary split I required in `plan-architect-r1.md` is implemented as specified: `submitPo` now owns its own `withTenant` calls; `router.ts`'s call site updated to match. |

## Blocking findings
1. **Contract-adjacent state semantics changed without a contract change or decision record.** `invai-backend/src/modules/inventory/service.ts` (`submitPo`'s `if (!adapter) { markSubmitted(tx, ctx, po, null, "manual"); ... }` branch, and `toPurchaseOrders`'s `submitting → draft` mapping) now has a PO reach the contract's `submitted` state for SanMar/"other" without ever contacting a supplier. `submitted` is a contract-level state other consumers (web, floor is n/a here, `today`/alerts, `finance`) read and reasonably assume means "sent." This wasn't in T-1-3's AC list, wasn't in `wave.md`'s agreed interfaces, and I wasn't asked to review a contract change for it — it arrived as backend-only behavior riding on an existing enum value. Per my own role file: "MUST: shop language… the reason for a design choice in a doc comment, **and an ADR for anything cross-cutting**." A PO's `submitted` meaning is exactly that: cross-cutting. Concretely, this also uses the same "manual" fallback that produced the bug this very card exists to remove (the pre-change code faked a `MOCK-SAN-…` id for SanMar/other in prod; the fix trades a fake id for a fake status) — better than before, but not resolved to a state other modules can trust.
   - Required before I approve: either the author's option (a) from the reviewer's file — refuse (`CONFLICT`) for no-API suppliers in production, matching AC1's own symmetry with S&S — or a decision record in `invai-docs/decisions/` plus (if kept) a contract-visible way to tell "confirmed with supplier" apart from "needs manual placement" (a boolean or a distinct enum value added later), not an audit-log sentence alone.
2. Joining reviewer's finding on the same code (`service.ts` around line 1149) — not duplicating file:line detail here, see `T-1-3-reviewer-r1.md`.

## Checks
- [x] Only owned paths changed; no `invai-contracts/**` files touched by this commit (correctly used the pre-committed stub, read-only).
- [x] `submitting`'s "internal only" design is sound and doesn't leak: verified `toPurchaseOrders` maps it to `draft` for every read path, and `listPos`'s `draft` filter includes `submitting` server-side only.
- [x] `po.poNo` reused as the supplier idempotency key: confirmed unique-per-company and immutable (no update path touches `poNo` in the diff) — matches what I signed off on in the plan review.
- [ ] Decisions recorded where needed — missing (blocking finding above).

## Optional notes (not blocking)
- Once accepted, `submitting` should be added to the contract's `PO_STATES` (additive) in a follow-up card so the mapping-to-`draft` workaround can be dropped, as the author's report already suggests.
