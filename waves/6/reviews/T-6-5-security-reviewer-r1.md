# Review of T-6-5 (round 1) — security-reviewer co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-foundation + integrations-engineer on Opus
- Verdict: **escalate**

Risk flags: payments, tenancy. This co-review uses `threat-model-change`'s lens on top of the
`independent-review` verdict in `T-6-5-reviewer-r1.md` (same evidence run once, not duplicated
here — see that file for the full command table).

## 1. What changes
Every real-provider adapter factory (carrier, marketplace/channel, billing, supplier, mail) now
requires a company scope and returns/does the mock/no-op when that company is a sample workspace.
`isDemoCompany()` (`companies.demo`) is replaced by `isSampleWorkspace()`
(`demoOwnerUserId IS NOT NULL` or `settings.demoRetiredAt`). Stripe checkout/portal/plan-change
throw `DEMO_MODE`. No new tables, no new webhooks, no new public endpoints.

## 2. Entry points (the money- and mail-relevant ones)
| Entry point | Who can call it | Tenant comes from | Guard |
|---|---|---|---|
| `billing.checkout`/`.portal`/`.requestPlanChange` | user, `billing.manage`-shaped | session `ctx.companyId` | `assertNotSampleWorkspace` before any provider call (`billing/service.ts:452,478,500`) |
| `shipping.rates`/`.buy`/`.void`, settings | user, `shipping.manage` | session | `carrierAdapter(ctx)` — mock for a sample company, checked live on every call, no cache of the decision to buy |
| Channel sync/webhook/publish (`channels.sync`, webhook handler, `ai.listings.publish`) | job, webhook (tenant from the matched connection, not the payload), user | connection row's `companyId`, never the webhook body | `getChannelAdapter(kind, provider, scope)` re-checks live; `webhookAdapter` is verify/parse-only, no store call possible from it |
| Vendor invite / sheet delivery | user, `team.manage`/`production` | session | `sendMail(mail, {companyId})` — sample workspace gets `skipped:sample-workspace`, no SMTP call |
| Auth notices (verify-email, reset, security) | Better Auth hook, no company | user only | intentionally ungated (`sendMail(mail, "account")`) — see §4 threat 9 |

All inputs on these paths are Zod-validated by the existing contract; nothing new here is
attacker-controlled beyond what already existed.

## 3. Data touched
No new PII. `settings.demoRetiredAt`/`demoSeededAt` are timestamps on the existing `companies.settings`
jsonb, not sensitive. No new logging of anything user-identifying beyond `mail.subject`
(`log.info("mail skipped: sample workspace", { subject })`) — acceptable, matches existing
`skipped:pin-only` logging style.

## 4. Threats
| # | Threat | This change | Control (file:line) | Gap? | Test |
|---|---|---|---|---|---|
| 1 | Cross-tenant read | n/a — guard reads the caller's own `companyId` from session/connection, never another tenant's | — | none | — |
| 8 | Abuse without limits / real money from a sample workspace | the card's whole point | every adapter factory (see reviewer file's grep) | **AI spend** (Anthropic calls from a sample workspace still use the platform key — flagged by the author as a known gap, out of this card's AC) and **blank-supplier ordering** (closed anyway, see §6) | `demo-guards.test.ts`, all 10 tests, spy+behavioral |
| 9 | Fail-open | Redis/DB unreachable during a guard check | `isSampleWorkspace` does a DB read with no timeout/catch of its own — an error here **throws**, not fail-open, because the caller (e.g. `checkout`) is inside a request that would then 500 rather than silently proceed live. Correct default (fail closed), not explicitly tested but matches the codebase's general pattern of not catching DB errors in request paths. | none blocking | — |
| 10 | Double side effect | Stripe checkout/portal/label buy hit twice | unrelated to this card (idempotency of the underlying calls is pre-existing); this card only adds a guard *before* those calls, doesn't change their idempotency | none | — |

Everything else in the template (2–7) is not applicable: no new webhook signature surface, no new
foreign-id/S3-key input, no new injection surface, no new AI prompt path (the AI-spend gap is a
gap in what's *not* built, not a new attack surface).

## 5. Worst outcome
Before this change: any sample workspace with a live key configured for carrier, marketplace,
billing or supplier providers could place a real order, buy a real label, or charge a real card —
one shop's sample data causing real-world spend and possibly a real email to a real customer or
vendor. After this change, that path is closed for carrier, marketplace, billing and mail, verified
by spy/reference-equality tests that fail on the pre-change code. The one path knowingly left open
(by the card's own AC and the author's report) is **AI credit spend from a sample workspace**,
which is real money but bounded by whatever the platform Anthropic key's usage limits are — not a
per-shop blast radius, a platform-wide one if abused at scale. That's a backlog item, correctly
flagged, not a regression.

## 6. Decisions and follow-ups
- **Required before this can be approved as-is:** the supplier guard
  (`integrations/suppliers/index.ts`, `modules/inventory/service.ts`) was built without the
  `scope-change-request` the card's own AC2 and both plan reviews (architect, PM) explicitly
  called for. I agree with the *outcome* — it closes a real gap in the same risk class as the
  carrier/marketplace guards this card exists to build, and it's well-tested
  (`demo-guards.test.ts:222-260`, proves mock-even-with-own-keys-and-in-production) — but the
  process was skipped, and on a payments/tenancy-flagged card that's not a nit. **Escalating to
  the tech lead/owner for a retroactive scope decision**, not requesting a revert: undoing a
  correct security fix to satisfy ownership process would itself weaken a control, which the
  review skill treats as its own escalation trigger.
- **Accepted as reasonable, not a finding:** auth notices always sending regardless of demo status
  (verify-email/reset/security). The author's reasoning holds — Better Auth's hook only has a user,
  a sample-workspace user always also has a real company (`demo.start` requires one), and gating
  password reset for a real user because they also happen to have a sample workspace open would be
  a worse outcome than the mail this sends. No change requested.
- **New finding for `security/v1-review.md` (owner to assign an id):** AI spend from a sample
  workspace is unguarded — Anthropic calls (listing drafts, assistant) use the platform key
  regardless of demo status. Severity: medium (platform-wide cost exposure, not cross-tenant, not a
  data leak, and explicitly out of this card's AC). Owner: backlog, per the author's report.
