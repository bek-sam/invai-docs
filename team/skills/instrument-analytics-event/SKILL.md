---
name: instrument-analytics-event
description: Add a product analytics event in invai-web or invai-backend from the data-analyst's taxonomy (invai-docs/metrics/events.md) - tenant-tagged, no PII, no marketplace content, named and typed once, tested and seen arriving. Use for "track", "analytics event", "instrument", "funnel", "PostHog", "measure usage", "KPI event".
---

# Instrument an analytics event

An event that exists in the taxonomy first, carries `company_id` and ids only, never a buyer's or seller's personal data or marketplace content, and was seen arriving with the right properties.

## When to use
- A card or metric definition (`define-metric`) needs a user action or system outcome counted: onboarding steps, first sheet built, label batch bought, AI draft approved, time from import to ship.
- Owners: web-engineer (browser events), backend-engineer (server events in its module). data-analyst owns the taxonomy and co-reviews every instrumentation change.

## Current state (verify before starting)
- **Nothing is instrumented yet.** No analytics SDK is in any `package.json`; `invai-docs/tools-stack.md` plans PostHog (with Sentry and Axiom). Research 13 §1 and §3.1 note the gap.
- The taxonomy file `invai-docs/metrics/events.md` does not exist yet (to be created by data-analyst). The web helper `invai-web/src/lib/analytics.ts` and the backend helper `invai-backend/src/lib/analytics.ts` don't exist either (to be created; the backend one belongs to backend-foundation, `src/lib`). Adding an SDK is a new dependency and a new sub-processor: it needs a decision (`record-decision`) and the compliance-officer's sub-processor list, and the owner approves the vendor (`escalate-to-owner`).

## Steps
1. **Taxonomy first.** The event must be in `invai-docs/metrics/events.md` with: name, trigger (exactly when it fires), where (web or server), properties with types and allowed values, the metric it feeds, and the owner. No entry → ask the data-analyst to add it; don't invent names in code.
2. **Name** as `object_action` in past tense, lowercase snake_case (`gang_sheet_built`, `label_batch_bought`, `listing_draft_approved`), matching the taxonomy exactly.
3. **Properties allowed:**
   - `company_id` (UUID) on every event; `user_id` (UUID) or `station_id` for who; never email or name;
   - entity ids (UUIDs), enums, counts, durations, cents, inches, ratios, `channel`, `plan`, `role`, app version, locale;
   - **not allowed:** buyer names, emails, phones, addresses, `buyer_note`, personalization text, order numbers shown to buyers, listing titles or descriptions, design names, free text of any kind, tokens, URLs with query strings.
4. **Marketplace terms:** Etsy's API Terms forbid collecting Etsy data for analytics and connecting it to ad platforms (research 10 §3). Events describe what the **shop did in InvAI** (counts, timings, ids), never marketplace content. No ad pixels in the app.
5. **Server or browser?** Prefer server events for outcomes that must be exact (a sheet built, a label bought): emit from the service after commit (`afterCommit(tx, () => track(...))`) so a rolled-back transaction never counts. Browser events are for UI intent (opened, clicked, dismissed).
6. **One typed helper.** Call the shared `track(name, props)` helper (to be created) whose types come from the taxonomy, so a typo or an unlisted property fails typecheck. It adds `company_id`, app version and environment, and it drops events when analytics isn't configured (the mock pattern: no key, no network call, never an error).
7. **Never block the user.** Tracking is fire-and-forget: no `await` on the request path, errors swallowed and logged once at debug.
8. **Test:** a unit test that the helper is called once with the exact name and properties, and a test that a PII-shaped value (email, phone, address) is rejected or stripped by the helper (reuse `stripPii` from `invai-backend/src/ai/pii.ts` as the pattern, or a strict property allowlist).
9. **See it arrive.** Run the flow locally with the dev analytics project (or the helper's debug log when no key exists) and check the event name, `company_id` and every property. Paste the captured event in the report.
10. **Tell the data-analyst** the event is live and from which version, so the metric definition can start counting.

## Rules (MUST / MUST NOT)
- MUST tag every event with `company_id`; per-tenant queries are how pilot KPIs are cut.
- MUST NOT send PII or marketplace content, even hashed free text.
- MUST NOT use `company_id` as a label on high-volume infrastructure metrics (research 11 §5.2); analytics events and logs are the place for per-tenant views.
- MUST NOT add an analytics vendor, cookie or pixel without the owner's decision.
- MUST keep the app fully working with analytics off.

## Done when
- The event is in `invai-docs/metrics/events.md` and the code uses the typed helper with that exact name.
- Tests for the call and for PII rejection pass; `pnpm typecheck && pnpm lint && pnpm test` pass in the repo touched.
- A captured event with its properties is in the report; data-analyst reviewed it.

## References
- `.claude/agents/data-analyst.md`, `.claude/agents/web-engineer.md` (analytics rule)
- `invai-docs/tools-stack.md` (PostHog planned), `invai-docs/research/13-team-gap-analysis.md` §1, §3.1
- `invai-docs/research/10-marketplace-engineering-rules.md` §3 (Etsy API Terms), R14–R15
- `invai-docs/research/12-security-quality-playbook.md` §4 ("No buyer PII in ... analytics")
- Related: `define-metric`, `weekly-metrics-review`, `scrub-pii-fixture`
