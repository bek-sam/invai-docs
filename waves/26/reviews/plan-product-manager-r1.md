# Plan review (product-manager, round 1): waves 26 and 27 — AI listing photos

**Verdict: approve**

## Scope
- Scope ref now exists and matches both wave files exactly: `product/scope.md#listing-photos` (item 18), added this round with the design-pixels-never-generated fence, the OI-25 default-off fence, and the "only Shopify gets an API push" fence.
- `product/scope-changes/SCR-008-listing-photos.md` records the owner's chat approval ("implement these all", 2026-10-02) and states plainly this is distinct from SCR-007 (still open, OI-17): SCR-007 invents designs; this feature only photographs a design the shop already uploaded. Decision `0006-v1-cuts.md`'s "AI design generation" cut is untouched.
- `decisions/0022-listing-photos-design-lock.md` records the design-pixels rule both cards' ACs already assumed (T-26-2 AC1 "drawn by code... no downloaded stock images"; T-27-1/T-27-2's provider-never-sees-the-design split). 0023 correctly left for the architect's ADR.
- Both wave files' fences (mocks default, real image gen off, no new paid service turned on, at most 3 agents) match scope item 18 and OI-25 exactly. No scope drift found.

## Acceptance criteria
- `specs/listing-photos.md` is written consistent with the cards as already authored (T-26-1..5, T-27-1..5), not a competing version — I did not find a contradiction between any card's AC and the spec. Where a card is more specific (thresholds, exact shapes), the card governs; the spec states the user-observable behavior.
- Edge cases the cards already cover and the spec now states as Given/When/Then: credits exhausted before render (T-26-4 AC3), approval gate before zip/attach (AC5), missing back print file (T-26-2 AC2), design larger than print area (T-26-2 AC2), imaging-down during a job (T-26-4 AC4), idempotent create and no-double-charge-on-retry (T-26-4 AC4/AC9), tenant isolation and role refusal (T-26-4 AC2/AC5, T-26-5 verification), phase B drift rejection (T-27-2) and daily caps (T-27-1), Shopify push idempotency (T-27-4).
- No card promises something the spec forbids, or vice versa.

## User value
- The phase A flow alone (analyze → choose → generate → approve → zip/attach) is a complete, usable improvement over today's single flat-tee mockup, independent of phase B ever shipping or OI-25 ever being answered. Wave 26 does not depend on wave 27 to deliver value — good sequencing.
- Evidence is honest: `research/16` §2 ranks "mockup creation" as the #1 feature gap against 5 competitors, but 0 pilots have asked; SCR-008 and the spec both say so plainly rather than overstating demand.

## Non-blocking notes (not findings)
- Marketplace preset pixel/format numbers (Shopify/TikTok/Walmart) and the exact Etsy-disclosure-applies-to-which-image question are flagged as open questions in the spec, for compliance-officer's existing co-review slots on T-26-2 and T-27-3 — not blocking the plan.
- Credit values (1 template / 10 scene) are stated everywhere as starting values the owner may change; fine as planned.
