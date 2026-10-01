# Review: T-P4-1 (architect co-review, round 1)

- Reviewer: architect (Opus 5.5). Author: backend-engineer (Opus 5.5). Angle: cross-module meaning of `isReprint` (ADR 0020, plan review rulings 1-4, 6, 7). Tests and arithmetic: primary reviewer.
- Diffs: invai-backend `8d69b64` (14 files), invai-docs `8881d5a` (metrics SQL, data-analyst grant).
- **Verdict: approve**

## Ruling 2: re-import (orders/import.ts)
- `:528-535` `applyLineEdits` now groups every unit, reprinted ones included. Case 1 (qty-1 line, only unit reprinted) pairs by `channelLineId` to its `ExistingLine`, so the "line added" path (`:594-598`) can't fire. Case 2 (qty 2, one reprinted): `kept` counts both, `counted = 2`, no replacement (`:661-665`).
- `:685` `unitsInLine` update covers every unit on the line. `:863` channel line-cancel loads all units for the line, so a reprinted unit gets cancelled. The "line removed" path (`:689-695`) reads the same unfiltered `pending`, so it cancels reprinted units too.
- `grep isReprint src/modules/orders` finds only the comment at `import.ts:528` and the badge copy at `orders/service.ts:278`. No path is left that can add a second unit or skip cancelling a reprinted one. A real quantity drop still cancels exactly one unit (test qty-2, last assertion).
- Re-ran `vitest run src/modules/orders/import-edits.test.ts`: 14/14 pass (3 new: qty-1, qty-2 plus a real drop, line-cancel including a replay that returns `cancelled: 0`).

## Ruling 1: no reader decides sale or units from the flag
`grep -rn "isReprint\|is_reprint" invai-backend/src` (non-test), every hit classified:
- Production (re-pressed meaning, untouched; diff stat has no `production/**`): `floor.ts:411,642,775`, `sheets.ts:193,230,341,498,506,520,647,1187`, `views.ts:198,255`.
- Pass-through or badge: `orders/service.ts:278`. `finance/service.ts:745,809,839,1076` copy the flag to `profit_lines` and the contract. `:560` reads `transfers.isReprint` alongside transfer cost (ADR 0020 item 3).
- Schema columns (`orders.ts:209`, `finance.ts:147`, `production.ts:164`) and seed (`builder.ts`, writes the flag with the re-pressed meaning).
- `inventory/ledger.ts:187,195` selects the flag but never reads it. Harmless dead field (optional note).
- Finance `service.ts:605-609` (sellable = every unit, active = non-cancelled), `:1036-1038` (order summary). Refunds `refunds.ts:140,144,267` (scope, cancelled credit, channel match). Analytics `shared.ts:61`, `finance-service.ts:158,212,549-586`, `design-service.ts:129`, `inventory-service.ts:167`. `market/history.ts:60,99`. None of them filter on the flag any more.
- AI reads were already fixed in T-P4-4 `461c8fd`: no `isReprint` hit left under `src/ai` or `modules/ai`.
- `grep is_reprint invai-docs/metrics` finds nothing. `8881d5a` drops the filter from the definitions and SQL, with an ADR 0020 note.

## Refunds
A unit with `cancelled && isReprint` now counts toward the cancelled credit, and a shipped reprinted unit takes a line refund. Both match "a sale unit is any non-cancelled item" (ruling 1); the new test is at `refunds.test.ts:142`.

## Rulings 3, 4, 6, 7
- No contract, schema, migration or seed change: diff stat lists only `modules/{analytics,digest,finance,market,orders}` (ruling 4).
- The release-notes line (report §Release notes) names nightly 45 days plus `finance.recompute` for older rows, with no backfill. Matches ruling 3.
- AI is split out to T-P4-4 (ruling 6). The QA fixtures `market.acceptance.test.ts:666` and `digest.acceptance.test.ts:501` are left to qa-engineer (T-P4-5, ruling 7). The uncommitted `market.acceptance.test.ts` in the tree is not this card's change.
- Owned paths: all inside ruling 5. The fixture rewrites (`finance-testkit.ts:356`, `digest.test.ts`) use the real model (same item, second transfer), which matches ADR 0020.

## Optional notes
- `inventory/ledger.ts:187,195`: remove the unused `isReprint` select later (inventory owner). Folding it into the backend-foundation doc-comment follow-up would also work.
- `market/service.test.ts` keeps an unused `reprint` option on `sales()` (the report already says so).
