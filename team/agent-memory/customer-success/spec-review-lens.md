---
name: spec-review-lens
description: What to check when co-reviewing a PM spec for customer evidence (checklist distilled from wave 18/19 reviews)
metadata:
  type: feedback
---

When co-reviewing a PM spec (customer-success's role per operating-system "Who reviews whom"), check, in order:
1. Is demand evidence stated honestly (0 shops asked vs. inferred vs. owner override)? Specs here are good about this — they quote the owner-inbox answer verbatim rather than paraphrasing it into something stronger.
2. Would a real small/mid/large shop understand "sample data", confidence bands, and "not enough data" answers, or would they act on a labelled-but-still-actionable mock claim? A badge alone is weak disclosure for anything actionable (price changes, new designs, ad spend) — see [[wave-18-19-spec-reviews]].
3. List predicted day-1 tickets explicitly (wrong niche/classification, missing competitor data, numbers not matching the marketplace's own dashboard, "did this change something automatically", email/opt-in confusion) and check each against the spec's copy table — most are already covered by copy, but the help article / macro to *pre-empt* the ticket is usually still unplanned and worth flagging as a fix with an owner (docs-writer for help articles, customer-success for macros).
4. Watch for anything that reads as a guarantee or upsell even if unintended — these specs were clean (explicit "no promises", no upsell fence in weekly-digest).

**Why:** this is the recurring shape of my co-review job on PM specs, distilled after wave 18/19. **How to apply:** reuse this as the review skeleton before reading a new spec end to end; it keeps the review under the ~70-line budget the task usually sets.
