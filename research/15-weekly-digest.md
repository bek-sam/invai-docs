# 15: The weekly business review digest: how to build it

- Author: research agent (general-purpose), 2026-09-27
- For: OI-7 (answered: approved), `product/scope-changes/SCR-002-assistant-weekly-digest.md`
- Guardrails from the owner's answer: its own spec, opt-in/opt-out, an eval gate before any unattended send, a spending cap per tenant.
- Related: `specs/assistant-business-analyst.md` (wave 17), `research/14-market-signals.md` (OI-6, being written in parallel), `decisions/0007-ai-model-policy.md`.

## 0. Summary (the recommendation in one screen)

Build a **hybrid digest: numbers and insight ranking in code, words optionally by the model, with the model never writing a digit.**

1. Every Monday at 07:00 in the shop's own time zone, a job computes a **metrics snapshot** for last week (Mon–Sun, shop time) with the same SQL the wave-17 analyst tools use.
2. Deterministic **detectors** turn the snapshot into candidate insights (change vs last week and vs the trailing 4–8 week median, ad efficiency flags, rising/falling designs, cross-listing gaps, on-time rate, reprints, overdue orders, low stock, disconnected channels). Each insight has an estimated $ impact, a confidence and **one concrete action with a deep link into InvAI**.
3. Code **ranks** them and keeps the **top 3 actions**, plus one "win" and a short "numbers at a glance" block.
4. A **template** renders the whole digest in English and Spanish. This alone is a complete, shippable digest.
5. Optionally, a cheap single model call (no tools, no agent loop) **rewrites the connective text** using placeholders like `{{f.net_change_pct}}` instead of numbers. Code validates the output (schema, only known placeholders, no raw digits, same insights in the same order, no promises, right language). **Any failure → the template text is sent instead**, and the failure is logged.
6. Deliver **in-app always** (a Digest page and a card on Today) and **by email only to people who opted in**, with one-click unsubscribe.
7. Track **clicks into actions, whether the action was taken within 7 days, and thumbs up/down per insight**. Don't trust email opens.

Why not simply re-run the analyst-mode assistant on a timer (what SCR-002 first described)? It costs about 20–40x more per shop per week, its numbers can't be checked mechanically before an unattended send, and its output changes whenever the prompt changes. The hybrid keeps the analyst's *format* (finding → evidence → action → estimated impact) and its *SQL*, but not its loop. A "Ask the assistant about this week" button on the digest hands off to the on-demand assistant when the owner wants depth, paid for by credits the owner chooses to spend.

MVP = steps 1–4 and 6–7 with the template only, plus the model narrative built but running in **shadow mode** (generated, validated, stored, not sent) until the real-key eval (OI-8) passes. Estimated AI cost: **0¢/shop/week for the MVP, about 1–2¢/shop/week with the narrative on Sonnet 5, about 5–9¢ on Opus 5**, versus roughly 45–60¢ for a full agent re-run (arithmetic in section 7).

---

## 1. What exists today (read before designing)

| Piece | Where | What it gives the digest |
|---|---|---|
| Analyst tools | `invai-backend/src/modules/ai/assistant-tools.ts` | `get_profit`, `get_orders_summary`, `compare_periods`, `get_ad_performance`, `get_design_insights`, `get_fulfillment_health`, `get_stock`, `get_channel_performance`, `get_production_status`. Each returns `{data, summary, answer}` where `answer` is already **deterministic, template-written text with numbers**. That is the digest's fallback text for free. Range capped at 400 days (S-33). `incomplete` flags for disconnected channels (spec AC10). |
| Profit engine | `src/modules/finance/profit.ts`, `service.ts` | True profit by channel/design/day, `incomplete` when costs are missing. |
| Today + alerts | `src/modules/today/service.ts`, `jobs.ts`, `alerts` table (`dedupeKey` unique per company) | Real-time alerts already exist (at-risk orders, broken sync, stuck sheets, low stock) on a 5-minute sweep. The digest should **summarize, not duplicate**, these. The sweep pattern (`alertsSweepJob` fans out ids with `withSystem`, then `withTenant` per shop, jobId bucketed) is the template for the digest sweep. |
| Jobs | `src/lib/queues.ts` (`defineJob`, stable `jobId`, `reports` queue, `upsertJobScheduler`) | Scheduling and idempotent job ids. |
| Mail | `src/integrations/vendors/mailer.ts` (`sendMail`, Mailpit locally, skips sample workspaces and PIN-only placeholder addresses), `src/lib/auth-mail.ts` (en/es subject/text/html builders, `escapeHtml`) | Transport and the en/es email pattern to copy. |
| AI gateway | `src/ai/gateway.ts` (`runStructured`, PII scrub, `<data>` isolation), `models.ts` (`ROUTES`, `MODEL_PRICES`, `tokensToCostCents`, `tokensToCredits`), `credits.ts` (ledger, `assertCredits`), `breaker.ts` (daily tenant cap `AI_DAILY_TENANT_CAP_CENTS` = $50, platform cap $500) | A new `digest_narrative` route, cost accounting, credits and the spend breaker. |
| Shop context | `companies.timezone` (default `America/Phoenix`), `users.locale` (`en`/`es`), `CompanySettings` JSON | Time zone for scheduling, language per recipient. |
| Roles | `invai-contracts/src/roles.ts` | `owner`, `admin` and `office` all hold `finance.read` and `ai.assistant.ask`; designers and floor roles don't. |
| Plans | `modules/billing/service.ts` `PLAN_CATALOG` | Monthly AI credits: trial 100, starter 500, growth 2,000, pro 6,000, scale 20,000. |
| Missing | — | No notification preferences, no unsubscribe mechanism, no `List-Unsubscribe` header, no product-email footer with a postal address, no digest tables. |

## 2. How good products do this (findings with sources)

**Shopify: Sidekick Pulse (Winter '26 Edition, Dec 2025).** Sidekick moved from a reactive chatbot to a proactive monitor: Pulse surfaces recommendations on the admin home screen, each with "a clear summary of what's happening, why it matters, and actionable next steps" (e.g. "You're running low on your best-selling product"). It lives **in-app first** (a Pulse card on the home page), not as an email blast, and each item is one finding tied to one action. Separately, merchants can save "Skills" (reusable prompts) for things like monthly performance summaries: the pull version.
Sources: https://www.shopify.com/editions/winter2026, https://www.shopify.com/news/winter-26-edition-merchant, https://www.getmesa.com/blog/shopify-sidekick
Lesson: finding + why + action, surfaced where the merchant already works; the digest is a card and a page before it is an email.

**Google Analytics Intelligence (GA4 insights).** Automated insights are driven by **anomaly detection against a forecast**: the metric's expected value is predicted from history and flagged when the actual falls outside the credible interval; weekly anomalies use a **32-week training window**. Custom insights let users choose conditions and evaluation frequency (hourly/daily/weekly/monthly) and **toggle email notifications per insight**.
Sources: https://support.google.com/analytics/answer/9517187, https://support.google.com/analytics/answer/9443595
Lesson: flag *changes against expectation*, not static totals; let people control which insights email them. We won't have 32 weeks of history for new shops, so we need a small-sample fallback (section 5.3).

**QuickBooks / Intuit Assist.** Surfaces "cash flow hotspots, spending anomalies, and business wins worth celebrating" in a **Business Feed** on the home page, with suggested actions.
Sources: https://quickbooks.intuit.com/r/innovation/intuit-assist-for-quickbooks/, https://fitsmallbusiness.com/intuit-assist-explained/
Lesson: include **wins**, not only problems; the feed is in-app.

**Amazon Seller Central.** Business Reports (sales, traffic, per-ASIN) are the high-level snapshot; reports can be scheduled and emailed daily or weekly; account-health ratings carry personalized recommendations.
Sources: https://sell.amazon.com/blog/amazon-business-reports, https://www.supplykick.com/blog/how-to-use-amazon-reporting-to-your-advantage
Lesson: marketplace sellers already live with weekly numbers and account-health thresholds (late-shipment rate etc.). A digest that restates totals adds little; one that says "your on-time rate on Etsy slipped to X; these N orders are overdue now" adds a lot.

**Etsy.** Stats show visits, orders, conversion and revenue for the last 7 days in-dashboard; Etsy's own guidance is to review stats on a fixed day each week. I found no evidence of a rich Etsy weekly stats email.
Sources: https://help.etsy.com/hc/en-us/articles/115015774268-How-to-Use-Etsy-Stats-for-Your-Shop, https://www.etsy.com/seller-handbook/article/624088232713
Lesson: "once a week, same day" is the habit sellers are told to build; we can make that habit take 2 minutes.

**Stripe.** Reports can be **scheduled** daily/weekly/monthly with an email when ready; the email points back to the dashboard rather than carrying everything.
Source: https://docs.stripe.com/reports/options
Lesson: the email can be short and link to the full in-app page.

**Linear (Inbox digests, Pulse).** Users choose email digest vs immediate; Pulse sends **optional daily or weekly summaries into the in-app Inbox**, with cadence set per user.
Sources: https://linear.app/docs/notifications, https://linear.app/docs/pulse
Lesson: per-user subscription and cadence; the in-app inbox is the primary surface, email secondary.

**Notification fatigue.** Digests exist to batch non-urgent items; urgent items (payment failure, security, SLA breach) should skip the batch and go immediately; give users controls, quiet hours and sensible defaults.
Sources: https://www.suprsend.com/post/notification-batching-and-digest, https://www.courier.com/blog/how-to-reduce-notification-fatigue-7-proven-product-strategies-for-saas, https://www.nngroup.com/videos/alert-fatigue-user-interfaces/
Lesson: InvAI already has the "urgent" path (Today alerts). The digest is the batch path. Don't turn it into a second alert channel.

**LLMs and numbers.** Numeric errors are a common, subtle form of hallucination in data-to-text generation; the reliable pattern is to **compute every number in code and have the model only phrase pre-computed facts** (the "data-to-text" split), which in one study removed hallucinated figures entirely.
Sources: https://arxiv.org/pdf/2202.03629 (survey of hallucination in NLG, numbers section), https://arxiv.org/pdf/2608.19526 (financial summaries with pre-computed features)
Lesson: go one step further than "the model copies numbers verbatim": give it **placeholders, not numbers**, so a wrong number is impossible, and still validate.

**Anomaly detection on small samples.** Robust z-scores (median and MAD × 1.4826) tolerate outliers better than mean/SD; with fewer than ~30 points, plain z-scores are unstable and **domain rules often work better**.
Sources: https://thirdeyedata.ai/data-ai-industry-insights/anomaly-detection-with-robust-zscore, https://mcpanalytics.ai/articles/z-score-anomaly-detection-practical-guide-for-data-driven-decisions
Lesson: rules plus minimum-volume thresholds first; robust z only once a shop has 8+ weeks of history.

**Email law (US, CAN-SPAM).** Messages whose primary purpose is "transactional or relationship" (including **"regular, periodic account balance information"** and account statements) are exempt from most CAN-SPAM rules, but only if the message is **exclusively** that content, or the relationship content comes first and the subject line wouldn't read as an ad. Commercial mail needs a clear opt-out honored within **10 business days**, a valid **physical postal address**, accurate headers and a non-deceptive subject. Penalty: up to **$53,088 per email**.
Sources: https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide-business, https://www.law.cornell.edu/cfr/text/16/316.3
Lesson: keep the digest a pure account report (no upsells, no "upgrade your plan" promos) so it stays relationship content, and **still** include opt-out and a postal address, because it's cheap and one promo line could change the classification. Counsel should confirm (compliance-officer, `legal-doc-draft`).

**Email deliverability (Gmail/Yahoo sender rules).** SPF + DKIM + DMARC with From-domain alignment; spam-complaint rate kept under **0.1%**, never reaching **0.3%**; **one-click unsubscribe (RFC 8058, `List-Unsubscribe` + `List-Unsubscribe-Post`) is required for marketing/promotional mail**, transactional mail is exempt; honor unsubscribes within 48 hours. "Bulk sender" = ~5,000+ messages/day to Gmail.
Sources: https://support.google.com/a/answer/14229414, https://www.captaindns.com/en/blog/gmail-one-click-unsubscribe-rfc8058
Lesson: we'll be far under 5,000/day for a long time, but a recurring email is exactly the kind people mark as spam instead of unsubscribing. Add RFC 8058 one-click anyway, and **send digests from a separate subdomain/stream** so complaints can't hurt password-reset delivery.

**Measuring email.** Apple Mail Privacy Protection preloads images, so **opens are inflated** (15–35% by some estimates) and click-to-open is distorted; **clicks are unaffected** and are the reliable signal.
Sources: https://mailchimp.com/help/apple-privacy-faq/, https://www.beehiiv.com/blog/apple-mpp-open-rate
Lesson: don't put a tracking pixel in; measure clicks into actions and in-app views.

**Scheduling (BullMQ).** Job schedulers accept a cron `pattern` with a `tz`; the docs don't discuss DST; a newly inserted scheduler fires its first repetition immediately (v5.19+).
Source: https://docs.bullmq.io/guide/job-schedulers/repeat-options
Lesson: don't create one scheduler per tenant (thousands of Redis keys, DST edge cases, time-zone edits need upserts). Use **one hourly UTC sweep** that asks Postgres "whose local Monday 07:00 is it?", like the existing alert sweep.

**Cost levers (Anthropic).** Message Batches: 50% off, results within 24 h (usually much sooner), stacks with prompt caching; cache reads cost 10% of input.
Source: https://platform.claude.com/docs/en/build-with-claude/batch-processing (prices already in `src/ai/models.ts`, checked 2026-09-26)
Lesson: a Monday-morning fan-out is a natural batch job, but the latency adds complexity; it's a later optimization, not MVP.

## 3. Design alternatives compared

| Design | How it works | Number accuracy | Usefulness | AI cost / shop / week | Unattended-send risk | Build effort |
|---|---|---|---|---|---|---|
| **A. Pure template** | SQL snapshot → rule detectors → ranked top 3 → fixed en/es sentences | Exact by construction | Good; slightly robotic; no cross-insight synthesis | 0¢ | Lowest; the only risk is a detector bug, testable with unit tests | Medium (detectors are the work) |
| **B. LLM narrative via full agent loop** (re-run analyst mode on a schedule) | Scheduled "Give me a weekly business review" through `runAssistant`, 5–10 tool iterations, Opus 5 high effort | Unverifiable before send; model does arithmetic for "expected impact" | Highest ceiling, most variable | ~45–60¢ (≈90–120 credits: most of a starter plan's 500/month) | Highest: prompt changes silently change every shop's email; can't cross-check numbers mechanically | Low to wire, high to make safe |
| **C. Hybrid (recommended)** | A + one single-shot, tool-less model call that phrases the ranked facts using placeholders; strict validator; template fallback | Exact (numbers inserted by code); validator rejects any raw digit | Best balance: reads naturally, stays on the ranked facts | ~1–2¢ on Sonnet 5 (≈4 credits), ~5–9¢ on Opus 5 low | Low: bad output can't reach a shop; falls back to A | A + ~1 card |
| **D. Real-time alerts instead of weekly** | Push each change when it's detected | Exact | Good for urgent ops (already built as Today alerts); bad for trends (weekly change needs a full week) and causes fatigue | 0¢ | Low | Already exists for ops; trends don't fit |
| **E. In-app only** (no email) | Digest page + Today card, no outbound mail | Same as A/C | Misses the core problem in SCR-002: the owner doesn't remember to open the app | Same as A/C | Lowest (no outbound) | Lowest |

**Recommendation: C, delivered in-app for everyone and by email to opted-in people, with D kept as it is today for urgent items.**
- A is the floor and the fallback; C is A plus words, so building C means building A first.
- B's only advantage (open-ended synthesis) is available *on demand*: the digest's "Ask the assistant about this week" button opens the assistant pre-seeded with the digest's period, spending credits only when the owner asks.
- D and C are complementary: anything urgent stays on the 5-minute alert sweep; the digest recaps "3 alerts this week, 2 resolved" rather than re-alerting.
- E is the MVP's safe first step (ship the page, then turn email on once deliverability and the footer are ready), not the end state.

## 4. The pipeline, step by step

```
hourly sweep (UTC) ──► due shops? ──► digest.build (jobId digest-build-<company>-<week>)
                                         │ 1 snapshot (SQL, withTenant)
                                         │ 2 detect   (pure functions)
                                         │ 3 rank     (pure function)
                                         │ 4 narrative? (gated; else template)  ── validate ── fail → template
                                         │ 5 render en/es, store digest row (status ready)
                                         ▼
                           digest.deliver (jobId digest-deliver-<digest>-<user>-email), one per opted-in user
                                         │ in-app: realtime publish + Today card (no job needed)
                                         ▼
                           feedback: click redirects, thumbs up/down, "acted within 7 days" check
```

### 4.1 Schedule (time-zone aware, quiet hours)
- **One scheduler**: `digest.sweep`, `upsertJobScheduler('digest-sweep', { pattern: '0 5 * * * *', tz: 'UTC' })` on the `reports` queue (5 minutes past each hour, away from the alert sweep's boundaries).
- The sweep selects shops (`companies.type = 'shop'`, not deleted, not a sample workspace, digest enabled) whose **local** time is at or after their send slot (default **Monday 07:00**), computed in Postgres with `now() at time zone companies.timezone`. That handles DST: the hourly sweep simply finds the right UTC hour each week.
- **Catch-up**: if a shop's slot passed (worker down) and no digest exists for that week yet, build it as long as local time is still before 20:00 that day; otherwise build it quietly (in-app only) and skip the email. No email is ever sent between **20:00 and 07:00 shop time** (quiet hours; email isn't interruptive like push, but a 2 a.m. "your week" email looks broken and hurts trust).
- **Week definition**: the last complete ISO week, Monday 00:00 to Monday 00:00 in the shop's time zone. `weekKey` = ISO week of that period, e.g. `2026-W39`. This key is the idempotency key.
- **Late data**: marketplace fees and refunds can land days later (Amazon settlements). Use the profit engine's `incomplete` flag and say "fees for N orders are still estimated" rather than waiting. Don't re-send when late data arrives; the in-app page can show "updated Tue 09:00" if we later choose to recompute (later slice).
- Configurable day/hour per shop (owner/admin). Hour choices 06:00–10:00 only, which keeps sends inside the quiet-hours window by construction.

### 4.2 Compute the metrics snapshot (deterministic)
Run under `withTenant(companyId)` with no LLM. Reuse the analyst tools' SQL by **extracting their query functions out of the `assistantTools()` closure** into plain service functions (e.g. `comparePeriods(tx, ctx, range)`, `adPerformance(...)`, `designInsights(...)`, `fulfillmentHealth(...)`) that both the tools and the digest call. That keeps "the numbers in the digest match the numbers the assistant and the profit page show" true by construction (spec AC1). This is ai-engineer-owned code, so the extraction is its own card or a grant.

Snapshot contents (all money integer cents, percents as `*Pct`, per convention), for last week, the week before, and a trailing window (4 weeks for new shops, up to 8 when history exists):
- Orders, units, revenue, net profit, margin %, AOV; per channel; `incomplete` channels.
- Ads: spend, ROAS, TACoS per channel; flags (spend with negative net; spend up while revenue down).
- Designs: top 5 by net; rising/falling (min 3 units); low-margin (<15%, min 3 units); cross-listing gaps (only for connected channels, spec AC3).
- Fulfillment: on-time rate per channel, late shipments, **overdue open orders right now**, median hours placed→shipped, reprints by reason and cost, refunds.
- Ops: this week's Today alerts opened/resolved; low-stock blanks that feed top designs.
- Account: orders used vs plan cap; AI credits remaining (only shown to owner/admin; see 4.6).
- Data health: channels disconnected or in error during the week.

Store the snapshot as JSON on the digest row (`facts`). Every fact gets a stable id (`revenue.week`, `net.change_pct`, `channel.etsy.ontime_pct`, `design.3.name`), and every number is stored both raw (cents / number) and pre-formatted per locale (`$1,234.56`, `12.5 %` vs `12,5 %` for es if we choose es-MX formatting; keep USD). Formatting happens in code once; the renderer and the narrative only ever reference ids.

### 4.3 Detect changes and anomalies (rules first, statistics when history allows)
Detectors are pure functions `(snapshot) → Insight[]`, each unit-tested with fixtures. An `Insight` is:

```ts
type Insight = {
  key: string;            // stable, e.g. "fulfillment.ontime_drop.etsy" (dedupe + feedback)
  kind: "problem" | "opportunity" | "win" | "data_health";
  severity: 1 | 2 | 3;
  impactCents: number;    // estimated weekly $ at stake, arithmetic stored in `impactBasis`
  impactBasis: string;    // fact ids + formula, e.g. "units.design.7 * net_per_unit.design.7"
  confidence: number;     // 0..1: lower for small samples, incomplete data, channel-level ad attribution
  factIds: string[];      // the evidence
  action: { labelKey: string; href: string }; // deep link into InvAI, e.g. /orders?filter=overdue
};
```

Starter detectors (each with a minimum-volume guard so small shops don't get noise):
1. **Revenue / net change** vs last week and vs trailing median; name the channel contributing most (from `compare_periods` contributions). Trigger: |change| ≥ 15% and ≥ $100.
2. **Margin slip**: margin down ≥ 3 points with ≥ 20 orders; name the cost line that moved most (fees, blanks, labels, ads).
3. **Ads**: spend up while channel revenue down; ROAS below 2 (or below the shop's own trailing median); spend with negative net. Always say attribution is channel-level.
4. **Designs**: rising (push it: make listings on other connected channels), falling, low-margin (review price or blank), cross-listing gap (create a draft listing: deep link into AI listings).
5. **Fulfillment**: on-time rate per channel below 95% or down ≥ 5 points; overdue open orders right now (deep link to the filtered order list); reprint rate spike with top reason.
6. **Stock**: low blanks that top designs need next week.
7. **Data health** (always ranked first when present): a disconnected channel means the digest's numbers are partial; action = reconnect.
8. **Wins**: best week in N weeks, record on-time rate, a design crossing a milestone.

Statistics: when a shop has ≥ 8 weeks of history, add a robust z-score (median, MAD × 1.4826) on weekly revenue, net, orders and on-time rate, and use |z| ≥ 2.5 to raise confidence or add an "unusual" insight. With less history, rules and thresholds only. Keep thresholds in one config object so the PM can tune them from pilot feedback without code archaeology.

### 4.4 Rank insights ("top 3 actions")
- Score = `impactCents × confidence × severityWeight`, with data-health pinned first.
- Suppress repeats: if the same `key` was in last week's digest and the shop voted it down, or it was shown 3 weeks running with no action, demote it (the digest must not nag).
- Keep **at most 3 actions**, 1 win, and a fixed "numbers at a glance" block (revenue, net, margin, orders, on-time, with change vs last week). If nothing crosses a threshold, the digest says "A steady week" and shows only the glance block: still useful, and cheap.
- **Skip rule**: zero orders last week and no open issues → no email (in-app row still written, status `skipped_quiet`). Two consecutive skipped weeks for an active subscriber → one short "we paused your digest until orders resume" line in-app only.

### 4.5 Optional narrative (the only model call) with validation
- New gateway route `digest_narrative` in `ROUTES`: single structured call via `runStructured`, **no tools**, effort `low`, `maxTokens` ~2,000. Start on Opus 5 (policy 0007 default); move to Sonnet 5 or Haiku 4.5 only after the eval shows equal quality (`model-upgrade`), which is the expected outcome for a phrasing task.
- **Input**: the ranked insights and the fact *ids with their formatted values*, inside the gateway's `<data>` isolation (design names and channel names are untrusted text: wave-17 AC8's injection case applies). Shop context (name, time zone, language) after the cached system prefix, like assistant prompt v4.
- **Output schema** (Zod):
  ```ts
  { headline: string, intro: string,
    items: Array<{ insightKey: string, text: string }>,   // same keys, same order as input
    win?: { insightKey: string, text: string }, closing?: string }
  ```
  Texts reference facts only as `{{fact.id}}` placeholders; code substitutes the formatted values.
- **Validator** (every rule is a hard fail):
  1. Schema valid; lengths within limits (headline ≤ 90 chars, each item ≤ 280).
  2. `items[].insightKey` equals the ranked list exactly (no added, dropped or reordered insights).
  3. Every placeholder exists in `facts`; each item only references facts in that insight's `factIds` (so the model can't attach Etsy's number to Amazon's finding).
  4. **No digits** anywhere outside placeholders (regex on `[0-9]`, plus Spanish/English number words like "twelve", "doce" for small counts). This is the numeric cross-check made structural: there is nothing left to cross-check.
  5. Direction words agree with signs: if the item contains "up/rose/increased" or "subió/aumentó" and the referenced change fact is negative (or vice versa), fail. Simplest implementation: direction comes from a placeholder too (`{{net.change_dir}}` → "up"/"down"/"subió"/"bajó"), and the validator bans free direction verbs near change facts.
  6. Banned phrases: promises and guarantees ("will increase", "guaranteed", "garantiza"), outside market claims unless the insight is a market signal (section 9), URLs, email addresses.
  7. Language: output language matches the requested locale (a cheap stop-word check; en vs es).
  8. PII scrub passes (no buyer names; the snapshot has none, but check anyway).
- **Hold and fall back**: on any failure, don't retry (cost, and a retry usually repeats the failure). Use the template text for that digest, set `narrativeStatus = 'rejected'` with the failed rule ids, and emit a metric. The shop never sees a failed narrative.
- **Kill switches** (in order of blast radius): env `DIGEST_ENABLED` (everything), `DIGEST_EMAIL_ENABLED` (outbound only), `DIGEST_NARRATIVE_MODE = off | shadow | on` (global), per-company `digest.narrative` toggle. An automatic breaker flips the global mode to `shadow` if more than 10% of narratives in a 24-hour window are rejected (reuse `breaker.ts`'s Valkey counters and its critical-alert path).
- **Shadow mode**: generate and validate, store alongside the template, deliver the template. The ai-engineer reviews a sample of shadow narratives vs templates weekly. Move to `on` only after the eval gate below passes on the real model.
- **Eval gate** (`evals/digest_narrative/`, run by `evals/run.ts` like the other routes): cases for a normal mid-shop week, a quiet week, a small shop with one channel and no ads (spec AC9), a big drop, a disconnected channel (AC10), Spanish, injection design names (AC8), every insight kind, and a snapshot where two channels have near-identical numbers (to catch cross-attribution). Pass bar: **100% validator pass on mock and real model**, plus a rubric score (clear, actionable, no invented cause) above a threshold the ai-engineer sets. The gate runs in CI on mock; the real-model run needs OI-8's key.

### 4.6 Render en/es and per role
- Render per **(digest, locale)**, not per user: at most two renders (en, es) per shop per week. Language from `users.locale`.
- Content by **permission, not role name** (roles can change): recipients must hold `finance.read`; that's owner, admin and office today. Sections that need other permissions (e.g. plan usage needs `billing.manage`) are dropped for recipients without them. That gives owner/admin the full digest and office the same minus billing, with no role-specific templates to maintain.
- Later: a lighter **"production week"** variant for leads without `finance.read` (on-time rate, reprints, overdue items, no money), because floor leads care about those numbers too.
- Email: plain text + HTML built like `auth-mail.ts` (string templates, `escapeHtml`), max ~600px, no images needed, no tracking pixel. Subject is deterministic from facts, never from the model: "Your week at {shop}: net profit {net} ({change})" / "Tu semana en {shop}: ganancia neta {net} ({change})". No buyer PII in the email; order references use InvAI order numbers only.
- In-app: `/digests` (list by week) and `/digests/:weekKey` (full page with the glance block, top 3 actions with buttons, the win, a "numbers are estimated because…" note when `incomplete`, and "Ask the assistant about this week"). A card on Today on Mondays.

### 4.7 Deliver
- In-app: writing the digest row with `status = 'ready'` publishes a realtime event so open dashboards show the Today card. No per-user job.
- Email: one `digest.deliver` job per opted-in recipient, `jobId = digest-deliver-<digestId>-<userId>-email`. The job inserts the `digest_deliveries` row first (unique key), marks it `sending`, calls `sendMail`, then stores `messageId` and `sent`. A retry that finds `sent` exits. A crash between SMTP accept and `sent` can cause a rare duplicate; SMTP has no read-back, so set a **deterministic `Message-ID`** (`<digest-<digestId>-<userId>@mail.invai...>`) so clients that dedupe on Message-ID (Gmail is widely reported to) collapse it, and accept that residual risk (document it in the card; per rule 8 it's the best available for SMTP).
- `sendMail` already skips sample workspaces and PIN-only placeholder addresses. Add: skip users who aren't active members anymore, unverified emails (`users.emailVerified = false`), and suppressed addresses (hard bounce or complaint, once the production provider reports them).
- Headers: `List-Unsubscribe: <https://…/u/<token>>, <mailto:…>` and `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058). The token is an HMAC (via `lib/crypto.ts`) over `companyId`, `userId` and `kind`, so the unsubscribe endpoint can run `withTenant(companyId)` without a cross-tenant lookup. The POST endpoint is idempotent and needs no login; the GET shows a confirm page (link scanners prefetch GETs; never unsubscribe on GET).
- Footer: why you got this, one-click unsubscribe, "manage in Settings", InvAI's postal address (owner decision: we don't have one on file).
- Sending domain: a digest-specific subdomain or provider stream (e.g. `updates.` vs `accounts.`), SPF/DKIM/DMARC aligned. Production SMTP provider choice is an owner/platform-sre item; locally Mailpit shows everything.

### 4.8 Track feedback and usefulness
- **Clicks**: action buttons go through `/d/c/<deliveryId>/<insightKey>` (HMAC-signed), which records a click and redirects into the app. In-app clicks are events directly.
- **Acted within 7 days**: per insight kind, a cheap check next week (overdue orders from the insight shipped? draft listing created for the cross-listing gap design? channel reconnected?). This is the metric that matters: did the digest change what the shop did.
- **Thumbs up/down per insight**, in-app only (email votes via GET would be triggered by link scanners). An optional reason ("not relevant", "wrong", "already knew"). "Wrong" votes page the ai-engineer/backend owner for review, because a wrong number is a bug.
- **Unsubscribe rate** and spam complaints per send (from the provider), **in-app digest views**.
- Don't rely on opens (Apple MPP). No pixel.
- Events via the data-analyst taxonomy (`instrument-analytics-event`): `digest_built`, `digest_email_sent`, `digest_viewed`, `digest_action_clicked`, `digest_insight_voted`, `digest_unsubscribed`, `digest_narrative_rejected`. Tenant-tagged, no PII.
- Success metric proposal (to formalize with `define-metric`): **weekly share of active subscribers who click at least one action**, and **action-taken rate within 7 days**. Guardrail metrics: unsubscribe rate < 2% per send, spam complaints < 0.1%, narrative rejection rate < 5%, zero "wrong number" reports.

## 5. Data model sketch

All new tables are tenant tables: `company_id` + `tenantPolicy(...)` + `.enableRLS()`, composite `(company_id, id)` foreign keys (S-26), `company_id`-leading indexes (use the `add-tenant-table` playbook; backend-foundation co-reviews the migration).

**Company-level settings** go in `CompanySettings` (JSON, no migration):
```ts
digest?: {
  enabled: boolean;          // default true once the feature ships (in-app only unless people opt in to email)
  sendDow: 1..7;             // default 1 (Monday)
  sendHour: 6..10;           // default 7, shop time zone
  narrative: boolean;        // AI-written summary; default false until the eval gate passes, then true
}
```

**`notification_preferences`** (per user, per company, per kind; the first real preference table, reusable later):
| column | notes |
|---|---|
| `company_id`, `id` | tenant |
| `user_id` | FK users |
| `kind` | `'weekly_digest'` (text enum, extensible) |
| `channel` | `'email'` (in-app is always on) |
| `enabled` | boolean |
| `source` | `'user' \| 'admin' \| 'unsubscribe_link' \| 'bounce' \| 'complaint'` (audit why) |
| `changed_at` | timestamptz |
| unique | `(company_id, user_id, kind, channel)` |

**`digests`** (one per shop per week):
| column | notes |
|---|---|
| `company_id`, `id` | tenant |
| `week_key` | `'2026-W39'`; **unique `(company_id, week_key)`**: the idempotency key |
| `period_from`, `period_to` | timestamptz, shop-local week boundaries |
| `status` | `building \| ready \| skipped_quiet \| failed` |
| `facts` | jsonb snapshot (ids → raw + formatted) |
| `insights` | jsonb ranked list (keys, scores, factIds, action) |
| `render` | jsonb `{ en: {subject, headline, items…}, es: {...} }`, what was actually shown |
| `narrative_status` | `off \| shadow \| valid \| rejected \| skipped_budget` |
| `narrative_shadow` | jsonb, shadow output kept for review (no PII by construction) |
| `validation` | jsonb, failed rule ids |
| `ai_job_id` | FK `ai_jobs` when a model call happened (cost, tokens, model, prompt version live there) |
| `cost_cents`, `credits` | int |
| `incomplete` | boolean, channels flagged |
| timestamps | |

**`digest_deliveries`**:
| column | notes |
|---|---|
| `company_id`, `id`, `digest_id`, `user_id` | tenant; FK `(company_id, digest_id)` |
| `channel` | `'email'` |
| `locale` | `'en' \| 'es'` |
| `status` | `queued \| sending \| sent \| skipped \| failed` (+ `skip_reason`) |
| `message_id` | provider/SMTP id |
| `sent_at`, `first_click_at` | |
| unique | **`(company_id, digest_id, user_id, channel)`** |

**`digest_feedback`**:
| column | notes |
|---|---|
| `company_id`, `id`, `digest_id`, `user_id`, `insight_key` | tenant |
| `event` | `click \| vote_up \| vote_down \| acted` |
| `reason` | nullable text enum |
| unique | `(company_id, digest_id, user_id, insight_key, event)` for votes (upsert: a user can change their vote) |

History for anomaly baselines comes from recomputing past weeks from orders/profit (bounded by the 400-day cap) or from earlier `digests.facts`; no separate metrics table in the MVP.

Job keys: `digest-sweep` (scheduler), `digest-build-<companyId>-<weekKey>`, `digest-deliver-<digestId>-<userId>-email`. Credits charged with `ref = { type: 'digest', id: digestId }` so a re-run can't charge twice (check the ledger for the ref before charging). Add `digest_narrative` to `AI_JOB_KINDS` and `CREDIT_KINDS` (or reuse `assistant`; a separate kind makes `cost-review` easier).

Contract (architect, `invai-contracts`): `digest.list`, `digest.get({weekKey})`, `digest.vote`, `digest.settings.get/update` (owner/admin), `digest.preferences.get/update` (self), `digest.sendTest` (owner/admin, rate-limited), a realtime event `digest.ready`, and a public unsubscribe route outside oRPC (like webhooks). New permission: reuse `finance.read` for reading, `org.settings`-style permission for company settings.

## 6. Settings UI

- **Settings → Notifications** (new `invai-web/src/routes/_app/settings/notifications.tsx`), owner/admin:
  - Weekly business review: on/off for the shop.
  - Day and hour, with the shop's time zone shown ("Mondays at 7:00 a.m., Phoenix time").
  - "Write the summary with AI" on/off, with the plain cost: "about N AI credits a week; if credits run low we send the standard summary." Disabled with an explanation while the global mode is `shadow`.
  - Recipients: members with access to profit numbers, each with their email on/off state (read-only for others' choices except an admin can turn someone *off*, never on: consent stays with the person).
  - "Send me a preview now" (rate-limited, sends to the clicking user only).
- **Account page** (`account.tsx`), every eligible user: "Email me the weekly business review" toggle; language follows the existing locale setting.
- **Opt-in moment**: on the first digest's in-app page and the Today card: "Get this in your inbox every Monday?" with one button. Email is **opt-in per person**; in-app is on for the shop by default. This satisfies the owner's opt-in/opt-out guardrail without a signup flow, and keeps unsolicited email at zero.
- **Unsubscribe landing page** (public): "You won't get the weekly review by email any more. [Undo]" in the user's language.
- **Digest pages**: `/digests`, `/digests/:weekKey` as in 4.6; 390 px, light/dark, en/es (standard `build-dashboard-screen` bar).

## 7. Cost per tenant per week (estimates; real numbers come from the OI-8 eval run)

Prices from `src/ai/models.ts` (cents per million tokens): Opus 5 500 in / 2,500 out, cache read 50; Sonnet 5 200 / 1,000, cache read 20. Credits = 1 per 1,000 billable tokens (`tokensToCredits`).

Assumptions for one narrative call: cached system prompt ~1,500 tokens, facts + insights input ~2,500 tokens, output ~700 tokens per language.

| Option | Arithmetic | Cents / shop / week | Credits / week |
|---|---|---|---|
| Template only (MVP) | no model call; SQL ~100–300 ms; email ~$0.10 per 1,000 on a typical provider | ≈ 0¢ AI, ~0.01¢ email | 0 |
| Hybrid, Sonnet 5, one language | 2,500×200/1M = 0.5¢; 700×1,000/1M = 0.7¢; 1,500 cached ×20/1M ≈ 0.03¢ | **≈ 1.2¢** | ≈ 4 |
| Hybrid, Sonnet 5, en + es in one call | output ~1,400 → 1.4¢ | **≈ 2¢** | ≈ 5 |
| Hybrid, Opus 5 effort low, one language | 2,500×500/1M = 1.25¢; (700 out + ~1,000 thinking)×2,500/1M = 4.25¢ | **≈ 5.5¢** (both languages ≈ 9¢) | ≈ 5–6 |
| Hybrid, Sonnet via Message Batches (later) | 50% off | ≈ 0.6–1¢ | same credits (we may choose to pass the discount on) |
| B: full agent re-run, Opus 5 high | ~5 iterations, ~90k input tokens total (partly cached) ≈ 30–45¢; ~6k output incl. thinking ≈ 15¢ | **≈ 45–60¢** | ≈ 90–120 (18–24% of a starter plan's monthly 500 credits every week) |

At 1,000 shops the hybrid on Sonnet is ~$12–20 a week; on Opus ~$55–90; option B ~$450–600. Per shop per month the hybrid is ~5–40¢, well inside any plan price ($149 starter).

**Cost controls**
1. Skip the model when there's nothing to phrase (quiet week, zero insights) or when nobody on the shop will read it this week (no opted-in email recipient *and* nobody opened last week's in-app digest: template only).
2. Per-tenant weekly cap: `DIGEST_MAX_CENTS_PER_WEEK` (default 10¢). Estimate input tokens before the call (chars ÷ 4); if over, send the template (`narrative_status = 'skipped_budget'`). The existing daily tenant/platform breakers still apply on top.
3. Credits: charge the narrative's credits to the shop (kind `digest_narrative`), but **reserve**: if fewer than 25 credits remain, use the template so the digest never eats the credits the owner wants for listings.
4. Prompt caching: static system prompt first (shared across all shops, so the Monday fan-out gets cache hits within the 5-minute TTL); shop context after it.
5. One call per shop producing both languages only when both are needed; otherwise one.
6. Cheaper model after the eval (`model-upgrade`); batches later.

## 8. Risks and mitigations

| Risk | Mitigation |
|---|---|
| A wrong number reaches a shop's inbox with no human check (SCR-002's main worry) | Numbers only from code; model uses placeholders; validator bans digits; template fallback; "wrong" thumbs-down reviewed within a day; digest numbers built from the same functions as the profit page, with a test asserting digest net = `getProfit` net for the seed week. |
| A wrong *recommendation* (e.g. "cut ads" when attribution is channel-level) | Actions come from detectors, not the model; each action's wording is fixed per detector and reviewed by the PM; ad insights always state channel-level attribution and carry lower confidence; wording is "consider", never "you should". |
| Prompt injection through design/listing names | `<data>` isolation, placeholders mean names are substituted by code into escaped HTML, validator rules 2–3 stop the model adding content; eval injection cases. |
| Prompt or model change silently alters every digest | Eval gate in CI; `prompt_version` stored per digest; shadow mode for any prompt change before `on`; automatic breaker at >10% rejections. |
| Spam complaints hurt all InvAI mail (password resets) | Opt-in email only; one-click unsubscribe; separate sending subdomain/stream; suppress bounces and complaints; pause email globally if complaint rate > 0.1% (`DIGEST_EMAIL_ENABLED`). |
| Legal classification (CAN-SPAM) | Keep content purely account information, relationship content first, no promotions; include opt-out and postal address regardless; compliance-officer drafts, counsel confirms before first real send. |
| Noisy insights for small shops | Minimum-volume thresholds; "steady week" format; repeat suppression; thumbs feedback tunes thresholds. |
| Scheduling bugs (DST, time-zone edits, double sends) | Hourly UTC sweep + Postgres time-zone math; unique `(company_id, week_key)`; unique delivery key; run-twice tests (`idempotent-job`). |
| Late marketplace data makes last week's numbers shift | `incomplete` flags and "estimated" wording; in-app page may recompute later; emails are never re-sent. |
| Cost creep | Cap per tenant per week, credit reserve, skip rules, cheap model, `cost-review` line for `digest_narrative`. |
| Digest duplicates Today alerts and adds fatigue | Digest recaps alert counts; urgent items stay on the 5-minute alert path. |
| Sample/demo workspaces sending real mail | `sendMail` already skips them; test for it. |
| Cross-tenant leak via unsubscribe or click links | HMAC tokens bound to company+user; endpoints scope with `withTenant`; security-reviewer co-review (`threat-model-change`, flags: tenancy, pii, ai). |

## 9. Market signals from OI-6 (`research/14-market-signals.md`)

That research is being written in parallel, so this section is conditional.
- If OI-6 approves a source, add a **"Market watch"** block (max 2 items) *below* the top 3, never mixed into "numbers at a glance".
- Fetch signals **once per week platform-wide** (a single job before the Monday sweep), store them in a platform (non-tenant, public-read) table with source, date and license notes, and match them to each shop by its own designs/tags in code (e.g. a seasonal search term rising that matches tags on the shop's top designs). No per-tenant external calls, so cost is shared.
- A market signal becomes one of the top 3 only when it's tied to the shop's own data (e.g. "a design you sell is in a rising search theme, and it isn't listed on your connected Amazon channel"), and its impact estimate is labelled low-confidence.
- Always label it outside data, with the source name and date. The validator's "no outside market claims" rule is relaxed only inside `market.*` insights, and those numbers are placeholders too.
- If no source is approved or the fetch fails, the block is simply absent; the digest never waits on it.
- Respect the spec's rule: no scraping that breaks marketplace terms.

## 10. MVP slice vs later

**MVP (one wave, ≤ 5 cards; suggested owners)**
1. **Spec + scope** (product-manager): `specs/weekly-digest.md` from this doc, with Given/When/Then acceptance criteria, thresholds table, en/es copy for every detector's action; mark SCR-002 decided.
2. **Contract** (architect): `digest.*` procedures, `digest.ready` event, preference and settings schemas, permission mapping.
3. **Backend digest module** (backend-engineer, new `src/modules/digest`; backend-foundation co-reviews tables; security-reviewer co-reviews): tables, sweep/build/deliver jobs, detectors + ranking + template renderer (en/es), email with List-Unsubscribe and footer, unsubscribe + click endpoints, run-twice tests, digest-vs-profit-page parity test. Needs a small grant to call the extracted analyst query functions.
4. **AI** (ai-engineer): extract analyst-tool query functions into callable services; `digest_narrative` route, validator, eval set; ships with `DIGEST_NARRATIVE_MODE = shadow`.
5. **Web** (web-engineer): `/digests` pages, Today Monday card, Settings → Notifications, account toggle, opt-in prompt, unsubscribe landing page, thumbs.

MVP definition of done includes: a digest built for the demo seed and viewed in the browser in en and es; the email visible in Mailpit with working one-click unsubscribe; build and deliver jobs run twice with one digest and one email; eval gate green on mock.

**Before the first real email to a pilot (owner-inbox items)**
- InvAI postal address for the footer; production email provider and sending subdomain (SPF/DKIM/DMARC); counsel's view on the transactional classification.
- OI-8 real-key eval run including `digest_narrative`, then flip narrative from `shadow` to `on`.

**Later**
- Message Batches for the Monday fan-out (build at 00:30 local, deliver at 07:00, template if the batch isn't back).
- Robust-z anomaly detection once shops have ≥ 8 weeks of history.
- "Production week" variant for leads without `finance.read`; large-shop per-department filtering (SCR-002 notes large shops need this).
- Recompute-and-update of the in-app page when late fees land.
- Market watch block (after OI-6).
- A monthly review variant; Slack/WhatsApp delivery if pilots ask.
- Personal thresholds learned from thumbs feedback.

## 11. Open questions for the PM / owner
1. Default for email: strictly opt-in per person (recommended), or on by default for the owner only with a prominent off switch?
2. Should AI narrative credits count against the plan's allowance, or be included free (the hybrid costs ~1–6¢/week)? Recommendation: count them, with the reserve rule, so costs stay visible in `cost-review`.
3. Monday 07:00 default, or Sunday evening (some owners plan the week on Sunday)? Pilot question for customer-success.
4. Thresholds (15% / $100 change, 95% on-time, 15% margin floor): PM to confirm with the first pilot's real numbers.
