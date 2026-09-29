# Review: T-21-4 Help center en/es and runbook fixes — compliance-officer r1

Co-reviewer scope only: public claims and legal text in `invai-docs/help/{en,es}/**`. Not re-reviewing
plain-language, i18n mechanics or the runbook (docs-writer's card, product-designer's lane) except where
they touch a claim.

## Verdict: **approve** (no blocking findings)

## What I checked and evidence

**1. No promises of security, compliance, guarantees, delivery times or marketplace approval.**
- Ran `grep -rniE "guarantee|secure|security|compliant|compliance|encrypt|certified|SOC ?2|PCI|GDPR|CCPA|approved by (etsy|amazon|shopify)|will (arrive|ship|deliver)|delivery (time|date)|within [0-9]+ (hour|day)|100% |always (works|correct)|never (fails|down)|SLA|uptime"` over `en/*.md` and the Spanish equivalent over `es/*.md`.
- Only hits: "compliance review" / "revisión de cumplimiento" in `ai-listings-and-trademark-check.md` — this names the in-app **Record review** workflow (a UI feature), not a claim that InvAI itself is legally compliant. Not a violation.
- No dollar guarantees, no ship-by/delivery-time promises (`getting-started.md`, `receiving.md` use "arrive" only to describe when orders/boxes physically show up, not a promise), no "approved by Etsy/Amazon/Shopify" language anywhere.

**2. AI listings and trademark article vs. the real gate.**
- Code: `invai-backend/src/modules/ai/trademark.ts:61` — `riskScore >= 60 ? "high" : riskScore >= 25 ? "medium" : "low"`; `:194` high always throws with **no override**; `:201` medium throws **unless a review is on record**. `src/modules/ai/service.ts:685-688` — `recordTrademarkReview` only accepts `riskLevel === "medium"`.
- Article (`en/ai-listings-and-trademark-check.md` and `es/`) states exactly this: high risk "cannot be approved, published or exported until the flagged text is changed... no override for high risk"; medium risk "a recorded compliance review is required" via **Record review**. Matches the gate precisely, both languages.
- Etsy AI disclosure: the disclosure text is appended automatically by the system (`invai-backend/src/ai/validators/listing.ts:336` "Append the AI-use and production-partner disclosures (always; Etsy requires them)") — it is not a user action, so the article correctly says nothing about the user needing to add a disclosure, and doesn't claim AI-written copy alone triggers Etsy's rule. No inconsistency with the rule (disclosure is about the item/design, handled server-side).

**3. Weekly digest article vs. opt-in and one-click unsubscribe.**
- Code: `invai-backend/src/modules/digest/digest-consent.acceptance.test.ts` — `getEmailPreference` starts `on: false` ("opt-in default (spec, open question 1)"); email only sends after `setEmailPreference(..., { on: true })`.
- Article: "It's opt-in by email; it always shows up in-app... either way" and a dedicated **Opt in** section — matches the default-off/opt-in behavior.
- Unsubscribe: article says "Click Unsubscribe at the bottom of the weekly email — no sign-in needed." Code uses a signed token link (`signLink({ kind: "unsubscribe", ... })`, `src/api/links.test.ts`), consistent with a one-click, no-auth unsubscribe. Matches.

**4. Plans and billing article — no prices.**
- Read `en/plans-and-billing.md` and `es/plans-and-billing.md` in full. All amounts are placeholders (`{{plan}}`, `{{n}} credits`) — no dollar figures, no specific plan tiers or numeric limits stated. Matches "owner decides" pricing rule.
- Note (non-blocking): the "Known gaps" section of the report flags a `billing.stub` in-app string ("Payments are not connected yet...") as something it considered documenting — it is **not** actually present in the shipped article (`grep` confirms no match). Nothing to fix; flagging only so the note in the report isn't mistaken for something still open.

**5. Privacy statements vs. legal drafts (`invai-docs/legal/{,es/}{privacy,dpa,terms,subprocessors}.md`).**
- `grep -rliE "privacy|buyer.{0,15}(data|information|pii)|processor|controller|sub-?processor|GDPR|retain|delete.{0,20}data"` over `help/en/*.md` returns **no files**. The help center makes no privacy, data-retention, processor/controller or sub-processor claims at all, so there is nothing that could conflict with the legal drafts. This is a safe (if minimal) position — no finding either way.

**6. Spot checks.**
- `combineRisk` thresholds (60/25) and the no-override rule were re-derived from `trademark.ts` and `service.ts` directly, not taken from the report's word.
- Confirmed independently (not just trusting the report) that no internal words (tenant, RLS, queue, webhook, mock, payload, outbox, oRPC, BullMQ, drizzle) appear in either language: `grep -rnoiE '\b(tenant|company_id|RLS|queue[sd]?|cola[s]?|webhook[s]?|mock(s|ed)?|payload[s]?|outbox|oRPC|BullMQ|drizzle)\b' en/*.md es/*.md` → no output.

## Known gaps (not blocking this review)
- No screenshots exist yet behind the `![...](../img/<slug>/...)` references (report's own gap, owned by whoever next has a running stack — not a compliance issue).
- Help center has zero privacy/data-handling content; if a future article adds any (e.g. in a "your data" or security-focused article), it must be checked against `invai-docs/legal/privacy.md` and `dpa.md` at that time — flagging as a forward-looking note only.

Reviewed by: compliance-officer (Sonnet 5), 2026-09-29. Files read: `waves/21/T-21-4.md`, `waves/21/reports/T-21-4.md`, all 14 articles + index in `help/en/` and `help/es/`, `invai-backend/src/modules/ai/trademark.ts`, `src/modules/ai/service.ts`, `src/ai/validators/listing.ts`, `src/modules/digest/digest-consent.acceptance.test.ts`, `src/db/schema/digest.ts`, `invai-docs/legal/**`.
