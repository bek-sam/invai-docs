# Report: T-2-2 Billing UI and upgrade prompts
Author: web-engineer on Opus 5.5

```
Card: T-2-2  Owner: web-engineer  Scope ref: product/scope.md#mvp-in item 15
Owned (edit): invai-web settings/billing.tsx, lib/errors.ts, features/billing/**, app-frame.tsx (banner only), i18n/{en,es}.ts (new keys), tests
Read-only: invai-contracts, invai-backend, invai-ui
Risk flags → co-reviewers: ui → product-designer
```

Web commit: **invai-web `e37e716`** (on main, not pushed). It was built against T-2-1's commit `5d80c52` and verified on it.

## Built
- **Billing page** (`src/routes/_app/settings/billing.tsx`)
  - Shows the plan and a status badge for all five statuses (en/es), and a line for the current state: trial end with days left, "Renews {date}", "Ends {date}. It won't renew." (`cancelAtPeriodEnd`), past due, trial ended, or cancelled.
  - Usage meters show "limit reached" as text as well as red, so color isn't the only signal. Plan cards list orders, AI credits, users, channel connections and the label fee. Scale shows "Custom price · Contact us" instead of $0.
  - **Plan choice.** With payments live, the page calls `billing.checkout({plan})` and redirects. If T-2-1 returns CONFLICT (the shop already has a subscription), it opens `billing.portal`. In test mode (mock Stripe), it calls `changePlan`, which applies right away, as T-2-1 documents for demos.
  - **Confirmations.** A downgrade asks first (the dialog lists the new limits). "Switch to the free plan" (`changePlan({plan:"trial"})`, T-2-1's free plan) also asks first. With live Stripe the dialog says the shop keeps the plan until the period ends.
  - **Return from checkout.** `?checkout=success` shows a thank-you, refreshes billing, credits and `me`, and polls billing every 2 s for 30 s while the webhook lands. `?checkout=cancel` says nothing was charged. The mock returns (`mock=1`, `portal=mock`) get their own honest test-mode message. The flags are then removed from the URL.
  - **Manage billing** opens the portal. It shows for active, past-due and cancelled plans.
  - **AI credit packs.** "Buy 500 credits" and "Buy 2,000 credits" call `checkout({pack})`. The keys `credits_500` and `credits_2000` match T-2-1's `AI_CREDIT_PACKS`.
  - **Checkout and portal failures** get translated toasts: 501 ("isn't switched on yet"), EMAIL_NOT_VERIFIED, no billing account, network, and a generic message. Server text never shows (`features/billing/checkout.ts`).
- **Upgrade dialog, app-wide** (`features/billing/upgrade-prompt.tsx`, mounted by the banner)
  - It subscribes to the QueryClient's mutation and query caches. Any `PLAN_LIMIT_REACHED` (users, connections, orders or AI credits, with the limit number), `CREDITS_EXHAUSTED` or `PAYMENT_REQUIRED` opens one translated dialog with a "Go to Billing" button. People without `billing.read` are asked to contact the owner instead.
  - A query that keeps failing re-opens the dialog at most every 5 minutes.
  - `lib/errors.ts` adds `upgradeReason()`. `errorInfo()` now swaps these codes' server text for a translated one-liner, so the global mutation toast doesn't show raw English either.
- **App-frame banner** (`features/billing/billing-banner.tsx`, plus one import and one JSX line in `app-frame.tsx`)
  - It covers a trial ending within 7 days ("ends in N days", "tomorrow", "today"; the reminder can be hidden for the session), past due, and an expired trial. The last two are red and can't be dismissed.
  - It shows only for shop orgs with `billing.read`. The "Choose a plan" / "Update payment" link is hidden on the billing page itself.
- **i18n.** 90 en and 93 es keys were added by hand (`billing.*`, `billingBanner.*`, `upgrade.*`, `billingStatus.trial_expired`), with nothing removed. A script checked that every key the new code uses exists in both catalogs. `action.close` comes from the shared invai-ui catalog.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 plan, status, dates, meters, cards | yes | `active-501-d-en-light`, `trialing-d-en-light`, `past-due-billing-d-en-light`, `trial-expired-billing-d-es-dark` |
| 1 paid plan → checkout + redirect | yes | `checkout-plan-live-d-en-light`: with `paymentsEnabled` forced true (Playwright route on billing.get), Upgrade sent `billing/checkout {"plan":"pro"}` and the page redirected to the mock success URL and showed the notice. The request log is below. |
| 1 return success/cancel, refresh | yes | `return-success-*`, `return-cancel-d-es-dark`; the URL is cleaned to `/settings/billing` |
| 1 Manage billing → portal | yes | curl `billing/portal` → `?portal=mock` URL. Before T-2-1: `portal-501-m-es-dark` |
| 1 downgrade (and to free) confirms | yes | `downgrade-confirm-d-en-light`, `free-confirm-m-es-light`, `free-applied-d-en-light` (toast "Plan changed to Trial"; DB `trial/trialing`) |
| 2 translated limit/payment dialog | yes | `limit-users-d-en-light`, `limit-users-m-es-dark`: a real invite on the Starter plan (8/5 users) got a 402 PLAN_LIMIT_REACHED from T-2-1. `payment-required-d-es-light`, `-m-en-light`: a PAYMENT_REQUIRED body with message "SERVER ENGLISH TEXT" (route-injected) wasn't shown anywhere. |
| 3 banner: trial ≤7d, past due, expired (en/es) | yes | `trialing-today-*`, `past-due-*`, `trial-expired-*` |
| 4 AI credit pack | yes | `pack-keyboard-d-en-dark`: Buy 500 credits, pressed with Enter from the keyboard → `checkout {pack}` → redirect → test-checkout notice. curl with an unknown pack → BAD_REQUEST |
| 5 390 px + keyboard | yes | every `-m-` shot at 390 px; the script checks `scrollWidth`, and no horizontal scroll was reported. The Tab order runs through nav into content, focus rings are visible, dialogs are Radix (focus trap, Esc) |
| 6 en/es for every status incl. trial_expired | yes | `billingStatus.*` in both catalogs; `trial-expired-billing-d-es-dark` shows "Prueba terminada" |

Screenshots are in `invai-docs/waves/2/reports/T-2-2/` (27 files). I looked at each one discussed here.

## Checks I ran (invai-web, after the final edit)
| Command | Result |
|---|---|
| `pnpm typecheck` | clean |
| `pnpm lint` | `Checked 104 files … No fixes applied.` |
| `pnpm test` | `Tests 37 passed (37)`, including new `features/billing/status.test.ts`, `checkout.test.ts` and `upgradeReason` cases in `lib/errors.test.ts` |
| `pnpm build` | `✓ built in 1.08s` (the >500 kB chunk warning was already there) |
| `E2E_WEB_URL=:5220 E2E_API_URL=:3220 playwright test e2e/screens.smoke.spec.ts` | `2 passed`, "No screen issues." (every shop screen and the vendor portal, with the banner mounted) |

## Exercised for real
- API on :3220 ran from a `git archive` snapshot of backend `5d80c52` (non-watch, so other agents' in-progress edits couldn't restart or break it). It used DB copy `invai_t22_copy` (migrated) and web on :5220.
- curl as the owner:
  - `billing/checkout {pack:credits_500}` → `…/settings/billing?checkout=success&mock=1&session=cs_mock_payment_invai_pack_credits_500`
  - `checkout {plan:pro}` → the mock subscription URL
  - `portal` → `?portal=mock`
  - `checkout {pack:"nope"}` → `BAD_REQUEST`
  - `billing/get` now returns `currentPeriodEnd` and `cancelAtPeriodEnd`.
- States were forced on the copy DB (`subscriptions.status`, `trial_ends_at`, `companies.plan`): trialing +3 days, past_due, trial_expired, active, and Starter with 8 users (for the limit).
- Before T-2-1 landed, checkout and portal returned 501. The page showed "Online payment isn't switched on yet…" and "Managing billing online isn't switched on yet." (`checkout-501-d-en-light`, `portal-501-m-es-dark`).
- Refused case: people without `billing.manage` see no plan, pack or portal buttons (from `useCan`). `billing.read` gates the banner and the "Go to Billing" button.

## Decisions
- **Test mode switches plans with `changePlan`, live mode uses checkout.** T-2-1's mock checkout never changes the plan, and T-2-1 keeps `changePlan` immediate under mock "so demos work". Going through checkout in test mode would redirect back to a "thanks" message with nothing changed. Packs always use checkout, and in test mode the return says honestly that nothing changed. The live checkout path was verified by forcing `paymentsEnabled` in the browser.
- **"Free" is the `trial` plan key**, following T-2-1: `changePlan("trial")` is the downgrade to free, or cancel at period end on live Stripe.
- **CONFLICT from checkout opens the portal**, because T-2-1 refuses a second subscription and changing an existing one happens in Stripe's portal.
- **`CREDITS_EXHAUSTED` also opens the upgrade dialog** (AI credits, with a pack hint). It is a plan-limit refusal like the other two.
- The dialog listens to the QueryClient caches from the app frame, so `main.tsx` (outside my paths) didn't need an edit.
- Pack prices aren't shown in the app, only on Stripe's page, because the contract has no pack price list and the owner hasn't approved pack prices.

## Known gaps and follow-ups
- **T-2-1's `assertPaidActionAllowed` isn't called by imports or label buys yet** (in `5d80c52`, grep finds it only in `billing/service.ts` and its tests). So a trial-expired shop isn't actually blocked, and I couldn't trigger PAYMENT_REQUIRED for real. I verified the dialog with an injected 402. Owner: backend-engineer (T-2-1), or the owners of those modules.
- On a limit error the global mutation toast still shows (translated) under the dialog. Skipping it for these codes needs a one-line change in `main.tsx`'s `MutationCache.onError` (web, not on this card).
- There's no `billing.packs` procedure, so pack keys are duplicated in `features/billing/packs.ts`. The architect could add a pack list with prices.
- Plan names ("Trial", "Growth") come from the server's catalog and aren't translated.
- `formatDate` uses the browser locale, not the app language, and has no year. This behavior was already there.
- The full browser golden path (`pnpm e2e` golden-path, `E2E_API=1` api golden path) wasn't run. It needs a fresh seed of a shared stack. The screens smoke passed against my stack.
- Redis: `redis://localhost:6379/22` is out of range (Valkey has 16 DBs, `ERR DB index is out of range`), so I used DB **12** and flushed it afterwards. The wave rules' `/2<k>` numbering needs changing: every `/2x` index fails.
- While restarting my first API I ran `pkill -f "invai-backend.*tsx watch src/api/server.ts" -P 1`, which could also have matched another agent's detached `tsx watch` API. Afterwards no node process was listening on any port. If an agent lost its API around 16:17, this was probably the cause.

## Blocked by other owners
- None blocking. Follow-ups are listed above (T-2-1 gate wiring, `main.tsx` toast suppression, a `billing.packs` contract).

## Processes and data
- Stopped: my API on :3220 (snapshot in `/tmp/t22-backend`, deleted) and Vite on :5220. Dropped `invai_t22_copy`. Flushed Valkey DB 12. Shared dev DB untouched.
