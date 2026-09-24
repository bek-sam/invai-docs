# Wave 2 plan review — architect, round 1

## Verdict: approve (with clarifications applied to the cards and `wave.md`)

## Path overlaps between parallel cards
- **`app-frame.tsx` (T-2-2 and T-2-4):** T-2-2 owns "a trial, past-due or expired banner only"; T-2-4
  owns "the user menu entry... coordinate by editing only the user-menu block." Checked the current file
  (329 lines): the banner slot (top-level `AppFrame` render) and the account-menu block (a separate
  `AccountMenu`-style component near the bottom, lines ~260–329) are already structurally distinct
  regions. Both cards already carry the required mitigation (pathspec commit + `git diff` check before
  committing, escalate to tech lead on overlap). Sufficient as written; no change needed.
- **`channels/service.ts` (T-2-1 and T-2-5):** T-2-1 touches `connect` (~line 200) to call
  `assertWithinPlan`; T-2-5 touches `pushTrackingForShipment` (~line 426) only. Confirmed these are
  different, non-adjacent functions in the same file. Same pathspec-commit mitigation already in both
  cards. Sufficient.
- **`tenancy/service.ts`:** only T-2-1 touches it (to call `assertWithinPlan` on invite), so there's no
  wave-2 overlap here despite it being a shared, sensitive file; noting it only because the task asked me
  to check it.

## Agreed contract changes
- `billing.checkout` / `billing.portal`: new procedures, additive, `billing.manage` permission fits
  (reused from existing `changePlan`). Fine as designed.
- `BillingStatus` new fields (`trialEndsAt` already exists; adding `currentPeriodEnd`,
  `cancelAtPeriodEnd`, and widening `status`): additive. **Caught and fixed:** the wave.md draft wrote
  the new status value as `"canceled"` (one L), but the existing `SUBSCRIPTION_STATUSES` DB enum and the
  current `BillingStatus.status` Zod enum both already use `"cancelled"` (two Ls). Left as drafted, this
  would have created two near-identical enum values instead of reusing the existing one. Fixed in
  `wave.md` and will commit the schema with `"cancelled"`, not `"canceled"`.
- `PLAN_LIMIT_REACHED`: already typed in `COMMON_ERRORS` (`contract/_base.ts`) — no change needed.
  `PAYMENT_REQUIRED` and `EMAIL_NOT_VERIFIED` are **not** typed anywhere in contracts today (checked
  `_base.ts` and every `contract/*.ts`); they're referenced only in the task cards' prose. Adding both to
  `COMMON_ERRORS` is additive and needed so `billing.checkout`/`.portal`, `changePlan` and the paid-action
  procedures can declare them and the web can match on `error.code` instead of parsing message strings.
- `submitting` added to `PO_STATES`: additive. Confirmed the backend already has a private notion of this
  state (`inventory/service.ts:852`, `:1150`, `:1192`, `:1234`, `:1399` all branch on
  `po.status === "submitting"` as a crash-safety intent state from wave 1/B-64) and currently coerces it
  to `"draft"` before it reaches the API — the contract has been lying about what state POs can be in.
  Checked every web/floor consumer of `PoState`: no exhaustive `switch` breaks, but
  `invai-web/src/components/po-badge.tsx`'s `TONE` map **does** fail `pnpm typecheck` in `invai-web`
  (confirmed by running it after the contract change) — TS7053, indexing a 5-key object literal with the
  now-6-member `PoState` union. `invai-floor` typechecks clean; `invai-backend` typechecks clean (its own
  `inventory/service.ts:852` already branches on `"submitting"` today). This is the one real, mechanical
  piece of breakage from this wave's contract change, and it's a one-line fix: add
  `submitting: "warning"` (or similar) to `po-badge.tsx`'s `TONE` object. Per `CLAUDE.md`'s "a breaking
  contract change must be fixed in every consumer the same day," this is `web-engineer`'s fix to land
  alongside T-2-2 or T-2-4 (whichever lands first) — the architect role rule is explicit ("MUST NOT:
  hand-edit consumer repos to absorb your change"), so I did not make this edit myself. Flagging it here
  so it isn't missed.
- `user.invited` payload `{ orgId, userId }` → `{ orgId, invitationId }`: **not strictly additive** (a
  field is renamed/replaced, not added), so per the architect rule I checked every consumer.
  `grep -rn "user.invited"` across all 8 repos (excluding `node_modules`) returns exactly one hit: the
  definition in `invai-contracts/src/events.ts`. Nothing emits it and nothing subscribes to it yet. Safe
  to change the payload shape now; would need an ADR and a deprecation window if anything consumed it
  after this lands.

## Stripe webhook design and out-of-order handling
The design (verify signature → dedupe on event id → handle `checkout.session.completed`,
`customer.subscription.*`, `invoice.payment_*`, plan/status changes only in the webhook handler) matches
the verify-first, dedupe-before-work shape decision 0009 already established for marketplace webhooks,
and out-of-order handling by comparing timestamps is the standard Stripe integration pattern.

**Caught and fixed:** the card said this dedupes "through `webhook_deliveries` (decision 0009)." That
table's `channel` column is `text(enumText(CHANNELS))` — a Postgres check constraint on the marketplace
`CHANNELS` enum (`etsy | amazon | shopify | tiktok | walmart | ebay | csv`), used identically across
`channelConnections`, `orders`, `webhook_deliveries` and every channel adapter. `stripe` is not, and must
not become, a member of that enum — it isn't a marketplace channel and nothing else in the codebase
treats billing as one. Reusing the table as drafted would have failed at the schema/insert level (or,
worse, someone would have "fixed" it by adding `"stripe"` to `CHANNELS`, which would then need handling
in every marketplace-channel switch across sync, adapters and the web channel settings page — the same
class of breakage the architect rule about exhaustive switches exists to prevent). **Fixed:** T-2-1 now
adds its own table in `db/schema/billing.ts` (e.g. `billing_webhook_events`, unique on Stripe event id,
system-only writes, same RLS-tenant/purge shape as `webhook_deliveries`) and `POST /webhooks/stripe` is
its own Hono route, not a case of the generic `/webhooks/:channel` dispatcher (which 404s on anything
outside `CHANNELS` — confirmed in `api/webhooks.ts:28-31`). This is within T-2-1's already-granted paths
(`db/schema/billing.ts` and its migration; `api/webhooks.ts` "add the Stripe route only").

## Label crash-safety design
Checked `shipping/service.ts` directly: `rateOrder` selects the order `for("update")` and then calls
`carrierAdapter().rate(...)` while that row lock is held, and `buyLabel` calls `carrierAdapter().buy(...)`
fully inside a `withTenant` transaction, both live network calls the audit already flagged (B-61, B-62,
B-67). The `labels` table (`LABEL_STATUSES = ["purchased", "voided", "refund_pending", "refunded"]`) has
no intent/in-flight state today, so there's no way to currently distinguish "we don't know if the carrier
charged us" from "nothing happened." The card's design — record an intent row with an idempotency key
inside the transaction, commit, call the carrier outside any transaction, record the result, and have a
retry read back from the carrier before buying again — is the correct fix and matches the project's
`idempotent-side-effect` pattern (`CLAUDE.md` rule 8). It needs the migration the card already asks for.
`pushTrackingForShipment` (`channels/service.ts:426`) has the identical problem today (called with a live
network call from inside a transaction) and currently only filters cancelled items when
`shipment.orderItemIds` is empty, not when it's populated, and doesn't check holds at all — so the card's
acceptance criterion 3 ("checks the items' state and holds at push time") is a real, verified gap, not a
belt-and-suspenders ask.

## Is T-2-5 too big for one card?
Borderline, and I flagged it rather than blocking on it. It spans two state machines (`ShipmentState` via
`buyLabel`/`rateOrder`/void, and `OrderItemState` via cancel/hold), a schema migration, and a
channel-behavior change (CSV items stop "shipping" at label-buy time). That's more surface than the other
four cards. Splitting it would push wave 2 past the 5-card cap the operating system sets, and the two
halves share the same crash-safety motivation ("a shop must never be charged twice or have a cancelled
order's tracking pushed"), so I left it as one card and added a note asking it be landed as two internally
sequenced commits (crash-safety first, cancel/hold-voids-label second), with `qa-engineer` checking each
half on its own evidence, and a rule that a third review round means splitting it for the next wave
instead of trying again.

## Better Auth 1.7 plugin feasibility
Checked `invai-backend/node_modules/better-auth@1.7.5` directly, not from training-data memory (per
`CLAUDE.md`'s lesson about this library):
- `plugins/two-factor/index.d.mts` exports a full `twoFactor()` plugin with TOTP, backup codes and a
  server/client API (`enableTwoFactor`, etc.) — feasible as specified.
- `emailVerification.sendVerificationEmail` is a core `betterAuth()` option
  (`dist/api/routes/email-verification.mjs` reads `ctx.context.options.emailVerification
  ?.sendVerificationEmail`), not a separate plugin — feasible, no plugin needed, just the option plus a
  mailer call (T-2-3 already scopes `lib/auth-mail.ts` for this).
- Password reset (`dist/api/routes/password.mjs`) exists as a core route — feasible.
No missing capability; T-2-3 is buildable against the installed version as written.

## Changes made
- `invai-docs/waves/2/wave.md`: fixed `"canceled"` → `"cancelled"` in the `BillingStatus.status` line;
  added `EMAIL_NOT_VERIFIED` to the error-codes-the-web-must-handle line and noted all three
  (`PLAN_LIMIT_REACHED`, `PAYMENT_REQUIRED`, `EMAIL_NOT_VERIFIED`) will be typed in `COMMON_ERRORS`;
  replaced the "dedupes through `webhook_deliveries`" line with the billing-specific dedupe table design;
  added a note on the `PO_STATES`/`user.invited` safety check with the consumer file found.
- `invai-docs/waves/2/T-2-1-stripe-billing.md`: acceptance criterion 2 rewritten for the new dedupe table
  and route, with the out-of-order comparison made concrete (store last-processed event's `created`).
- `invai-docs/waves/2/T-2-5-shipping-safety.md`: added a "Note from plan review" section on sequencing
  the card as two commits, without changing its acceptance criteria.
- (Product-manager also edited T-2-1 criterion 5 and T-2-3 criterion 1; see
  `plan-product-manager-r1.md`.)

## Next
Proceeding to commit the agreed contract stubs in `invai-contracts` on `main` (checkout/portal
procedures, `BillingStatus` fields with the corrected spelling, `PAYMENT_REQUIRED`/`EMAIL_NOT_VERIFIED`
in `COMMON_ERRORS`, `submitting` in `PO_STATES`, and the `user.invited` payload change), plus a
`NOT_IMPLEMENTED` stub in `invai-backend/src/modules/billing/router.ts` if the backend needs one to
typecheck.
