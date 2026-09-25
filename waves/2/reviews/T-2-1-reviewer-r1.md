# Review of T-2-1 (round 1)

- Reviewer: reviewer on Opus
- Author: backend-engineer (billing) on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Setup: `git worktree add --detach /tmp/review-t21-worktree 5d80c52` (invai-backend), `node_modules`
symlinked from `invai-backend`, own DB `invai_test_r21` / `TEST_MIGRATION_DATABASE_URL` per the
task, `REDIS_URL=redis://localhost:6379/11`. Reviewed only `1d3a8e0`, `fadfa26`, `5d80c52` (the parent
chain also carries T-2-3's `6ff0890` and T-2-5's `26cda9b`, not reviewed here).

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | exit 0, no output |
| `./node_modules/.bin/biome check .` | "Checked 206 files in 96ms. No fixes applied." |
| `./node_modules/.bin/tsup` | "Build success" (server.js, index.js, chunks) |
| `tsx src/db/migrate.ts` against `invai_test_r21` | "up to date" (0009–0012 applied cleanly) |
| `./node_modules/.bin/vitest run` | 41/42 files passed; **1 failed: `rls-coverage` → `tables without RLS are only the Better Auth identity tables`, `two_factors`**. 273/274 tests passed. Confirmed this is T-2-3's `6ff0890` (parent of `5d80c52`), not this card's table (`billing_webhook_events` has RLS and passes coverage). No other failure. |
| `./node_modules/.bin/vitest run src/modules/billing` | 31/31 passed (matches the report) |
| `.claude/skills/independent-review/scan-test-weakening.sh` (files touched by 1d3a8e0/fadfa26/5d80c52 only, base `d97cd3c`) | 0 removed assertions, 97 added; no `.skip`/`.only`/`fixme`; 2 `vi.mock` calls in `stripe.test.ts`, both preserve the real implementation (`...real`) and only swap the HTTP transport (`fakeStripeFetch`) or wrap `emit` to force one crash-test failure — not mocks of the unit under test. (A first run against `d97cd3c` unfiltered surfaced hits in `label-safety.test.ts`/carrier mocks — those belong to T-2-5's `26cda9b`, which sits in the same linear history; excluded.) |
| Exercised for real: API on port 3291, `tsx src/api/server.ts`, mock billing, against `invai_r21_copy` (`createdb -T invai`, dropped after) | see below |

Real exercise, signed with `Stripe.webhooks.generateTestHeaderString` against `MOCK_STRIPE_WEBHOOK_SECRET`:
- `POST /billing/checkout {plan:pro}` → 200, mock URL, `GET /billing/` still shows `growth` (plan unchanged by checkout).
- `POST /billing/checkout {pack:credits_500}` → 200; `{pack:bogus}` → 400 "Unknown credit pack"; `{plan:scale}` → 400.
- Signed `customer.subscription.updated` (pro/active) → `{"outcome":"processed"}`; **same request replayed** → `{"duplicate":true}`; DB shows exactly one `billing_webhook_events` row and the plan changed to `pro`/`active` **only** via this call.
- Bad signature → 401, no row written.
- Older `customer.subscription.updated` (past_due/starter, `created` in the past) → `{"outcome":"ignored"}`; plan/status stayed `pro`/`active` (out-of-order proven, not just claimed).
- Signed `checkout.session.completed` pack purchase (`metadata.pack=credits_500`) → processed; replay → duplicate; `ai_credit_ledger` has exactly one `pack|500|billing_webhook_event` row.
- `POST /channels/connect` on the trial plan (used 4, limit 2) → 402 `PLAN_LIMIT_REACHED {meter:"connections", used:4, limit:2}` (off-by-one at the boundary confirmed: `used + adding > limit`).
- `GET /orders` (reads) kept working throughout.
- No secrets (`whsec_`, `sk_`) in the API log at any point.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 checkout | Yes | Live exercise: `client_reference_id`/metadata set from `ctx.companyId` (session), plan unchanged after checkout; `stripe.test.ts` covers mode/price/plan-unchanged |
| 2 webhook | Yes | Own Hono route registered before `/:channel` (`api/webhooks.ts`); raw body via `c.req.text()`, signature verified before any parsing; dedupe race closed by a single transaction that inserts the unique-keyed row and applies the event together (a concurrent second insert blocks on the unique index, conflicts, does nothing); out-of-order via `stripe_event_at` compare (`isStale`), live-exercised |
| 3 portal | Yes | `stripe.test.ts` "portal needs a Stripe customer"; code path checked |
| 4 changePlan | Yes | `requestPlanChange`: paid plan → `PAYMENT_REQUIRED` + checkout URL; live cancel → `cancelAtPeriodEnd`; no live sub → drops to free now; mock unchanged; `stripe.test.ts` covers each |
| 5 trial expiry | Yes (imports); label buys correctly deferred to T-2-5 per the card | `expireTrials` idempotent (`WHERE status='trialing'`); `assertPaidActionAllowed`/`assertWithinPlan("orders")` gate imports only; floor/production code is untouched by this diff, so it stays ungated by construction; `limits.test.ts` "trial expiry" (3 tests) read directly |
| 6 limits | Yes | Off-by-one checked: `used + adding > limit`, boundary tests in `limits.test.ts` (3rd of 3 seats fine, 4th blocked; 2 of 2 connections fine, 3rd blocked) and live-exercised (`used:4,limit:2`) |
| 7 packs | Yes | Live-exercised: one ledger row survives a replay |
| 8 paymentsEnabled | Yes | Live-exercised: `false` under mock; `paymentsLive()` gates it |
| 9 tests | Yes | 31 billing tests, real Stripe SDK against a mocked `fetch` |
| 10 pack keys | Yes | `isPackKey` on both `checkout` input and the webhook's `metadata.pack`; live-exercised (`bogus` → 400) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` against `d97cd3c`: `db/schema/billing.ts` + migration, `api/webhooks.ts` (Stripe route only), `integrations/billing/**`, `modules/billing/**`, 3-hunk touches to `tenancy/service.ts` and `channels/service.ts` for `assertWithinPlan` only, `package.json`/lockfile for the `stripe` dep, plus test files next to owned code)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan found no weakening in this card's files. The `scale`-plan `beforeAll` edits in `tenancy/invites.test.ts` and `channels/webhooks.test.ts` are fixture adjustments (those suites weren't testing plan limits and would otherwise trip the new trial gate mid-suite); the boundary itself is covered, equally or more precisely, in `billing/limits.test.ts`. Not a weakening.
- [x] Tenancy (`withTenant`/`withSystem` with reason, RLS on new table), idempotency (unique on `stripe_event_id`, insert+apply in one tx), money in cents, en/es text unchanged from existing pattern (backend error messages are English-only project-wide; not a new deviation)
- [x] Decisions recorded where needed (architect's plan review already covers the `webhook_deliveries`-vs-own-table decision)

## Optional notes (not blocking)
- No explicit *concurrent* (`Promise.all`) two-delivery test for the dedupe race — only sequential replay is tested. Not blocking: the fix is structural (unique index + single transaction), so it holds under real concurrency regardless, and Stripe's own retries are sequential in practice.
- Author-flagged follow-ups (label-buy gating for T-2-5, `PACK_KEYS` contract enum, poller skipping trial-expired companies) are correctly out of this card's scope and already logged in `wave.md`.
