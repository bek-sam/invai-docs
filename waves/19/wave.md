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

## Contract landed (T-19-1)
- `invai-contracts` `e99ac21` (0.7.0): `digest` namespace (9 procedures), `me.notifications.get/set`, event `digest.ready {digestId, weekKey}` (the envelope carries the org, so the card's `companyId` is dropped, as in the Agreed interfaces), `digest_narrative` in `CREDIT_KINDS`, `ai_summary_breaker` in `ALERT_KINDS`. Report `reports/T-19-1.md`. ADR [0016](../../decisions/0016-signed-link-routes-and-notification-preferences.md) covers link routes and kind-keyed preferences.
- Expected breaks until stubs land: backend `src/api/router.ts` (T-19-3) and `src/modules/tenancy/router.ts` (T-19-4).
- 2026-09-27 grant T-19-5: `invai-web/src/routes/_app/index.tsx` `alertKindLabel` case for `ai_summary_breaker` plus `alerts.kind.ai_summary_breaker` in en/es (TS2366 in web typecheck since 0.7.0). T-19-5's first commit.

- 2026-09-27 grant T-19-4: `invai-backend/src/lib/ratelimit.ts` for the per-IP `links` bucket (A9); backend-foundation's own file, not on the card's list.
- T-19-1 approvals: reviewer r1 approve; backend-foundation r1 changes-required (GET wording) → fixed `83eee25` / ADR `9a1a31a` → r2 approve. Web consumer co-review runs as T-19-5's first step.

- T-19-4 built: `0af819a`, `776697b`. Routed to security-reviewer (its file): `src/api/authz.test.ts:129` exact vendor-namespace list needs `me` because `me.notifications` is on `org.read` (contract 0.7.0). Decision noted from T-19-4: `DIGEST_EMAIL_ENABLED` defaults true; the no-real-email fence holds through `SMTP_URL` unset (Mailpit).

- T-19-4 r1: reviewer approve; security changes-required (S-35: a 500 on `/l/:token` logs the token via `app.onError`'s path). Round 2 (backend-foundation): S-35 fix in `links.ts` and path redaction for `/l/*` in `app.ts` `onError`; the per-IP `links` bucket uses the same trusted client-IP helper as sign-in (no raw `x-forwarded-for`); `mailer.ts` stops logging the recipient address (grant extended to that line); **tech lead decision:** `DIGEST_EMAIL_ENABLED` defaults to false when `NODE_ENV=production` (true in dev), so no real digest email can go out before OI-12/13/14 even if `SMTP_URL` is set.

- T-19-4 round 2 `8b9b6f0` (S-35, S-36, S-37 via `src/api/context.ts` `clientIp()` (backend-foundation's own file), production email default off). T-19-3: reviewer approve; T-19-5: reviewer approve; T-19-2: reviewer + security approve.
- Found by the T-19-3 reviewer: a Market watch R1 mock item rendered with an empty `{{channels}}` placeholder (broken sentence). To check at the gate; owner T-19-3 (digest render of market params).
- Process note: the T-19-3 reviewer committed its own review file to invai-docs (`64319df`); harmless (its own file), but prompts say reviewers don't commit.

- 2026-09-28 usage-limit stop. Done before it: T-19-4 round 2 `8b9b6f0`; security's `authz.test.ts` fix `013f3d6`; T-19-5 reviewer approve. Stopped mid-task (the coordinator resumes them with SendMessage): security T-19-4 r2 check (`a5429cf9b51d7f4ef`, worktree `invai-backend-sec4-r2`), security T-19-3 co-review (`aea98521d7e764aa6`, worktree `invai-backend-sec-t19-3`), QA second pass (`a0f871f8eb3026c54`, uncommitted acceptance and e2e edits, its API on 3162 against `invai_t19qa_web`), designer T-19-5 co-review (`aaf9f7b1244bf6d5d`, nothing written).

- 2026-09-28 T-19-5: designer r1 changes-required (D8 win headline never matches the backend's `"D8 win"` key; D3 shows the raw cost-line enum). Round 2 (web-engineer, agent `ab33ca35eea259f04`) also traces the Market watch empty-channel sentence (web fix if web-side; otherwise routed to the T-19-3 owner) and the browser-locale date in `digest-copy.ts`.

- 2026-09-28 T-19-5 round 2 agent `ab33ca35eea259f04` stalled (Docker hang) with uncommitted edits in `invai-web/src/components/digest/digest-copy.ts` and `insight-card.tsx`; next step was the `sourceDateText` language fix. To be resumed by the coordinator.

- 2026-09-28 T-19-3: security co-review approve (7 tables with RLS and composite FKs; `withSystem` only in the due-shop sweep and purge; no PII in facts or logs). Backend-foundation co-review started (agent `a6701ce3e54ff87af`); architect co-review next.

- 2026-09-28 T-19-5 round 2 done: web `87e800d` (D8 win matched on `"D8 win"` with the headline from facts; D3 cost-line names en/es copied from `render.ts`; market dates in the app language). Re-reviews by the reviewer and product-designer pending. Empty-channel sentence is backend (`render.ts:282`, R1 `channels || channel` with an empty channel) → T-19-3 round 2 (agent `a0e3501aa99a68ca9`).

- 2026-09-28 T-19-4 security r2 approve (S-35, S-36 fixed; S-37 partially fixed under S-30). Architect co-review of T-19-3 started (`a5ce76383f11cd914`). Gate precondition: the 16 red digest acceptance tests (fixture clock at Phoenix midnight, etc.) must be green or explained by QA's second pass (`a0f871f8eb3026c54`) or T-19-3 round 2 before the gate.

- 2026-09-28 T-19-3: architect approve (all round-1 approvals in). T-19-4: integrations-engineer approves the mailer hunk; **T-19-4 has all required approvals** (reviewer r1, security r2, integrations). T-19-3 round 2 `cfe1098` (empty-channel sentence). Pending: reviewer r2 on T-19-5 and T-19-3, designer r2 on T-19-5, QA second pass.

- 2026-09-28 T-19-5: product-designer r2 approve (D8 win and D3 cost-line copy verbatim with `render.ts`; T-19-3's `market.channels.connected` fallback matches the web string). Pending: reviewer r2 (T-19-5, T-19-3), QA second pass.

- 2026-09-28 Reviewer r2 approves T-19-5 (`87e800d`) and T-19-3 (`cfe1098`). **All five wave 19 cards now have every required approval.** Gate waits only on QA's second pass (16 red digest acceptance tests).

- 2026-09-28 QA second pass done (backend `53cc86a`, web `1e4d307`, docs `87b5c39`): backend 1068 passed, 2 skipped, 1 todo; web 97 + build. Integration gate started (qa-engineer, agent `a5a58c7cc8a24480d`).

## Link-route rule, clarified (2026-09-27, T-19-1 backend-foundation review)
- `GET /l/:token` never changes a person's email preference or unsubscribe state; only `POST` with `k: unsubscribe` does. For `k: click`, the GET performs exactly one write: it records the click idempotently (first click wins, a repeat is a no-op; same semantics as `digest.recordClick`) and then redirects to a same-origin path. T-19-1 round 2 aligns the README and ADR 0016 wording.

## QA first pass (backend `a50817d`, `bdab237`; web `5df9227`)
- 4 backend acceptance files (digest, digest-market, digest-prod-mode, digest-consent) red for the right reasons; `e2e/digest.spec.ts` marked `test.fail` until built. Report `reports/QA-acceptance.md`.
- Notes for builders: AC17 votes go through `market.recommendations.vote`, not `digest.feedback`. AC13: the backend returns `formatted.en` and `formatted.es` on every fact; the browser picks which to render.

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

## Integration gate (2026-09-28, `reviews/gate.md`)
- [x] QA scale runs: digest AC29, one large shop 330 ms (budget 60 s), sweep of 1,000 shops 15.2 s (budget 30 min), no duplicates; market AC28, 584k orders / 1.17M items: refreshDemand 4.4 s + computeSignals 7.8 s (budget 15 min)
- [x] All repo checks: contracts, backend 1068 tests, web 97 + build, floor + build
- [x] Fresh reset, migrate, seed; API golden path 13/13 (film use 0.83), floor 3/3, full browser `pnpm e2e` in one run 27/28, with no rate-limit failures (B-133 fixed). The one red was QA's own digest.spec selector; fixed and re-run 8/8
- [x] Digest built by the worker's own sweep at 07:05 Phoenix; numbers equal the profit page for the week; one Mailpit email with `List-Unsubscribe` and one-click headers and the placeholder postal address; POST twice = one change, GET = redirect only, Undo works; office has no plan usage, presser refused; AI summary `shadow`, no AI text anywhere
- [x] Key screens looked at by the tech lead (gate-shots 01, 02, 05). Found and filed: stock "before September" on Sep 28 (B-140), English date in the Spanish heading and relative-percent copy (B-141)
- [x] Pushed to `main` 2026-09-28: invai-contracts `83eee25` (0.7.0), invai-backend `5a443ed`, invai-web `49b22c9`, invai-docs (this commit's parent chain); invai-floor unchanged (`68b9cbb`)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
| Primary reviewer r1: 5 of 5. All required reviewers r1: 1 of 5 (T-19-2). T-19-1 (backend-foundation, doc wording), T-19-3 (the reviewer found a live empty-channel sentence, fixed in r2), T-19-4 (security S-35 token in log), T-19-5 (designer: D8 win never matched, D3 raw enum) each took a second round | not planted (OI-15 open) | 0 escaped from approved cards so far; gate found 3 Low/Medium copy issues (B-140, B-141), 1 of them a known wave 18 issue now reaching the digest | 0 | about 15 h wall clock including four usage-limit stops and a Docker hang | builders about 330k–470k per card; reviews 110k–240k; gate about 1 run |

## Retro
- **What worked:** the plan reviews pinned the interfaces (A1–A12), so the three backend cards built in parallel against stubs with no mid-wave contract change. Co-reviews caught real problems the primary reviewer passed: a token written to logs on error (S-35), recipient email addresses in the mailer log (S-36), a spoofable IP header on a public route (S-37), and a win headline that could never match the backend's key. B-133 (rate limit) was fixed inside the wave and the full browser suite now passes in one run.
- **What slipped:** four usage-limit stops and a Docker hang that looked like model stalls; the tech lead had no SendMessage, so the coordinator resumed agents. Several copy defects reached the gate (dates in the browser language, relative percents, a past act-by date) because no card or reviewer checked the rendered digest against real calendar dates.
- **Lessons:** Docker hang check first when agents stall (added); reviewers should compare rendered copy with the wire values across repos (both round-2 fixes were cross-repo key mismatches); a digest or market card's acceptance criteria should include "run with today's date" checks.
