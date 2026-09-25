# Wave 3 plan review — architect, round 1

**Verdict: approve with clarifications applied** (directly to `wave.md` and the four cards; listed below, and cross-referenced from the cards).

## Path overlaps
- **`sync.ts` (T-3-1 / T-3-4):** real. T-3-1's owned-paths line for `modules/channels/{sync,jobs,service}.ts` didn't carve out `importCsv`, even though T-3-4's card already says "touch only the import-CSV function." Added the carve-out to T-3-1's card too, so both sides read the same boundary (`importCsv` is lines ~73-176 of `sync.ts` today).
- **`app.ts` / `webhooks-carriers.ts` (T-3-2):** the one mount line is fine, but T-3-2 also needs the `noMockWebhooksInProd`-style guard extended to `/webhooks/easypost` (a mock EasyPost provider will sign with a fixed dev secret exactly like mock Shopify does) and should mount as its own top-level route, not nested, so it can't be shadowed by `webhooks.post("/:channel")`. Added to the card.
- **Shipping files split T-3-2 / T-3-4:** clean as written — T-3-2 owns `shipping/jobs.ts` (tracker + sweep), T-3-4 gets a new `shipping/batch.ts` and registers in the worker registry, not in `jobs.ts`. No conflict found in the actual file.

## Is T-3-1 too big?
Yes, leaning toward too big. 9 acceptance criteria across three genuinely different concerns: order/inventory correctness (B-28, B-63, B-04, B-99), Shopify token lifecycle (B-05), and a new compliance/privacy subsystem (B-06) with its own dedicated co-reviewer. The compliance piece is a clean seam — new `modules/privacy/**`, one dispatch hook into `handleWebhook` — so it could become its own card in a later wave slot without real coupling cost. Not mandating a split now (would require rescheduling a 3-4-builder wave that's presumably already staffed); flagged on the card for the tech lead to decide if it runs long.

## T-3-4's async contract changes and their web consumers
Checked both. `invai-web/src/routes/_app/settings/channels.tsx:260` and `invai-web/src/routes/_app/shipping.tsx:127-145` both read the mutation's return value as the *finished* result, synchronously — neither is in any wave-3 owned-paths list, so this was a real gap. Designed stubs (full detail in `wave.md`):
- `ImportReport`: append `status: "queued"|"running"`, add `jobId: Id.nullable().optional()` — additive. A ≤300-row inline/sync fast path means `channels.tsx` needs no change; only large imports return `"queued"`.
- `BatchBuyResult`: add `status: "completed"|"queued"`. **No sync fast path here** — the card's own verification (kill the worker mid-20-label batch) only proves anything if `batchBuy` always goes through the real job, so it must always return `"queued"` now. That *does* break `shipping.tsx`. Gave T-3-4 a narrow, named grant on that one file (the `batch` mutation only), same-day, per CLAUDE.md's contract-change rule, with a web-engineer co-review on that hunk.

## T-3-3's listings schema
Already fully built: `db/schema/channels.ts:84-138` has `listings` and `listingVariants` with `companyId`, RLS (`tenantPolicy` + `.enableRLS()`), and every field the acceptance criteria need (`channelSku`, `blankVariantId`, `designId`, `quantityCap`, `lastPushedQty`). No migration should be needed — flagged on the card so the implementer doesn't write a speculative one. The real gap is exactly what the audit said (B-65): `channels/sku.ts` and `channels/service.ts` currently never write either table.

## EasyPost HMAC
Doesn't exist. No verification function and no webhook secret anywhere in `integrations/carriers/**` or `env.ts` (Shopify has both: `verifyShopifyHmac` / `SHOPIFY_API_SECRET` in `shopify/common.ts` and `env.ts`). Designed the equivalent for T-3-2: `EASYPOST_WEBHOOK_SECRET` in `env.ts` (one named line, outside T-3-2's normal paths, granted explicitly — coordinate with T-3-4's owner since `env.ts` is otherwise backend-foundation's), a mock-secret fallback matching the Shopify pattern, and `timingSafeEqual`-based verification of `HMAC-SHA256(secret, rawBody)` against the `x-hmac-signature` header.

## Hidden dependencies found
1. **`markInTransit`/`markDelivered` signatures were wrong in `wave.md`.** Real signatures: `markInTransit(tx, ctx, shipmentId)` — no `at` at all — and `markDelivered(tx, ctx, shipmentId, at = new Date())` (`shipping/service.ts:1690,1717`), not `(shipmentId, at)` for both as originally written. Corrected in `wave.md`; flagged that `markInTransit` needs an `at` param added (additive) if T-3-2 needs the real carrier-scan time for out-of-order comparisons.
2. **New carrier webhook dedupe table** needed exact design so T-3-2 doesn't improvise against decision 0009: `carrier_webhook_events`, nullable `companyId`, `provider`/`eventId` unique, RLS, system-only writes (revoke insert/update/delete from `invai_app`, same as migration 0007). Full shape written into `wave.md`.
3. **T-3-4's contract change requires touching a file outside its owned paths** (see above) — this was the biggest hidden dependency; the card as written would have either broken `shipping.tsx` silently or left T-3-4 blocked with no one assigned to fix the consumer.

No new ADR needed — the carrier dedupe table extends decision 0009's stated pattern rather than making a new call. Reviewed against `architecture-as-built.md` conventions (money in cents, additive contract rule, `withSystem`/`withTenant` split) — nothing else contradicts them.
