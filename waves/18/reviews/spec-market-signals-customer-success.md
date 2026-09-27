# Review: specs/market-signals.md — customer-success

Reviewer: customer-success | Date: 2026-09-27 | Verdict: **approve-with-changes**

## Evidence honesty
Honest: "0 shops have asked" is stated plainly, sourced to an inference not a ticket, and the owner override (OI-6, 2026-09-27) is quoted verbatim with its actual guardrails. No inflated demand claim. Good.

## Blocking
1. **Mock outside-market data can drive real, actionable recommendations shown to real pilot shops, with only a small badge as disclosure.** Until OI-9/10/11 land, every outside source (Trends, Pinterest, Amazon, Walmart, Jungle Scout) is a deterministic mock. R2 ("test a higher price") and R4 ("make 1–2 new designs for a rising niche") can fire on that fake data and reach a real shop owner's assistant answer with just a "Sample data" badge (badge.sample) and a source/date line. A busy owner can act on it — spend on new designs, raise prices — believing it's real. A badge is not enough friction for an *actionable* suggestion involving real money. **Fix:** either (a) suppress R2/R4 from firing on mock-only sources for real (non-sample) shops until a real provider is connected, or (b) put the disclosure in the action sentence itself ("Example data — no real market source connected yet") rather than only a badge, reviewed by product-designer/compliance-officer. Owner: PM + ai-engineer (copy/rule change).
2. **Disagreement answers (AC8) are correct but under-explained.** Showing "rising per your own data, falling per the outside mock" without a plain-language reason is honest but confusing to a non-technical owner. Not a wrong answer, but likely to be read as a bug. **Fix:** one added sentence template ("your own sales and outside interest disagree — this happens"), reviewed with write-plain-language-copy. Owner: ai-engineer (copy) / docs-writer (help article).

## Non-blocking
- Census NAICS "all US clothing stores" seasonality prior (Step 3) is disclosed via `get_seasonality`'s source field, but the label itself should say plainly that it's not specific to the shop's niche — worth a copy pass, not a spec blocker.
- Auto-detected "adoption" (price moved ≥3%) can misattribute a coincidental price change to a recommendation; the explicit vote overriding it (Step 7.2) is the right mitigation.
- Success metrics (≥15% tool adoption, ≥50% useful-vote rate with counts under 20) are honestly scoped for 2–3 pilot shops and explicitly revisit at low volume. Feasible.
- No upsell/guarantee language found; "estimate", "test", confidence bands are consistently used, not promises.

## Predicted day-1 tickets
| Ticket | Covered by spec? | Fix | Owner |
|---|---|---|---|
| "Why is my niche wrong / unclassified?" | Yes — niche chip + Change | Help article on mapping + correction | docs-writer |
| "Why can't I compare my price to other Etsy/TikTok/Shopify sellers?" | Yes — `unavailable.price` copy names the fence, no date promised | Macro pre-empting the "when" follow-up, no date given | customer-success |
| "This trend doesn't match what I see myself — is this real?" | Partially — badge only | Stronger in-line disclosure for R2/R4 (see Blocking #1) + help article | PM/ai-engineer, docs-writer |
| "Did this change my price or listing automatically?" | Yes — read-only, AC16 | Reassurance macro for first-time users | customer-success |
| "It shows conflicting info for the same niche" | Yes, but under-explained | Copy fix (see Blocking #2) | ai-engineer, docs-writer |
| "It flagged/dropped an idea and didn't say why" | Partially — logged, not user-facing | Neutral in-app message when trademark screen drops something | PM/ai-engineer |

## Notes
No shop names or PII used. Read-only on specs/code; no code, contract or copy edited by this review.
