---
name: reprint-fixture-decision-0020
description: How to model a reprint in test fixtures under decision 0020 (isReprint means re-pressed, still a sale) without creating a sibling unit
metadata:
  type: feedback
---

Decision 0020 ([[isReprint-is-re-pressed]], `invai-docs/decisions/0020-is-reprint-means-re-pressed.md`)
retired the old "reprint = extra revenue-0 sibling item/line" fixture model. No product code path
ever inserts such a sibling row; a reprint is the same order item re-pressed (openReprint flips
`order_items.is_reprint` in place and adds a `reprints` row / extra transfer cost).

**Rule for any fixture that needs a reprinted unit:**
- Don't call a `sale()`/`addOrder()` helper with `isReprint: true` to add *new* units on top of an
  existing series — that recreates the sibling-row bug (extra units that were never really sold).
- Either (a) flip `is_reprint = true` on an already-placed item via a direct SQL UPDATE (what I did
  in `market.acceptance.test.ts`'s AC17 fixture: update the 3 units `weeklySales` already put in
  the target week, don't add 3 more), or (b) when the fixture creates one row per sale (like
  `digest.acceptance.test.ts`'s `saleAt`/`finance-testkit.ts`'s `addOrder`), give that single item
  its normal revenue plus an inflated cost bucket (e.g. `transfer: REG.transfer * 2` or
  `costCents: 2_000` instead of `revenueCents: 0`), matching T-P4-1's own fixture fix
  (`finance-testkit.ts`, `digest.test.ts`).

**Why:** a fixture that adds extra units/revenue-0 lines for "the reprint" either breaks unit/yoy
counts once decision 0020's "reprints count as sales" takes effect, or (if left filtered) silently
re-introduces the retired model. The failing-for-the-wrong-reason trap here is subtle: the test can
look like it's "testing reprints" while actually testing an extra unit that was never sold.

**How to apply:** any card that touches `isReprint` test fixtures across modules (finance, digest,
market, orders) — check whether the fixture creates a *new* row/unit for the reprint, and if so,
rewrite it to flip the flag on an existing row or keep real revenue with extra cost.
