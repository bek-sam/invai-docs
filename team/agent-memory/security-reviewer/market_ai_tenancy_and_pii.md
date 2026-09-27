---
name: market_ai_tenancy_and_pii
description: T-18-4 (market assistant tools) review pattern - tenancy proof via "market service never called", PII scope, and the trademark-threshold ambiguity for automated (non-reviewable) paths
metadata:
  type: feedback
---

On T-18-4 (wave 18, market signals assistant tools), useful patterns for the same shape of review
next time:

**Tenancy proof for tool-layer cross-tenant checks:** the strongest assertion isn't just "returns
NOT_FOUND" — it's "the downstream service was never called" (`expect(m.getTrendSignal).not.toHaveBeenCalled()`
after asking about another company's design id). A tool that resolves the id under `companyId` first
and only then calls the service can't leak via a service-layer bug; check the id resolution
(`designById(tx, companyId, id)` filtered by both) happens before any cross-tenant-capable call.

**PII scope for AI tool code:** grep the touched files themselves for PII field names
(`buyerName`, `buyer_note`, `shipTo`, email/address/phone) rather than trusting a report's claim.
Absence of any hit (besides a comment saying so) across `assistant-tools.ts`, `niche.ts`,
`service.ts`, prompts and copy files was sufficient evidence here — these tools only ever touch
design/niche/price metadata, never order or buyer rows.

**Trademark-risk threshold ambiguity for automated paths:** the codebase's graduated model
(`combineRisk`: high ≥60 hard-blocks with no override, medium ≥25 requires a human "reviewed" tick,
low is fine) assumes a human reviewer exists downstream. A fully automated path with no reviewer
(`screenMarketTerms`, called from nightly jobs and assistant tools) can't use the medium gate the
same way, so picking the high-only threshold (60) isn't automatically wrong — check whether the
*actual* exposure (what gets queried externally, what gets echoed to the user) differs between the
two thresholds today. Here it didn't: both the "dropped" and "unknown" fallback paths use fixed,
generic copy that never echoes the raw term, so the ambiguity was a documentation gap, not a live
issue. Don't block on a threshold-number disagreement alone — trace what actually happens on each
side of it first.

**Defense-in-depth worth calling out as a strength (not just "not blocking"):** T-18-4's round-2 fix
applied the missing "Sample data" disclosure inside the *shared* `marketOutput()` helper rather than
patching only the two originally-reported templates, which caught the same gap in two sibling tools
the reviewer hadn't flagged. Worth noting explicitly in a review when an author's fix generalizes
past the reported case — it's a signal the fix addressed the root cause, not just the symptom.
