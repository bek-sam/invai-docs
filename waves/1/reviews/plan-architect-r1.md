# Architect review of the Wave 1 plan (round 1)

- Reviewer: architect
- Author: tech-lead
- Verdict: **approve** — three required changes found, all applied directly to the cards and to `wave.md` (see below); nothing left blocking.

## What I checked
`wave.md` and all 5 `T-1-*.md` cards against: path overlap, interface soundness, migration/RLS design, the two idempotency designs (PO submit, webhook dedupe), the prod-mock guard, and hidden inter-card dependencies. Read `env.ts`, `auth.ts`, `db/migrate.ts`, `api/webhooks.ts`, `modules/channels/{sync,jobs}.ts`, `modules/tenancy/service.ts`, `modules/inventory/service.ts` (+ router), `integrations/suppliers/index.ts`, `db/schema/{inventory,channels,_shared}.ts`, `modules/vendors/service.ts` to check each card's acceptance criteria are actually buildable inside its owned paths.

## Owned-path overlap between parallel cards
No file appears in two cards' owned-path lists. Confirmed clean: T-1-1 (`env.ts`, `api/app.ts`, `mailer.ts` config, package/tsup), T-1-2 (`api/webhooks.ts`, `integrations/channels/**`, new `db/schema/webhooks.ts`), T-1-3 (`integrations/suppliers/**`, `modules/inventory/**`, `db/schema/inventory.ts`), T-1-4 (`auth.ts`, `modules/tenancy/**`, `modules/vendors/**` invite code, two web files), T-1-5 (`db/reference/**`, one hook each in `migrate.ts`/`seed/index.ts`). Good.

## Required changes (applied)

**1. T-1-2's owned paths didn't cover where its acceptance criteria actually live.** The card marked all of `src/modules/**` read-only ("call existing functions; don't edit"), but I traced the code: `verifyWebhook`, `processWebhook` and `completeShopifyOAuth` — the functions AC2 (Etsy fetch-by-ID), AC4 (Shopify dedupe) and AC5 (OAuth state expiry) require changing — all live in `modules/channels/sync.ts`, and there's no `channels.etsy.webhook` job at all yet (only `channels.shopify.webhook` in `modules/channels/jobs.ts`). As written, T-1-2 could not meet its own acceptance criteria without either violating ownership or leaving Etsy webhooks unimplemented.
   - *Changed:* `T-1-2-verified-webhooks.md` owned paths now grants `modules/channels/sync.ts` (only the three named functions/helpers) and `modules/channels/jobs.ts` (only to register the Etsy job) to this card — the same pattern T-1-3 already uses to grant inventory paths to integrations-engineer. The rest of `modules/**` stays read-only. Noted in `wave.md`'s "Agreed interfaces" too.
   - Also found and flagged in the card: `processWebhook`/`verifyWebhook` pick mock-vs-live using `env.mocks.shopify` **regardless of the `channel` argument** — a latent bug that would make Etsy verify/process against the wrong adapter. Added as a required note on AC2.

**2. T-1-3 AC2's "call the supplier outside the transaction" is incompatible with the current call chain.** `modules/inventory/router.ts` wraps the *entire* `submitPo` call in one `withTenant(...)` transaction, and today `submitPo` calls `adapter.placeOrder` mid-transaction while holding the PO row's `FOR UPDATE` lock (confirmed at `inventory/service.ts:1064-1118`, exactly the audit's B-64 finding). A function that receives one pre-opened `tx` covering the whole call cannot "commit, then call the supplier, then commit again" — that's three transactions, not one.
   - *Changed:* added a note under AC2 in `T-1-3-supplier-safety.md`: `submitPo`'s signature must change to manage its own transaction boundaries (mark `submitting` → commit → call supplier → mark `submitted`/failed → commit), and `router.ts`'s call site changes accordingly. Also confirmed no contract change is needed for *this* idempotency key — `po.poNo` is already unique per company and stable, so it can be reused as the supplier-facing dedupe key.

**3. T-1-3 AC3 (`receivePo` idempotent) needs a contract change nobody owns in this wave.** "A client key, or a receipt id" that actually distinguishes a network retry from a legitimate second delivery of the same quantity requires a new field on the request. `ReceiveInput` in `invai-contracts/src/schemas/inventory.ts` currently has only `purchaseOrderId`, `locationId`, `lines[]`, `note` — no such field. `invai-contracts/**` is architect-owned and this wasn't listed in `wave.md`'s "Agreed interfaces," so T-1-3 as written would hit a wall it can't resolve inside its own paths.
   - *Changed:* added a new optional, additive `idempotencyKey` field on `ReceiveInput` to `wave.md`'s "Agreed interfaces," to be committed by the architect as a stub before T-1-3's build starts (per the wave process: "have the provider commit stubs first"). Added architect as a co-reviewer on T-1-3 in both the card and the `wave.md` cards table, since this is now a contract change (operating-system.md's review table requires it).

**4. T-1-1's required-boot-keys list (AC2) omitted `SHOPIFY_API_KEY`/`SHOPIFY_API_SECRET`.** These gate `env.mocks.shopify`, a platform-wide app credential exactly like `EASYPOST_API_KEY` or `ANTHROPIC_API_KEY` — without them, production would boot fine and silently run a real shop's Shopify connection on the mock adapter, which is precisely what this wave exists to prevent.
   - *Changed:* added `SHOPIFY_API_KEY`/`SHOPIFY_API_SECRET` to the required-key list in `T-1-1-build-and-prod-guard.md`, with a note explaining why `SS_ACTIVEWEAR_*` is deliberately *not* in that list (T-1-3 makes supplier credentials tenant-owned only, so there's no platform-wide supplier mock left to guard once it lands — this only holds if T-1-1 and T-1-3 both ship in this wave, which they do).

## Migration and table design
- `webhook_deliveries` (T-1-2, new): dedupe on `(channel, delivery_id)`, kept 30h+, purge job. The card correctly leaves the tenancy call to the implementer with a reasoned choice, and the right choice is **no `company_id`/no RLS** — a delivery ID is meaningful before any tenant is resolved (webhooks arrive pre-auth), and this matches the existing pattern for genuinely global tables (`trademark_marks`, `plans` via `publicReadPolicy`). No RLS gap: CLAUDE.md's "every tenant table has company_id and RLS" rule is about tables that *hold tenant data*, which this doesn't.
- `purchase_orders`/`purchase_order_lines` (T-1-3): already have `tenantPolicy(...)` + `.enableRLS()`. The new `submitting` PO status and idempotency-key column are additive; no RLS concern.
- T-1-5's `db/reference/**` tables: same global/`publicReadPolicy` pattern as trademarks today. Sound.
- No migration collisions expected beyond what `wave.md` already calls out (T-1-2 and T-1-3 each add one; later card regenerates on journal collision).

## Idempotency designs
- **Webhook dedupe (T-1-2):** sound in shape — verify-then-persist-then-enqueue, unique on `(channel, delivery_id)`, reject (don't fall back to a random UUID) when the dedupe header is missing. This closes the exact gap in `api/webhooks.ts` today (Shopify already falls back to `crypto.randomUUID()` on a missing header at line 28; the generic `/:channel` route enqueues before verifying anything at all for Etsy).
- **Supplier PO submit (T-1-3):** sound in shape once the transaction-boundary fix above is applied; without it, the "outside the transaction" requirement is not achievable with the current call chain.

## Production mock guard (T-1-1)
Good design: additive `env.allowMocks`, one loud combined error listing every missing key, `/health` stops leaking `mocks`, `NODE_ENV=test`/development behavior unchanged. The `ALLOW_MOCKS=true` escape hatch for demo/staging is the right shape — it's explicit opt-in, not a default, and it still logs a warning on every start. See required change 4 above for the one gap in which keys it checks.

## Hidden dependencies (beyond the required changes above)
- T-1-4's AC1 ("creates a real Better Auth organization invitation") should call Better Auth's *server-side* invitation API, not an HTTP path — `/organization/invite-member` is in `auth.ts`'s `DISABLED_AUTH_PATHS`. This is achievable inside T-1-4's owned paths (`auth.ts`, `modules/tenancy/**`) and is the established pattern here (InvAI procedures wrap Better Auth server calls), so no card change needed — just flagging so the implementer doesn't try the disabled HTTP path first.
- T-1-4 AC3 (unify vendor invite onto the same route) looked riskier than it is: `modules/vendors/service.ts` already creates a real Better Auth `invitations` row for a not-yet-registered vendor (it eagerly creates the vendor `companies` row too) — the bug is only that the email then links to a separate, custom `/vendor/accept?token=` flow instead of the invitation's own id. Fixing the link is enough; no eager-org-creation redesign needed.
- T-1-1 and T-1-3 both touch `env.mocks.supplier`/`getSupplierAdapter` semantics (T-1-1 by omission, T-1-3 by direct edit); order doesn't matter since T-1-1 never reads `SS_ACTIVEWEAR_*` after this review's fix, but call this out at integration if T-1-3 slips to a later wave — T-1-1's rationale note would then be wrong and need updating.

## Notes (not blocking)
- Consider generalizing `api/app.ts`'s `noMockWebhooksInProd` middleware (currently Shopify-only) once T-1-2 lands, so it isn't silently Shopify-specific forever. Not needed this wave since Etsy has no live adapter yet.
- T-1-3 AC2's "a test simulates a commit failure after the supplier accepted" is easiest to write once the transaction-boundary split (required change 2) exists — inject a failure into the second (mark-submitted) transaction and assert a retry doesn't call the supplier twice, rather than trying to kill the process mid-flight.
