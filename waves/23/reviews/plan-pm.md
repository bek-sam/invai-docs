# Wave 23 plan review — product-manager

**Verdict: approve with changes**

## Checked
- 5 cards, ≤5 limit met.
- Every source id in the sources line exists in `waves/backlog.md` with a matching status ("open (P2 sweep)" or wave-18/19 finding ids) — no unsourced work.
- Scope: these are web/floor screens and E2E coverage for capabilities wave 22 builds on the backend — the right way to close roadmap criterion 1 ("no contract procedures without a use", "no partial items"): every new procedure from T-22-1 gets a consumer here instead of sitting dead.
- No fence crossed: T-23-4's market/AI polish (mock follow-ups, eval cleanup, stream close, markdown/footer, seasonality math) is all local engine/UI work on existing mock data — no scraping, no cross-tenant aggregation, no new outside source, no automatic price/listing writes. It stays inside the item-16/17 fences.
- Priorities are sensible: floor correctness (T-23-2), i18n/markdown cleanup (T-23-4 parts) and E2E hardening (T-23-5) all serve roadmap criteria 1 and 5.

## Required changes
1. **B-131's spec step needs my change first, not an engineering grant.** `invai-docs/specs/**` is exclusively product-manager-owned (`team/operating-system.md` row 22, row 97); T-23-4 currently reads "ai-engineer (+ backend-engineer market for B-131 by grant)" with product-manager only as a co-reviewer "(B-131 spec step)". That has it backwards: the fix in `specs/market-signals.md` Step 3 is a product-algorithm decision (the seasonality index must be computed from a **detrended** series — SI per month currently is `month mean ÷ all-month mean` over raw, trended data, which is exactly the bug: a rising niche's growth leaks into SI, and then the trend calc's `y / SI` deseasonalization partly cancels the real trend, flattening it). I will write the Step 3 formula change in `invai-docs/specs/market-signals.md` myself before or on day 1 of the card; the card's engineer implements against that text and tests it, and reviews the *implementation* against it, not the wording. When T-23-4's task card is written, its owned paths must not include `invai-docs/specs/**`, and product-manager should be listed as the author of the spec-step change, not as a domain co-reviewer of someone else's edit to it.
2. When the T-23-4 card is written, its "Owns (exclusive)" table (not present yet at the wave-plan level) should list the market-signals engine/tests paths only, and exclude `invai-docs/specs/**` per (1).

## Notes (non-blocking)
- I'll deliver the Step 3 spec text separately from this review so it's ready when T-23-4 starts.
