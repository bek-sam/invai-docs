# Wave 19: the weekly business review digest

- Dates: 2026-09-27 → (wave 18 pushed 2026-09-27)
- Goal (user outcome): every Monday an owner or office user opens InvAI and finds "Your week in review is ready": last week's numbers (equal to the profit page), up to 3 ranked actions with a button each, one win and a Market watch block, in English or Spanish. People who opt in get the same digest by email (locally: Mailpit only), with one-click unsubscribe.
- Spec: `specs/weekly-digest.md` (status ready, AC1–AC33). Scope: `product/scope.md#weekly-digest` (item 17) and `#market-and-digest-fences`. Owner approval: OI-7. Decision: `decisions/0014`. Backlog: B-122..B-126.
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push; only the tech lead pushes after the gate."** Every grant is written below when given.
- Plan reviewed by: product-manager (2026-09-27, approve with 2 changes), architect (2026-09-27, approve with 12 changes). All applied: see "Binding plan-review changes"; the architect's file `reviews/plan-architect.md` is the detailed source for items A1–A12.

## Hard fences (a reviewer blocks any card that crosses one)
- **No real email.** Email goes only to local Mailpit (`SMTP_URL` unset). No production provider, sending domain or DNS (OI-13), no real postal address (OI-12: placeholder), no send to a pilot before OI-12/13/14 are answered.
- **AI summary stays in shadow mode** (built, validated, stored, never shown or sent) until OI-8. Mock model only; no real key.
- Email is opt-in per person; one-click unsubscribe (RFC 8058); no tracking pixel, no open tracking; no promotions or upsells in the digest.
- The digest makes no outside calls; Market watch reads wave 18's stored signals only and inherits the mock visibility rule (spec AC31).
- Recipients chosen by permission (`finance.read`), not role name; plan usage only for `billing.read` (owner, admin; not office).
- Rendered digest text comes only from the spec copy table and computed facts (no promotions by construction; PM plan review).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-19-1 Digest contract | architect | fable | reviewer (opus) + backend-foundation, web-engineer (consumer) | contract | planned |
| T-19-2 Shared analyst queries + `digest_narrative` (shadow) | ai-engineer | opus | reviewer (sonnet) + security-reviewer (injection, PII) | ai, tenancy | planned |
| T-19-3 Digest module: schedule, snapshot, detectors, ranking, templates, deliveries | backend-engineer (digest) | opus | reviewer (sonnet) + backend-foundation (migration), security-reviewer (tenancy), architect (cross-module) | tenancy, migration, data-integrity | planned |
| T-19-4 Email infra: preferences, signed links, unsubscribe, mail headers; + B-133 rate-bucket bug | backend-foundation | fable | reviewer (opus) + security-reviewer (auth-less endpoints, tokens, PII), integrations-engineer (mailer hunk) | auth, pii | planned |
| T-19-5 Web: digest pages, Today card, settings, account toggle, unsubscribe page | web-engineer | sonnet | reviewer (sonnet) + product-designer, qa-engineer (Today is a golden-path screen) | ui | planned |

## Order and ownership
1. **T-19-1** first. QA writes acceptance tests from the cards meanwhile (first pass against the contract).
2. **Stubs day 1:** T-19-2 `src/modules/ai/analyst-queries.ts` (extracted functions, behavior unchanged, assistant tests green) and `generateDigestNarrative` stub; T-19-4 `src/lib/notify.ts` + `src/lib/links.ts` signatures; T-19-3 `src/modules/digest/service.ts` read functions.
3. **T-19-2, T-19-3, T-19-4** in parallel (3 builders + QA = 4 agents).
4. **T-19-5** when T-19-3's router and T-19-4's public routes work.

| Card | Owns (exclusive) |
|---|---|
| T-19-1 | `invai-contracts/src/contract/digest.ts` (new), `src/schemas/digest.ts` (new), `src/contract.ts`, `src/index.ts`, `src/events.ts` + `src/realtime.ts` (`digest.ready` only), `src/contract/tenancy.ts` + `src/schemas/tenancy.ts` (`me.notifications.*` only), `src/schemas/ai.ts` (`digest_narrative` in `CREDIT_KINDS`), `src/roles.ts`/`roles.test.ts` if a permission is added, version 0.7.0, `CHANGELOG.md`, `README.md` rows |
| T-19-2 | `invai-backend/src/modules/ai/analyst-queries.ts` (new), `src/modules/ai/assistant-tools.ts` (switch to the extracted functions only), `src/ai/**` (`digest_narrative` route, prompt, validator, breaker, mock), `invai-backend/evals/digest_narrative/**` (new), `evals/run.ts` (one registration line), `evals/baseline.json` (digest entry) |
| T-19-3 | `invai-backend/src/modules/digest/**` (new; except QA's `*.acceptance.test.ts`), `src/db/schema/digest.ts` (new) + its migration |
| T-19-4 | `invai-backend/src/lib/notify.ts` (new), `src/lib/links.ts` (new), `src/lib/crypto.ts` (signed-token helpers only), `src/api/links.ts` (new public routes) + its mount in `src/api/app.ts`, `src/db/schema/notifications.ts` (new) + its migration, `src/env.ts`/`env.test.ts` (digest switches), `src/modules/tenancy/**` only for the `me.notifications` procedures, `src/api/orpc.ts` (`bucketFor`, B-133) |
| T-19-5 | `invai-web/src/lib/realtime.ts` (one `digest.ready` case), `invai-web/src/routes/_app/digests/**` (new), `src/routes/_app/settings/notifications.tsx` (new), `src/routes/_app/account.tsx`, `src/routes/_app/index.tsx` (Today card only), `src/routes/unsubscribe.tsx` (new, public), `src/components/digest/**` (new), settings nav entry, `src/i18n/en.ts` + `es.ts` (digest keys only) |
| QA | `invai-backend/src/modules/digest/*.acceptance.test.ts`, `invai-web/e2e/digest*.spec.ts`, `invai-docs/build/qa-report.md` |

## Grants (written when given)
- 2026-09-27 T-19-3: one-line registrations in `src/db/schema/index.ts`, `src/api/router.ts`, `src/modules/jobs.ts`. backend-foundation co-reviews.
- 2026-09-27 T-19-4: `invai-backend/src/integrations/vendors/mailer.ts`, only to accept optional extra headers (`List-Unsubscribe`, `List-Unsubscribe-Post`, `Message-ID`) and keep the existing placeholder/PIN-only skip. integrations-engineer co-reviews that hunk.
- 2026-09-27 Migration order (A11): T-19-4 commits `0028_notifications` on day 1; T-19-3 generates `0029_digest` only after that commit is in its tree. Both add a line to `src/db/schema/index.ts`; T-19-4 also gets the `src/db/schema/index.ts` export line.
- 2026-09-27 T-19-4: `src/modules/tenancy/router.ts` `me.notifications` stub in its day-1 commit (A6), so backend typecheck is green after T-19-1 together with T-19-3's `digest` stub.
- 2026-09-27 T-19-2: backend `src/db/schema/ai.ts` `CREDIT_KINDS` gets `digest_narrative` (mirror of the contract; enum text, no migration).

- 2026-09-27 T-19-1 (asked by T-19-2 for AC22): add `ai_summary_breaker` at the end of `ALERT_KINDS` in `invai-contracts/src/schemas/alerts.ts` in 0.7.0 (additive). Until it lands, T-19-2 logs the breaker trip at error level.

## Status at hand-back (2026-09-27, evening)
- Usage limits and stream stalls stopped every wave 19 agent twice. The tech lead has no SendMessage tool in this session, so it can't resume agents with their context; the coordinator asked for no fresh agents, so wave 19 is paused here.
- T-19-1 (architect): uncommitted contract work in `invai-contracts` (`src/schemas/digest.ts` new; `contract.ts`, `events.ts`, `index.ts`, `realtime.ts`, `schemas/ai.ts`, `schemas/tenancy.ts` modified). Not reviewed, not committed. Still to add: `ai_summary_breaker` in `ALERT_KINDS`.
- T-19-2 (ai-engineer): day-1 commit `759f2d4` (analyst-queries extraction, narrative stub); uncommitted in `invai-backend`: `src/ai/models.ts`, `prompts/index.ts`, `providers/mock.ts`, `db/schema/ai.ts`, new `src/ai/validators/digest.ts`.
- QA: first-pass acceptance tests not written yet (nothing on disk).
- T-19-3, T-19-4, T-19-5: not started (wait for T-19-1).
- Nothing of wave 19 is pushed. No processes left running from wave 19 (checked: no listener on 3100–3199 apart from the pre-existing 3142 orphan).

## T-19-2 day-1 interface (landed `759f2d4`)
- `src/modules/ai/analyst-queries.ts`: `comparePeriods`, `adPerformance`, `designInsights`, `fulfillmentHealth`, each `(tx, ctx: Pick<TenantContext, "companyId">, input)`; the caller opens `withTenant`.
- `src/ai/digest-narrative.ts`: `generateDigestNarrative(companyId, {digestId, lang, insights, facts}) -> {status, text?, failedRules?, cents, mode, showable}`; `digestSummaryMode()` is **async** (breaker state in Valkey/DB). Types `NarrativeFact {id, raw, formatted: {en, es}}`, `NarrativeInsight {id, kind, factIds, template?}`.
- AI tests 134/134 and assistant eval 30/30 unchanged after the extraction.

## Agreed interfaces (names fixed here; the architect's plan review may refine signatures)
**Contract (T-19-1):** router key `digest`: `digest.list(Page)` (paginated; `finance.read`), `digest.get({weekKey})` (`finance.read`; plan-usage section only with `billing.read`), `digest.latest() -> {digest: DigestSummary | null, paused: boolean}`, `digest.feedback({digestId, insightId, vote: up|down, reason?: not_relevant|wrong|already_knew})` (idempotent on digest, insight, user; latest wins), `digest.recordClick({digestId, insightId})` (idempotent; first click wins), `digest.settings.get` (with `recipients: [{userId, name, emailOn, deliverable: ok|unverified|placeholder|suppressed}]`) / `digest.settings.set` / `digest.settings.setRecipientEmail({userId, on: false})` and `digest.sendPreview()` (all `org.manage`: owner/admin). Client statuses only `ready | skipped_quiet`; no narrative text field at all in 0.7.0 (only `narrativeStatus`). Per-person email preference keyed by kind: `me.notifications.get() -> {items: [{kind, on, source, updatedAt}]}`, `me.notifications.set({kind, on})` (`org.read`; `NOTIFICATION_KINDS = ["digest"]`). Event `digest.ready` `{digestId, weekKey}` (envelope carries the org). Market watch votes use the existing `market.recommendations.vote`.

**Shared queries (T-19-2 → T-19-3):** `src/modules/ai/analyst-queries.ts`: `comparePeriods`, `adPerformance`, `designInsights`, `fulfillmentHealth` as plain `(tx, ctx, input)` functions returning data (no text), used by both the assistant tools and the digest, so numbers match by construction.
**Narrative (T-19-2 → T-19-3):** `generateDigestNarrative(companyId, { digestId, lang, insights, facts }) -> { status: "ok" | "rejected" | "skipped_budget" | "skipped_off", text?, failedRules?, cents }` plus `digestSummaryMode() -> "off" | "shadow" | "on"` (global, breaker-aware).

**Email infra (T-19-4 → T-19-3):** `src/lib/notify.ts`: `sendUserEmail({ companyId, userId, kind: "digest" | "digest_preview", dedupeKey, messageId, subject, text, html, unsubscribe: true }) -> { status: "sent" | "skipped", reason? }` (skip reasons: `not_member`, `unverified`, `suppressed`, `placeholder`, `sample_workspace`, `opted_out`, `duplicate`; `quiet_hours` is the caller's; `digest_preview` skips only the opt-in check). Durable idempotency in an `email_sends` table (A7). `getEmailPreference(companyId, userId, kind)`, `setEmailPreference(..., {on, source})`. `src/lib/links.ts`: `signLink({ kind: "unsubscribe" | "click", companyId, userId, ref }) -> url` (`${BETTER_AUTH_URL}/l/:token`) and `registerLinkHandler("click", ({companyId, userId, ref}) => Promise<{path} | null>)`. Keys: `dedupeKey = digest:${digestId}:${userId}`, `messageId = <digest.${digestId}.${userId}@<MAIL_FROM domain>>`.

**Digest module (T-19-3 → T-19-5):** router per T-19-1; `digest.ready` published when a digest is stored `ready`.

## Ports, test DBs, Redis DBs
| Who | API port | Test DB | Redis DB |
|---|---|---|---|
| T-19-2 | 3122 | `invai_t19_2` | 11 |
| T-19-3 | 3132 | `invai_t19_3` | 12 |
| T-19-4 | 3143 | `invai_t19_4` | 13 |
| T-19-5 | 3152 | (dev copy) | 14 |
| QA | 3162 | `invai_t19_qa` | 15 |
| Reviewers | 3171–3179 | `invai_t19_rev_<card>` | 10 |
Mailpit UI: http://localhost:8025 (shared; tag test mail subjects with the card id so agents can tell theirs apart).

## Binding plan-review changes (2026-09-27; details in `reviews/plan-architect.md` A1–A12, `reviews/plan-pm.md` P1–P2)
- A1 `me.notifications` keyed by kind (`org.read`). A2 plan usage on `billing.read`; settings and preview on `org.manage`. A3 recipients in `settings.get` + `setRecipientEmail`. A4 client statuses `ready | skipped_quiet`; `latest()` returns `paused`. A5 no narrative text field in 0.7.0; `digest_narrative` credit kind now. A6 two day-1 stubs (T-19-3 `digest` router, T-19-4 `me.notifications`). A7 `email_sends` table owns send idempotency; `digest_deliveries` is the per-recipient outcome. A8 preview bypasses only opt-in; per-user Redis limit `digest:preview:${companyId}:${userId}` 60 s. A9 public link routes as pinned (POST unsubscribe + 24 h Undo; GET only redirects to `WEB_ORIGIN`; same-origin click paths; purpose-bound HMAC key from `BETTER_AUTH_SECRET`; per-IP `links` bucket 60/min; no `PUBLIC_WEB_URL`). A10 T-19-5 owns `invai-web/src/lib/realtime.ts`. A11 migration order 0028 then 0029. A12 T-19-1 row synced.
- P1 a test in T-19-3 asserts every rendered string comes from the template keys + formatted facts (no free text). P2 QA's AC29 scale run is on the gate checklist.

## Integration gate
- [ ] QA scale runs: market AC28 (wave 18) and digest AC29
- [ ] All repos checks; fresh reset, migrate, seed; `run-golden-path` (API, browser, floor)
- [ ] Digest built for the seed shop with frozen/forced week; Today card, digest page en/es, email in Mailpit with List-Unsubscribe headers; one-click POST unsubscribe works
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Retro
- What slipped:
- Lessons added:
