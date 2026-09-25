# Report: T-2-1 Stripe billing (backend)
Author: backend-engineer (billing) on Opus 5.5

Commits (invai-backend, `main`, not pushed):
- `fadfa26`: schema and migrations (`0009_billing_stripe`, `0010_billing_webhook_events_system_writes`)
- `5d80c52`: adapters, service, webhook route, jobs, limits and tests

## Intake
- Card: T-2-1. Scope ref: `product/scope.md#mvp-in` item 15.
- Owned paths:
  - `modules/billing/**`
  - `integrations/billing/**`
  - `api/webhooks.ts` (the Stripe route only)
  - `db/schema/billing.ts` and its migrations
  - the `assertWithinPlan` calls in `tenancy/service.ts` and `channels/service.ts`
- Risk flags and co-reviewers:
  - payments and webhooks: security-reviewer
  - migration: backend-foundation
  - contract use: architect

## Built
- **Schema** (`db/schema/billing.ts`):
  - A new `billing_webhook_events` table: unique on `stripe_event_id`, nullable `company_id` with a tenant policy, RLS on. `INSERT/UPDATE/DELETE` are revoked from `invai_app` in migration 0010, following decision 0009's pattern. `webhook_deliveries` and `CHANNELS` are untouched.
  - `subscriptions` gains `cancel_at_period_end` and `stripe_event_at`.
  - `SUBSCRIPTION_STATUSES` gains `trial_expired`. It's a TS-only enum, so there's no check constraint to change.
- **Adapters** (`integrations/billing/`):
  - `stripe.ts`: the live provider on the `stripe` 22.6.2 SDK. It has a 10 s timeout, 2 network retries, and an injectable `fetch` for tests.
  - `mock.ts`: local URLs back to `/settings/billing`, no network.
  - `webhook.ts`: `constructEvent` with a 5-minute tolerance, then normalization into a `BillingEvent`. Services never see Stripe types.
  - Prices are addressed by lookup key: `invai_plan_<plan>` and `invai_pack_<pack>`.
  - The Stripe API version is 2026-08-26.dahlia, where `current_period_*` lives on subscription items and an invoice's subscription is `invoice.parent.subscription_details`. I checked both in `node_modules/stripe/esm/resources/*.d.ts`.
- **`billing.checkout`**:
  - Subscription mode for `starter`, `growth` and `pro`; payment mode for packs.
  - Sends `client_reference_id` = company id, plus metadata on the session and the subscription.
  - Never changes the plan.
  - `trial` and `scale` get BAD_REQUEST. So does an unknown pack key (AC 10).
  - An existing live subscription gets CONFLICT, which prevents double billing.
- **`billing.portal`**: returns the Stripe customer portal URL. With live Stripe and no customer, it returns BAD_REQUEST.
- **`POST /webhooks/stripe`** (its own Hono route, registered before `/:channel`):
  - It verifies the signature first; a bad or stale signature gets 401 and nothing is written.
  - It inserts the event id and applies the event in **one** `withSystem` transaction. A replay gets 200 with `duplicate:true` and changes nothing. A failure rolls both back and answers 500, so Stripe retries.
  - Handled events:
    - `checkout.session.completed` (subscription or pack)
    - `customer.subscription.created`, `.updated` and `.deleted`
    - `invoice.paid` and `invoice.payment_failed`
  - Out of order: any event older than `subscriptions.stripe_event_at` is recorded as `ignored`.
  - A deletion of a subscription that isn't the company's current one is ignored.
  - Events for no InvAI company get 200 and are recorded as `ignored`.
  - Packs write one `ai_credit_ledger` row with kind `pack`, `ref_type = billing_webhook_event` and `ref_id` = the event row id.
- **`changePlan`**:
  - Mock Stripe: unchanged from today.
  - Live, to free with a paying subscription: Stripe `cancel_at_period_end`.
  - Live, to free with no subscription: the plan drops now and the trial isn't restarted.
  - Live, paid plan: PAYMENT_REQUIRED with a checkout URL.
- **Trial expiry**:
  - `getStatus` reports an effective `trial_expired` as soon as `trialEndsAt` passes with no Stripe subscription.
  - The nightly `billing.expireTrials` job (05:15 UTC) writes it and audits each company.
  - `assertPaidActionAllowed` throws PAYMENT_REQUIRED, and `assertWithinPlan("orders")` calls it, so imports are blocked.
  - Floor actions and reads are not gated.
- **Limits**:
  - `maxUsers` is checked on invite. Active members plus pending, unexpired invites count; re-inviting the same email doesn't take a second seat.
  - `maxConnections` is checked on connect: new CSV or API connections, and new or reconnected Shopify installs.
  - Vendor orgs have no limits.
  - `sheetsBuilt` is recorded by `billing.recordSheetBuilt` on `sheet.built`.
- `getStatus` now also returns `currentPeriodEnd` and `cancelAtPeriodEnd`. `paymentsEnabled` is true only with live Stripe.
- Housekeeping: a nightly purge of events older than 30 days. The handler also refuses events older than 29 days, so a purged id can't be replayed.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 checkout | Yes | stripe.test "creates a subscription Checkout session…": mode, client_reference_id, price from lookup key, plan unchanged. Exercise step 2 |
| 2 webhook | Yes | stripe.test: bad, missing, stale and wrong-secret signatures → 401 with no row; each event type; replay; out-of-order; rollback → 500 then retry applies. Exercise steps 5–8 |
| 3 portal | Yes | stripe.test "portal needs a Stripe customer" |
| 4 changePlan | Yes | stripe.test: PAYMENT_REQUIRED with a checkout URL; cancel at period end; free downgrade; mock still applies. Exercise step 10 |
| 5 trial expiry | Yes for imports; label buys **pending T-2-5** | limits.test "trial expiry" (3 tests). Exercise steps 11–13: CSV import → 402 PAYMENT_REQUIRED, GET /orders → 200 |
| 6 limits and sheetsBuilt | Yes | limits.test users (used 3/limit 3), connections (2/2), vendor exempt, sheetsBuilt. Live: invite and connect → 402 PLAN_LIMIT_REACHED |
| 7 packs | Yes | stripe.test replay: 1 ledger row; unpaid or unknown pack → none. Exercise step 9: 1 row after a replay |
| 8 paymentsEnabled | Yes | stripe.test "getStatus reports paymentsEnabled only when Stripe is live" |
| 9 tests | Yes | `stripe.test.ts` (19 tests, real SDK with a mocked fetch) and `limits.test.ts` (12 tests) |
| 10 pack keys | Yes | `credits_500` and `credits_2000` only; anything else → BAD_REQUEST |

Mutation check: with the stale check disabled, the out-of-order test fails; with dedupe disabled, the replay test fails.

## Checks I ran
My test DB was `invai_test_t21`.

| Command | Result |
|---|---|
| `pnpm typecheck` (working tree, and a clean `git archive HEAD` export) | exit 0 |
| `pnpm lint` / `biome check .` | no fixes needed |
| `pnpm test` (HEAD export) | 273 passed, **1 failed: `rls-coverage` → `two_factors`**. That table comes from T-2-3's commit `6ff0890`, not from me. My `billing_webhook_events` passes the coverage test |
| `pnpm vitest run src/modules/billing` | 31 passed (run twice, stable) |
| `pnpm build` (tsup) | Build success |

## Exercised for real
Setup: API on port 3210, run with `tsx` without watch, mock Stripe, against the DB copy `invai_t21_copy`. Output is in `/tmp/t21-exercise.out`.

1. As owner, `GET /billing` → growth/active, `paymentsEnabled:false`.
2. `POST /billing/checkout {plan:pro}` → 200 with a local mock URL. The plan is still growth.
3. `{pack:credits_500}` → 200. `{pack:bogus}` → 400 "Unknown credit pack".
4. `office@` → 403 FORBIDDEN (`billing.manage`). The portal (mock) → 200.
5. A signed `customer.subscription.updated` (active, pro) → 200 processed. The status shows pro/active with `currentPeriodEnd` set.
6. The same event again → 200 `duplicate:true`.
7. A bad signature → 401.
8. An older `past_due`/starter event → 200 ignored. The status stays pro/active, and the row reads "older than last event".
9. A pack webhook, then its replay → processed, then duplicate. `ai_credit_ledger` has exactly one row: `pack|500|billing_webhook_event`.
10. `changePlan growth` with mock Stripe → applies at once (demo behaviour).
11. With the trial forced past its end → `status: trial_expired`.
12. CSV import → **402 PAYMENT_REQUIRED** "Your free trial has ended. Choose a plan to keep going." `GET /orders` → 200.
13. On the trial plan, invite → 402 PLAN_LIMIT_REACHED `{meter:users, used:8, limit:3}`, and connect → 402 `{meter:connections, used:4, limit:2}`.

## Decisions
- **Inline webhook processing, not the queue.** The work is a few row updates. Recording the event and applying it in one transaction gives exactly-once without a job, and a failure answers 500 so Stripe retries. `withSystem` is used with the reason written in code: there's no tenant session, and the event table is system-write-only.
- **No refetch from Stripe.** The signed event data plus the `stripe_event_at` ordering guard is the source of truth, which keeps network calls out of the transaction.
- **Prices by lookup key,** not env vars. `env.ts` isn't mine, and lookup keys also map a subscription changed in the portal back to a plan. **The owner must create Stripe prices with lookup keys `invai_plan_{starter,growth,pro}` and `invai_pack_{credits_500,credits_2000}`** (owner-inbox item needed; prices are OI-1).
- **Mock webhook secret** `MOCK_STRIPE_WEBHOOK_SECRET` is used only outside production. Production without `STRIPE_WEBHOOK_SECRET` refuses every Stripe webhook.
- **A cancelled subscription drops to the free (trial-limits) plan** with status `cancelled`, which isn't gated, per the "downgrade to free" wording. Only `trial_expired` blocks.
- **Pending invites hold seats,** so one owner can't invite past the limit in a burst.

## Known gaps and follow-ups
- **Label buys aren't gated yet.** `shipping/service.ts` belongs to T-2-5. The fix is to call `assertPaidActionAllowed(tx, ctx)` from `modules/billing/service` at the start of `buyLabel` and `batchBuy`.
- `sheetsBuilt` is idempotent per outbox event (jobId). A worker crash between commit and ack could count a sheet twice; it's only a meter.
- With a trial expired, the 10-minute channel poll job will fail with PAYMENT_REQUIRED on each import attempt, which is noisy in the logs. `pollableConnections` (channels, `sync.ts`) could skip those companies.
- Packs count only in the month they're bought, which is the existing `creditBalance` semantics (ai-engineer).
- Pack rows are written directly to `ai_credit_ledger` (ai-engineer's table) because the card asks for it and no grant function exists. Flagging it for the ai-engineer.
- `checkout.session.async_payment_succeeded` (delayed payment methods) isn't handled. Card-only checkout is assumed.
- Pack keys aren't in contracts: `pack` is `z.string()`, and the backend validates it. T-2-2 must use `credits_500` and `credits_2000`. The architect may want a `PACK_KEYS` enum.
- The card's `REDIS_URL=redis://localhost:6379/21` is out of range: Valkey has 16 DBs, so the API logged `ERR DB index is out of range`. Webhooks and billing don't need Redis, so the exercise wasn't affected. I ran the HEAD-export tests with db 15.

## Blocked by other owners
- `shipping/service.ts` `buyLabel`/`batchBuy` (T-2-5): add the `assertPaidActionAllowed` call, as described above.
- `rls-coverage.test.ts` fails on `two_factors` (T-2-3, commit `6ff0890`).

## Test changes outside `modules/billing`
- `tenancy/invites.test.ts` and `channels/webhooks.test.ts`: the `beforeAll` now puts their company on the `scale` plan. Those suites send many invites or installs, which the new trial limits would refuse. The limits themselves are tested in `billing/limits.test.ts`. No assertions changed.

## Processes and data
- Stopped: the API on 3210 (port verified free). `invai_t21_copy` dropped. The shared dev DB was never written by me; it already had migrations 0009/0010 applied by someone's migrate run.
- `channels/service.ts` is committed with only my 3 `connect` hunks, staged with `git apply --cached`. T-2-5's `pushTrackingForShipment` hunks and its line-11 import are left uncommitted in the working tree.
