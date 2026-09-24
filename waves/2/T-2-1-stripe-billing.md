# T-2-1: Stripe billing (backend)

| Field | Value |
|---|---|
| Wave | 2 |
| Scope ref | `product/scope.md#mvp-in` item 15 |
| Backlog | B-53 (backend) |
| Owner | backend-engineer (billing), with `integrations/billing/**` and `api/webhooks.ts` granted on this card |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer, backend-foundation (migration), architect (contract use) |
| Risk flags | payments, webhooks, migration |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/billing/**`
- New `invai-backend/src/integrations/billing/**` (a Stripe adapter and a mock adapter)
- `invai-backend/src/api/webhooks.ts` (add the Stripe route only; keep T-1-2's verify-first order)
- `invai-backend/src/db/schema/billing.ts` and its migration
- `invai-backend/src/modules/tenancy/service.ts` and `modules/channels/service.ts`, **only** to call `assertWithinPlan` for users and connections
- `invai-backend/package.json` (add the `stripe` dependency; if an install is needed, ask the tech lead, don't run it in the shared tree)
- tests next to these files

## Evidence
`build/audit-2026-09-24.md` §A-BE B-53.

## Acceptance criteria
1. `billing.checkout` creates a Stripe Checkout session (subscription mode, price per plan from config) with `client_reference_id` = company id. It returns the URL. It never changes the plan.
2. `POST /webhooks/stripe` (its own Hono route in `api/webhooks.ts`, separate from the generic `/webhooks/:channel` marketplace dispatcher, which only accepts channels in the contracts `CHANNELS` enum):
   - verifies the Stripe signature first;
   - dedupes on the event id through a new billing-owned table in `db/schema/billing.ts` (e.g. `billing_webhook_events`, unique on Stripe event id, system-only writes, same RLS/purge shape as decision 0009's `webhook_deliveries` — that table itself isn't reusable here because its `channel` column is constrained to the marketplace `CHANNELS` enum, which must not grow a `stripe` value);
   - handles `checkout.session.completed`, `customer.subscription.created/updated/deleted` and `invoice.payment_failed/paid`.
   The plan and status change **only** here. Out-of-order events are handled by comparing the subscription's `created`/`current_period` fields (store the last-processed Stripe event's `created` timestamp on the subscription row and ignore an incoming event that's older).
3. `billing.portal` returns a customer-portal URL for companies with a Stripe customer.
4. `changePlan` with live Stripe: allowed only as a downgrade to free, or a cancel at period end. A paid plan returns `PAYMENT_REQUIRED`. With mock Stripe it behaves as today, so demos work.
5. Trial expiry: a daily job moves companies past `trialEndsAt` without a subscription to `trial_expired`. That state blocks imports and label buys with `PAYMENT_REQUIRED`; reading data still works, and orders already in the system keep moving through the production floor (pick, press, QC, pack, scan) — none of that spends money, so it isn't gated.
6. Plan limits enforced for `maxUsers` (invite) and `maxConnections` (connect), with `PLAN_LIMIT_REACHED` and `limit`. Record `sheetsBuilt` usage.
7. AI credit packs: `checkout` with `{ pack }` (one-time payment). The webhook writes a `pack` ledger row, idempotent on the event id.
8. `getStatus` reports `paymentsEnabled` true only when Stripe is live.
9. Tests use a fetch-mocked Stripe for signature verification, each event type, replays, out-of-order events and the limits.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-backend, with your own test DB.
- For real: on your port with mock Stripe, `checkout` returns a URL. Post signed test webhooks (sign them with a test secret in a script) and show the plan changing only through the webhook. Show a replay being ignored and a trial-expired company getting `PAYMENT_REQUIRED` on import.

## Out of scope
- The web UI (T-2-2). Real Stripe keys (the owner). Prices (OI-1; use the current catalog).

## Added by the stub review
- AC 10: the `pack` input accepts only known pack keys.
