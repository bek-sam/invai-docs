# Review: specs/weekly-digest.md — customer-success

Reviewer: customer-success | Date: 2026-09-27 | Verdict: **approve-with-changes**

## Evidence honesty
Honest: "0 shops have asked" is stated plainly with the owner override (OI-7, 2026-09-27) quoted verbatim, including the guardrails the team attached (own spec, opt-in, eval gate, spend cap). The AI summary staying in shadow mode until a real-model eval (OI-8) passes, with the template shown meanwhile, is a good, honest design — no unverified AI text reaches a shop.

## Blocking
1. **The Market watch block inherits market-signals.md's mock-data risk, in a higher-trust, unattended surface.** An assistant chat answer is something the owner asked for; a Monday digest card or email lands unasked, in-app or in an inbox, which invites less scrutiny of the "Sample data" tag than a conversational answer would. The spec correctly keeps R2/R4 (which need outside data) out of the top-3 action slots, but they still show in the Market watch block itself with only "Sample data" text. A shop that skims the digest could still act on a fabricated trend. **Fix:** either hold the Market watch block out of email/digest entirely for real (non-sample) shops until a real outside provider is connected (PM decision, cheap given "0 shops asked" evidence), or give Market watch items a stronger fixed disclosure line than the assistant uses, since this surface has no back-and-forth to catch a misunderstanding. Owner: PM, with ai-engineer for the block's render rule.

## Non-blocking
- The digest's own numbers are protected well: AC1 parity-tests the glance block against the profit page, "incomplete" is flagged when fees aren't final, and D4's "measured by channel, not by ad" note pre-empts one common confusion. Good design, not a spec issue.
- Minimum-volume guards producing "A steady week" instead of noise (AC8) is a reasonable, disclosed tradeoff for small shops, not a defect.
- Unsubscribe design (idempotent one-click POST, GET-never-unsubscribes, signed token bound to shop+person, AC24/25) is solid; low ticket risk expected.
- No upsell/promotion line exists in the digest (explicit fence) — good, avoids the "is this a sales pitch" read.
- Success metrics (≥30% click rate, ≥25% action-taken, both "with counts") are honestly scoped for a handful of pilot shops.

## Predicted day-1 tickets
| Ticket | Covered by spec? | Fix | Owner |
|---|---|---|---|
| "I didn't get the email" | Yes — opt-in is explicit and shown in-app, but expected anyway | Help article + macro on the opt-in step | docs-writer, customer-success |
| "My numbers don't match Etsy/Amazon's own dashboard" | Partially — "incomplete" flag and ad-attribution note exist, no methodology explainer | Help article: what "net profit" and timing mean here vs. the marketplace's own report | docs-writer, data-analyst |
| "It says 'A steady week' but something changed for me" | Yes, by design (volume guard + "Ask the assistant" link) | None required; optional mention in help article | docs-writer |
| "The Market watch item seems made up" | Partially — "Sample data" label only | See Blocking #1 | PM |
| "Unsubscribe link didn't work / I keep getting emails" | Yes — strong technical design | None expected | — |
| "Why does only I (owner) get the AI toggle / why can't office turn email on for others" | Yes — settings model documented (admin can turn off, never on) | Short help article for clarity | docs-writer |

## Notes
No shop names or PII used. Read-only on specs/code; no code, contract or copy edited by this review.
