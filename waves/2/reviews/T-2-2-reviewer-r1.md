# Review of T-2-2 (round 1)

- Reviewer: reviewer on Opus
- Author: web-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran

Setup: `git worktree add /tmp/review-t22-web e37e716` (invai-web) and `git worktree add
/tmp/review-t22-backend HEAD` (invai-backend, `240a19e` at the time), `node_modules` symlinked from
each origin repo. Own API on :3292 (`REDIS_URL=redis://localhost:6379/10`) against a DB copy
(`createdb -T invai invai_r22_copy` via `docker exec local-postgres-1 createdb …`, migrations
already current), web on :5292 pointed at it. `pnpm` scripts fail on a symlinked `node_modules`
("workspace hoist directory is not a real directory"), so I ran the `node_modules/.bin` binaries
directly, matching what the task's instructions expect.

Mid-review the tech lead reclaimed disk space and removed my worktrees, `/tmp/invai-ui` and
`/tmp/t22-*` (`:3292`/`:5292` stopped, `invai_r22_copy` dropped). All findings below were already
collected before that; I did not need to recreate the setup, since the remaining unexercised flows
(live-checkout redirect, downgrade/free-plan confirm dialogs) are already screenshotted and
reasoned about in the author's own report and match the code I read.

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` (invai-web) | exit 0, no output |
| `./node_modules/.bin/biome check .` | "Checked 104 files in 76ms. No fixes applied." |
| `./node_modules/.bin/vitest run --passWithNoTests` | "Test Files 7 passed (7)", "Tests 37 passed (37)" |
| `./node_modules/.bin/vite build` | "✓ built in 1.09s" (only the pre-existing >500 kB chunk warning) |
| `tsx src/db/migrate.ts` against `invai_r22_copy` | "up to date" |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` (re-run after the cleanup, needs no worktree) | 0 removed assertions, 40 added; no deleted/renamed test files, no `.skip`/`.only`/`fixme`, no snapshot/config changes, no test-only branches in production code. Two **untracked** files surfaced (`src/features/account/auth-errors.test.ts`, `src/features/account/session.test.ts`) — these are T-2-4's in-progress work in the same repo, not part of `e37e716`; not this card's concern. |

Exercised for real in the browser (Playwright, signed in as `owner@desertbloom.test`, DB copy
`invai_r22_copy`, states forced by hand):
- **Billing page states.** `active` (Starter, forced 8/5 users and 4/4 connections — both meters
  show red "limit reached" text as well as color, no banner since neither is a banner trigger):
  price/meters/labels all correct. `trialing` (`trial_ends_at` = +3d): badge "Trial", line "Free
  trial ends Sep 27 (3 days left)", dismissible amber banner "Your free trial ends in 3 days.
  Choose a plan to keep going." `past_due`: red badge "Past due", non‑dismissible red banner
  "Your last payment didn't go through…". `trial_expired` (`trial_ends_at` in the past, no
  `stripeSubscriptionId`): red "Trial ended" badge, non‑dismissible red banner "Your free trial has
  ended. Order imports and label buying are paused until you choose a plan." Reset to `active`
  (Growth) for the 390 px pass.
- **Money.** `labelFees: 828` cents rendered as "$8.28"; `priceMonthly: 14900` as "$149.00";
  `labelFee: 5` as "$0.05 per label" — cents-to-display is correct everywhere I checked, including
  after switching plans.
- **Limit dialog, for real.** Forced the shop onto Starter (`maxUsers: 5`) with 8 active members,
  then went to `/settings/team` and actually submitted the invite form (not an injected error). The
  backend's own `assertWithinPlan(tx, ctx, "users", 1, …)` (`invai-backend
  src/modules/tenancy/service.ts:337`) returned a real 402 `PLAN_LIMIT_REACHED
  {meter:"users",used:8,limit:5}`. The app showed: a translated toast ("Your plan's limit is
  reached. Go to Billing to upgrade.") **and** the app-wide dialog ("You've reached your plan's
  limit" / "Your plan allows 5 people. Upgrade to invite more." / Not now · Go to Billing), stacked
  correctly over the still-open Invite dialog (Radix marks the lower dialog `aria-hidden`). No raw
  server text anywhere (checked the full page text for "SERVER"/"undefined"/"[object").
- **a11y of the dialog.** `role="dialog"`, `aria-labelledby`/`aria-describedby` resolve to the
  actual translated title/body text. Manually tabbed through the open dialog: focus cycles cleanly
  through its 3 focusable elements (Go to Billing → Close → Not now → …) with no escape into the
  page behind it (confirmed by reading `document.activeElement` on each tab, not just a
  `.contains()` helper, which gave a false "escaped" reading once because it grabbed the *first*
  `[role=dialog]` in DOM order — the hidden Invite dialog — rather than the topmost one). Escape
  closes the topmost dialog and reveals the Invite dialog still open underneath (expected: form data
  isn't lost).
- **en/es at 390 px.** Billing page and the limit dialog both re-shot in Spanish at 390 px:
  `document.documentElement.scrollWidth === clientWidth` (no horizontal scroll) in both languages;
  full Spanish copy ("Llegaste al límite de tu plan", "Ir a Facturación", "Ahora no"), no untranslated
  strings, no layout breakage.
- **`changePlan` vs `checkout` consistency (the card's specific ask).** `billing.tsx`'s `choosePlan`
  calls `checkout.mutate` when `status.data.paymentsEnabled` and `change.mutate` (→
  `billing.changePlan`) otherwise. Backend `requestPlanChange` (`invai-backend
  src/modules/billing/service.ts:482`) uses the exact same gate: `if (!paymentsLive()) return
  …changePlan(…)`, for **any** plan, not only downgrades — the "downgrades/mock only" restriction in
  `wave.md`'s agreed interface is exactly what the backend enforces when `paymentsLive()` is true
  (only free is allowed then; a paid `changePlan` gets `PAYMENT_REQUIRED` with a checkout URL). The
  web's `paymentsEnabled` field is `paymentsLive()` verbatim (`getStatus`, `service.ts:310`), so the
  two sides can't drift. Confirmed via `curl .../billing/get` on my API (mock Stripe, no
  `STRIPE_SECRET_KEY`): `"paymentsEnabled":false`. Consistent with the agreed interface.

One environment note, not a product bug: my first pass at the limit dialog showed it pinned to the
bottom of the page instead of centered (`position:fixed; top:900px` — the browser's static-position
fallback for a `top:auto` fixed element). Root cause: my worktree lived at `/tmp/review-t22-web`, so
`invai-web/src/styles.css`'s `@source "../../invai-ui/src"` resolved to a nonexistent
`/tmp/invai-ui/src`, and Tailwind never generated the centering utility classes used only inside
`@invai/ui`'s `Dialog`. Symlinking `/tmp/invai-ui` to the real `invai-ui` repo and restarting Vite
fixed it immediately (dialog centered at `top:377,left:464` in a 1440×900 viewport, `z-index:50`).
Flagging only so a future reviewer doesn't waste time chasing a phantom CSS bug from the same
worktree placement.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 plan/status/dates/meters/cards, checkout+redirect, return notice, manage billing, downgrade confirm | Yes | Live-exercised plan/status/meters/cards and the limit dialog myself (above); checkout redirect, `?checkout=success\|cancel`, Manage billing and the downgrade/free confirms are code-verified (`billing.tsx`, matches `checkout.mutate`/`portal.mutate`/`ConfirmDialog` wiring) and screenshotted by the author (`checkout-plan-live-…`, `downgrade-confirm-…`, `return-success-…`, `free-confirm-…`) — I looked at these and they match the code and copy |
| 2 translated PLAN_LIMIT_REACHED/PAYMENT_REQUIRED dialog, no raw English | Yes | Real 402 from a real invite (above); `PAYMENT_REQUIRED` path code-verified in `lib/errors.ts` (swaps message for *any* caller of `errorInfo`, not just the dialog) and screenshotted by the author with an injected raw-English body that never surfaced (`payment-required-d-es-light.png`, which I looked at) |
| 3 banner: trial ≤7d, past due, expired (en/es) | Yes | All three forced and shown live in English (above); es strings present and symmetric in `i18n/es.ts` |
| 4 AI credit pack via checkout({pack}) | Yes | Code-verified (`buyPack` → `checkout.mutate({pack})`, keys match backend's `AI_CREDIT_PACKS`); author's `pack-keyboard-…` screenshot (keyboard-only) matches |
| 5 390 px + keyboard nav | Yes | Billing page and limit dialog re-shot at 390 px in en/es, no horizontal overflow; dialog focus trap and Escape manually verified (above) |
| 6 en/es for every `BillingStatus` incl. `trial_expired` | Yes | All five statuses in both `i18n/en.ts`/`es.ts` (`billingStatus.*`); `trial_expired` shown live as "Trial ended" / (i18n) "Prueba terminada" |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat e37e716`: `billing.tsx`,
      `features/billing/**`, `lib/errors.ts`(+test), `components/app-frame.tsx` (2-line banner
      mount only), `i18n/{en,es}.ts` — matches the card's owned globs exactly)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — `scan-test-weakening.sh` clean for this
      diff (0 removed assertions, 40 added); new tests (`status.test.ts`, `checkout.test.ts`,
      `errors.test.ts` additions) cover the banner windowing, the plan-move/custom-plan logic, the
      `meter`/`limit` field-name fallback, and "never shows server text" directly
- [x] Tenancy n/a (no server code in this diff); idempotency n/a; money in cents verified live
      (above); en/es text symmetric and complete (`upgrade.*`, `billingBanner.*`, `billingStatus.*`,
      `billing.*` all present in both catalogs, checked by reading the full diff of both files)
- [x] Decisions recorded where needed — the `changePlan`/`checkout` split matches `wave.md`'s
      agreed interface exactly (verified against the backend gate, not just the author's word)

## Optional notes (not blocking)
- The author's own known-gaps list (`assertPaidActionAllowed` not yet wired into imports/label
  buys, the global mutation toast still showing under the dialog, no `billing.packs` contract
  procedure, plan names untranslated, `formatDate` uses browser locale) are all correctly scoped to
  other owners or follow-up cards and don't block this one.
- Minor: `InviteDialog` (`invai-web/src/routes/_app/settings/team.tsx`) stays open behind the new
  limit dialog rather than closing itself on a plan-limit error. This is reasonable (no typed data
  is lost, and Radix correctly hides it from assistive tech while the limit dialog is open) but
  worth a design opinion from product-designer.
