# Review of T-2-1 (round 1)

- Reviewer: security-reviewer on Opus
- Author: backend-engineer (billing) on Opus 5.5
- Verdict: approve

## Threat model (webhooks, payments)
Entry points: `POST /webhooks/stripe` (public, no session — a webhook), `billing.checkout`/`.portal`/
`.changePlan` (`auth: user`, `billing.manage`, tenant from `ctx.companyId`). Worst outcome if broken:
a company gets a paid plan for free (billed elsewhere), or one company's checkout is attributed to
another company's account (cross-tenant plan grant). Both are High-class outcomes if unmitigated.

## Evidence I re-ran
Same worktree/setup as the primary reviewer (`5d80c52`, `invai_test_r21`, symlinked `node_modules`).

| Command | Result |
|---|---|
| `./node_modules/.bin/vitest run` | 273/274 passed; only failure is `rls-coverage` on `two_factors`, from T-2-3's `6ff0890` in the parent chain, not this card's table |
| `grep -n "withSystem(" src/modules/billing/*.ts src/api/webhooks.ts` | `handleStripeEvent` (comment: "a webhook carries no tenant session... billing_webhook_events is written by the system role only"), `expireTrials` (comment: "cross-tenant, so it runs as the system role"), `ensurePlanCatalog`, `purgeBillingWebhookEvents` — every use has a written reason, matches the MUST NOT-without-a-reason rule |
| `grep -n "timingSafeEqual\|constructEvent" src/integrations/billing/webhook.ts` | `Stripe.webhooks.constructEvent` (the SDK's own constant-time HMAC compare); tolerance `300`s (Stripe's default) |
| Live exercise: signed webhooks against port 3291 / `invai_r21_copy` (dropped after) | see below |

- **Raw body, verify-first:** `webhooks.post("/stripe", ...)` reads `c.req.text()` and calls
  `verifyStripeWebhook(body, header)` before anything else touches the payload; a bad or missing
  signature returns 401 with **nothing written** (confirmed live: bad signature → 401, no
  `billing_webhook_events` row).
- **Dedupe race:** the unique index on `stripe_event_id` plus doing the `INSERT ... ON CONFLICT DO
  NOTHING` and the event's effects in **one** transaction closes the race properly — Postgres
  serializes concurrent inserts on the same unique key (the second blocks, then conflicts and returns
  no row → `duplicate`), so there's no window where two deliveries both "win" the dedupe check. This
  is stronger than a check-then-insert pattern. Live-exercised sequential replay: one processed, one
  duplicate, exactly one DB row and one `ai_credit_ledger` row on the pack test.
- **Checkout can't name another company.** `client_reference_id`/`metadata.companyId` are set
  **server-side** in `openCheckout`/`checkout()` from `ctx.companyId` (the authenticated session's own
  company) — never from client input. The web can't pass a company id through `billing.checkout`'s
  input schema at all (`{plan}` or `{pack}` only). On the webhook side, `resolveCompany` first tries
  to match the event to a company by `stripeSubscriptionId`/`stripeCustomerId` already on file, and
  only falls back to the signed event's `companyRef` — itself Stripe-signed, so not attacker-writable
  — and even then requires `companies.type = 'shop'`. A forged `client_reference_id` would have to be
  injected into a *Stripe-signed* event, which the signature check already blocks. No cross-tenant
  path found.
- **RLS / access to `billing_webhook_events`:** tenant policy scopes reads to the caller's own company;
  `INSERT/UPDATE/DELETE` are revoked from `invai_app` in migration 0010, so no request path — not even
  a bug elsewhere — can pre-claim or tamper with a Stripe event id. Verified in `stripe.test.ts`
  ("the app role reads only its own company's events and can't write them": cross-tenant read returns
  empty, an app-role insert attempt `rejects.toThrow()`).
- **Secrets in logs:** grepped `stripe-events.ts`, `service.ts`, `stripe.ts`, `webhook.ts` for
  `log.info`/`log.warn`/`log.error` calls — none include the webhook secret, the Stripe secret key, or
  raw event payloads; `errorData(err)` only surfaces the Stripe error message on failures, and the
  `detail` column stored on `billing_webhook_events` is explicitly capped to short static reason
  strings ("event type not handled", "older than last event", etc. — no interpolated customer data).
  Live-exercised: `grep -i "whsec_\|sk_test\|sk_live"` on the exercise API's log output found nothing.
  `MOCK_STRIPE_WEBHOOK_SECRET` is a well-labeled non-production constant and `stripeWebhookSecret()`
  refuses every Stripe webhook in production when `STRIPE_WEBHOOK_SECRET` is unset — no silent
  fallback to the mock secret in prod.
- **Idempotent side effects:** money/credit-affecting work (`applyPack`'s ledger insert,
  `setPlanAndStatus`'s plan write) happens only inside the same transaction that first claims the
  event id — no double-grant path. No outward provider call happens inside a DB transaction here (the
  design correctly keeps Stripe calls, e.g. `checkout.sessions.create`, outside any transaction, per
  `idempotent-side-effect`); the webhook handler itself makes no outward calls, only DB writes, so the
  "call outside the transaction" rule doesn't apply to it and the simpler single-transaction pattern is
  appropriate and matches the author's stated decision.

## Acceptance criteria (security-relevant subset)
| # | Met? | Evidence |
|---|---|---|
| 2 webhook (sig, dedupe, ordering) | Yes | Live-exercised: bad sig → 401/nothing written; replay → duplicate/one row; older event → ignored, no rollback of newer state |
| Checkout tenant binding | Yes | `ctx.companyId` server-side only; webhook cross-checks against known Stripe ids first |
| 7 packs (idempotent) | Yes | Live-exercised: one ledger row survives a replay |
| Secrets in logs | Yes (none found) | grep across all touched files + live log capture |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan found no weakening in this card's files
- [x] Tenancy (`withTenant`/`withSystem` with written reason on every use, RLS + revoked writes on the
      new table), idempotency (unique key + single-transaction claim), money in cents, no PII in logs
- [x] Decisions recorded where needed

## Optional notes (not blocking)
- No explicit concurrent-request test for the dedupe race (see reviewer's file); the structural fix
  (unique index + single transaction) makes this a low-priority gap, not a finding.
- `billing_webhook_events.detail` is free text written by the handler; today every call site passes a
  static string, but there's no schema-level guard against a future call site interpolating something
  sensitive. Worth a one-line comment reminder if this file grows more event types (non-blocking).
