# Wave 2: money and accounts

- Dates: 2026-09-24 →
- Goal (user outcome):
  - A shop can pay for a plan through Stripe, and can't get a paid plan for free.
  - Accounts are recoverable and protected: email verification, password reset and optional MFA.
  - Buying a label can never double-charge, and a cancelled order never gets its tracking pushed or its postage wasted.
- Plan reviewed by: product-manager (`reviews/plan-product-manager-r1.md`), architect (`reviews/plan-architect-r1.md`)

## Cards
| Card | Owner | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|
| T-2-1 Stripe billing (backend) | backend-engineer (billing) | reviewer + security-reviewer, backend-foundation, architect | payments, webhooks, migration | planned |
| T-2-2 Billing UI and upgrade prompts | web-engineer | reviewer + product-designer | ui | planned |
| T-2-3 Account security (backend) | backend-foundation | reviewer + security-reviewer | auth, pii | planned |
| T-2-4 Account security (web) | web-engineer | reviewer + product-designer, security-reviewer | auth, ui | planned |
| T-2-5 Crash-safe labels, tracking and cancel | backend-engineer (shipping) | reviewer + security-reviewer, qa-engineer | payments, marketplace-policy | planned |

Moved out of the roadmap's wave 2: B-66 (EasyPost live tracking) goes to wave 3, because it needs `api/webhooks.ts`, which T-2-1 owns in this wave.

## Parallel work rules
- Each card has its own test DB, `invai_test_t2<k>`, and its own API port, `31<k>0` (web dev servers `52<k>0`).
- Commit only your paths: `git commit -m ... -- <paths>`, then check `git show --stat HEAD`.
- Never run `pnpm install` in a shared repo. For a worktree, symlink `node_modules` into it.
- Never `db:reset` the shared dev DB. For a real exercise, use a copy: `createdb -U invai -T invai invai_t2<k>_copy`, and drop it afterwards.
- Don't regenerate a migration another card may already have applied. If the journal collides, tell the tech lead.
- Run T-2-2 and T-2-4 after the architect's contract stubs are committed. T-2-4 also needs T-2-3's endpoints; build against the agreed Better Auth routes below.

## Agreed interfaces (stubs committed first by the architect)
- `billing.checkout({ plan }) -> { url }`: creates a Stripe Checkout session. It never changes the plan directly.
- `billing.portal() -> { url }`: opens the Stripe customer portal.
- `BillingStatus` gains `status: "trialing" | "active" | "past_due" | "cancelled" | "trial_expired"` (matches the existing `SUBSCRIPTION_STATUSES`/`BillingStatus` spelling already in the schema and contract; the earlier draft of this line said "canceled" — that was a typo, not a new value), `trialEndsAt`, `currentPeriodEnd` and `cancelAtPeriodEnd` (additive).
- `billing.changePlan` stays only for downgrades to free, or when Stripe is mocked (dev, or `ALLOW_MOCKS`). Otherwise it returns `PAYMENT_REQUIRED` with the checkout URL to use.
- Error codes the web must handle: `PLAN_LIMIT_REACHED` (with `limit`: orders, users, connections or ai_credits), `PAYMENT_REQUIRED` and `EMAIL_NOT_VERIFIED`. All three are typed in `COMMON_ERRORS` (contracts `contract/_base.ts`) as part of the architect's stub commit, additive alongside the existing codes.
- **Stripe webhook dedupe:** `webhook_deliveries` (decision 0009) cannot be reused as-is — its `channel` column is a Postgres check constraint on the marketplace `CHANNELS` enum (`etsy | amazon | shopify | tiktok | walmart | ebay | csv`), which does not and should not include `stripe`. T-2-1 adds its own table in `db/schema/billing.ts` (e.g. `billing_webhook_events`, unique on Stripe event id, system-only writes, same RLS/purge pattern as decision 0009) rather than widening `CHANNELS`. `POST /webhooks/stripe` is its own Hono route in `api/webhooks.ts`, not a case of the generic `/webhooks/:channel` dispatcher (which 404s on anything outside `CHANNELS`).
- Better Auth routes (T-2-3 provides them, T-2-4 consumes them):
  - `emailVerification` (link to `/verify-email?token=`)
  - `requestPasswordReset` / `resetPassword` (link to `/reset-password?token=`)
  - the `twoFactor` plugin (TOTP plus backup codes; issuer "InvAI")
  - `changePassword`, `listSessions` and `revokeSession` from the standard client
- Wave 1 follow-ups included in the architect's stub commit: `submitting` added to `PO_STATES` (additive; no consumer does an exhaustive switch over `PoState` today — `invai-web/src/components/po-badge.tsx`'s `TONE` map is the one place a future card must add a `submitting` entry before that state is ever shown to the web, since the backend currently coerces `submitting` to `draft` in `inventory/service.ts:852`), and the `user.invited` event payload changed to `{ orgId, invitationId }` (checked: nothing emits or consumes this event yet, so the shape change is safe even though it isn't strictly additive).

## Integration gate
- [ ] Fresh reset, migrate, seed (imaging up, worker stopped)
- [ ] `run-golden-path` passes (API, browser, floor)
- [ ] `pnpm build` in invai-backend, web, floor
- [ ] Key screens looked at by the tech lead
- [ ] Pushed to `main`

## Retro
- What slipped:
- Lessons added:
