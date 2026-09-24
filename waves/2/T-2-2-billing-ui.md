# T-2-2: Billing UI and upgrade prompts

| Field | Value |
|---|---|
| Wave | 2 |
| Scope ref | `product/scope.md#mvp-in` item 15 |
| Backlog | B-53 (web) |
| Owner | web-engineer |
| Reviewer | reviewer |
| Co-reviewers | product-designer |
| Risk flags | ui |
| Model | opus |

## Owned paths (edit)
- `invai-web/src/routes/_app/settings/billing.tsx`
- `invai-web/src/lib/errors.ts` (upgrade prompt for `PLAN_LIMIT_REACHED` and `PAYMENT_REQUIRED`)
- New `invai-web/src/features/billing/**`
- `invai-web/src/components/app-frame.tsx` (a trial, past-due or expired banner only)
- `invai-web/src/i18n/{en,es}.ts` (new keys only; edit by hand, because `pnpm i18n` is lossy)
- tests next to these files

## Depends on
- The architect's contract stubs (wave.md). Build against the mock backend: with mock Stripe, `checkout` returns a local URL.

## Acceptance criteria
1. The billing page shows the current plan, status, trial end or renewal date, usage meters and plan cards.
   - Choosing a paid plan calls `billing.checkout` and redirects.
   - On return (`?checkout=success|cancel`), it shows a clear message and refreshes the status.
   - "Manage billing" opens the portal.
   - Downgrading to free asks for confirmation.
2. A `PLAN_LIMIT_REACHED` or `PAYMENT_REQUIRED` error anywhere in the app shows a translated dialog: what hit the limit, and a button to billing. There are no raw English server messages.
3. The app frame shows a banner (en/es) for: a trial ending within 7 days, past due, and trial expired.
4. An AI credit pack can be bought from the billing page (checkout with `pack`).
5. The page works at 390 px and passes keyboard navigation.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-web.
- In the browser, against your own API on a DB copy: check each state (trialing, past_due, trial_expired; force it on the copy DB), the checkout redirect, and the limit dialog. Take screenshots in en and es at desktop and 390 px, and look at them.

## Out of scope
- Backend (T-2-1).

## Added by the stub review
- AC 6: en/es text for every `BillingStatus` status, including `trial_expired`.
