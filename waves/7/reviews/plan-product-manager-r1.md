# Wave 7 plan review — product-manager, round 1

Verdict: **approve with clarifications applied** (see each card and `wave.md`).

## Scope
All 5 cards map to in-scope items: T-7-1/T-7-2 to item 2 (channel adapters/CSV import) and item 8 (profit), T-7-3 to item 15 (plan limits/billing), T-7-4 to item 1 (Order Hub), T-7-5 to always-in-scope reliability/accessibility. Nothing here is an MVP cut (design generation, direct Amazon/Etsy/TikTok/Walmart APIs, etc.).

**T-7-3 using OI-1's default price while OI-1 is open: this is fine.** OI-1's own "default if no answer" clause and its stated recommendation (option C, with A — $0.10 — as the code default) both already name $0.10 as the code default *while the owner decides between pricing-experiment options*. Building the catalog default now doesn't preempt or reopen OI-1; it implements OI-1's own fallback. Added a requirement to the card: comment the catalog value with `// see OI-1`, not a bare number, and call out in the report that OI-1 stays open (this is a default, not a resolution).

**Cost-model scope boundary:** OI-1 also flags three other `cost_model.py` problems (AI design generation still counted, Scale priced at $1,499 vs. the code's `custom`/uncapped, revenue booked for free pilots). T-7-3's AC only covers the label-fee mismatch. Added a note to the card so this isn't fixed as a drive-by and isn't mistaken for closed once T-7-3 ships.

## Testable acceptance criteria
All 5 cards' ACs are testable as written (fixtures, DB-copy checks, grep proof, axe runs, property tests). Two gaps closed by adding contract stubs to `wave.md` (see architect review for the technical shape):
- T-7-2 AC2 ("refunds reduce profit on their date") had no backing data model that could actually satisfy it — `profit_lines` has one `placedAt` per row, not a dated ledger. Without a refund ledger this AC is untestable as stated (a refund would land in the wrong period). Now backed by the new `refund_events` stub.
- T-7-4 AC3 (staleness) had no field to test against — `NormalizedOrder` carries no channel-side "last modified" timestamp. Now backed by the new `sourceUpdatedAt` stub.

## Hidden dependencies
- T-7-2 cannot safely start until wave 6's T-6-3 (profit UI) merges — it's live, uncommitted, in `modules/finance/service.ts` and `router.ts`, the exact files T-7-2 owns. Added as a hard gate on the card and in `wave.md`, not just the existing "start T-7-2 second" ordering note.
- T-7-4's staleness fix depends on T-7-1 populating the new `sourceUpdatedAt` field per adapter (T-7-1 owns `integrations/channels/**` this wave); T-7-4 only owns the orders-side check. Flagged as a coordination point on both cards.
- T-7-4's ship-by re-import fix is not the one-line diff the card's phrasing suggests — `updateExisting` needs `timeZone`/`processingDays` threaded in to recompute ship-by, not just a changed comparison. Noted on the card so it isn't underscoped at estimate time.

## Cards edited
`T-7-1`, `T-7-2`, `T-7-3`, `T-7-4` (clarifications added); `T-7-5` unchanged (no scope, testability or overlap issues found). Full technical detail (contract stubs, file-level overlaps, sequencing against wave 6) is in `plan-architect-r1.md` and `wave.md` §"Contract stubs (exact)" / §"Clarifications from the plan review".
