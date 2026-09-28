---
name: digest-narrative-injection-pattern
description: T-19-2 review pattern - strip-placeholder-then-scan defeats prompt injection via shop-typed facts; mutation-test the explicit tenant filter, not just RLS
metadata:
  type: feedback
---

For an AI route that must let the model see untrusted shop-typed text (design names, campaign
names) but never let that text drive freeform claims: the safe pattern is (1) the model may only
reference that text via a `{{factId}}` placeholder, substituted by code after generation, and
(2) every hard-fail content rule (digits, direction words, promises, PII, ...) runs on the
model's own text with all well-formed placeholders stripped first. This means a hostile value
can only ever appear as a substituted value, never as text judged to be the model's claim — so
injected instructions inside a fact can't "count" toward passing the validator. Seen in
`invai-backend/src/ai/validators/digest.ts` (`ownWords()` strips placeholders before every rule)
and `src/ai/prompts/index.ts` `dataBlock()` (JSON-encodes + escapes `<` so input can't close the
data block or forge a new tag).

**Why:** proves injection resistance structurally instead of relying on the model "just not"
following injected instructions — matches AC20-style acceptance criteria in InvAI's AI cards.

**How to apply:** when reviewing an `ai` + `tenancy`-flagged card that puts shop data in a prompt,
check (a) the untrusted text sits inside a `dataBlock`/similar-escaped block, (b) the validator's
rules run on placeholder-stripped output, not raw output. Also: don't just trust a
"tenant isolation" test that asserts equality/counts — mutation-test the actual `company_id`
filter in the query (comment it out, rerun) to prove it's a real second line of defense on top of
RLS, not decoration. See [[market_ai_tenancy_and_pii]] for the earlier version of this pattern
from T-18-4.
