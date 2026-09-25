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
| T-2-1 Stripe billing (backend) | backend-engineer (billing) | reviewer + security-reviewer, backend-foundation, architect | payments, webhooks, migration | done (approved r1) |
| T-2-2 Billing UI and upgrade prompts | web-engineer | reviewer + product-designer | ui | done (approved r1) |
| T-2-3 Account security (backend) | backend-foundation | reviewer + security-reviewer | auth, pii | done (approved r1) |
| T-2-4 Account security (web) | web-engineer | reviewer + product-designer, security-reviewer | auth, ui | done (approved r1) |
| T-2-5 Crash-safe labels, tracking and cancel | backend-engineer (shipping) | reviewer + security-reviewer, qa-engineer | payments, marketplace-policy | done (approved r1) |

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
- [x] Fresh reset, migrate (to 0012), seed (imaging up, worker stopped)
- [x] `run-golden-path`: API 13/13; browser 15/15 ×3 after the `clickIfShown` flake fix (`33d15a4`, reviewed in T-2-7); floor 1/1 (`gate.md` §§1–6)
- [x] Builds pass in backend, web and floor
- [x] Gate screenshots in `gate/` looked at (billing, password reset, account, label buy and void)
- [x] Pushed to `main` (backend, web, infra, docs)

## Retro
- What slipped: the account usage limit stopped all 4 builders mid-card, and the disk filled (ENOSPC) and took Docker down. Both were resumed without lost work.
- First-pass approvals: 5 of 5 cards (T-2-1 to T-2-5). QA's e2e fix needed one lint round.
- Lessons added: kill only your own PIDs; Redis DBs are 0–15; only the tech lead pushes; check the disk before each wave; 3 builders at once; put worktrees next to the repos, not in `/tmp`.

## Follow-ups found during the build
- Real Stripe needs prices with lookup keys `invai_plan_{starter,growth,pro}` and `invai_pack_{credits_500,credits_2000}`. This goes to the owner with OI-1.
- An expired trial makes the 10-minute channel poll fail with `PAYMENT_REQUIRED` on every attempt. The poller should skip those companies. Owner: integrations-engineer (wave 3).
- Contracts: consider a `PACK_KEYS` enum for `billing.checkout({ pack })`. Owner: architect.
- Redis indexes in wave prompts must be 0–15.
- Auth (T-2-3):
  - Better Auth rate limits are in memory per process, so they must move to Valkey before there's more than one API task (with B-20).
  - Sign-up still reveals whether an email exists (pre-existing).
  - Rotating `BETTER_AUTH_SECRET` makes stored TOTP secrets and backup codes unreadable: add a runbook note (B-106).
  Owner: backend-foundation.
- Web `main.tsx`: hide the global mutation toast for `PLAN_LIMIT_REACHED`, `PAYMENT_REQUIRED` and `CREDITS_EXHAUSTED`, because the upgrade dialog already covers them. Owner: web-engineer.
- Add a `billing.packs` procedure, so pack keys and prices aren't duplicated in the web app (with `PACK_KEYS`). Owner: architect.
- Shipping (T-2-5):
  - Nothing sweeps a buy, void or push intent left in flight when nobody retries; it needs an alert or sweep job (with B-17).
  - The future Etsy API adapter must read back before `createReceiptShipment`, because each call emails the buyer (B-108).
  - With real EasyPost, CSV-channel items stay `packed` until the tracker webhooks land (B-66, wave 3).
  - `src/modules/README.md:79` still shows the old `pushTracking(tx, …)` example (docs-writer).
  Owner: backend-engineer (shipping).
- `createdb` isn't on the host. Use `docker exec local-postgres-1 createdb -U invai -T invai <copy>`.
- Security hardening (Low): `invai_app` has full CRUD on the Better Auth identity tables (`users`, `sessions`, `accounts`, `verifications`, `two_factors`). Consider narrowing the grants; add the item to `security/v1-review.md`. Owner: security-reviewer + backend-foundation.
- From the T-2-5 review:
  - Migration 0012's unique index on `labels` has no guard for existing data. It's safe today, but future index migrations on live tables should use `CONCURRENTLY` or a pre-check.
  - `orders.channelPerformance` still treats label-buy time as "shipped", which is now more wrong for CSV channels.
  Owner: backend-engineer (orders).
- `pnpm typecheck/lint/test` fail inside worktrees with a symlinked `node_modules`. Reviewers should run the `node_modules/.bin` binaries directly.
- A worktree under `/tmp` breaks the web's Tailwind `@source "../../invai-ui/src"`: symlink `/tmp/invai-ui`, or put worktrees next to the repos.
- **Disk:** the machine ran out of space mid-wave (ENOSPC), which also took down Docker. The owner cleared 16 GB. The tech lead now checks `df -h /` before each wave and drops test DBs after each gate.
- From the T-2-4 review:
  - Suppress the mutation toast for `EMAIL_NOT_VERIFIED` too, together with the upgrade codes in `main.tsx`.
  - Strip the reset and verify token from the URL after use (`history.replaceState`). Low.
  - Seed users all have `locale: "en"`; give Spanish floor staff `es` (B-34 or B-106).
  Owners: web-engineer, backend-foundation (seed).
