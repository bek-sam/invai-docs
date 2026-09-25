# T-3-1: Shopify adapter complete

| Field | Value |
|---|---|
| Wave | 3 |
| Scope ref | `product/scope.md#mvp-in` item 2; always-in-scope: compliance |
| Backlog | B-28, the rest of B-63, B-06, B-04 (mutation), B-05 (Shopify expiring tokens), B-99 (poller skips pending, error and trial-expired connections) |
| Owner | integrations-engineer |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer, compliance-officer (B-06) |
| Risk flags | webhooks, pii, marketplace-policy |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/integrations/channels/shopify/**`, `integrations/channels/{index,types}.ts`
- `invai-backend/src/api/webhooks.ts`
- `invai-backend/src/modules/channels/{sync,jobs,service}.ts` (the poller, the webhook processing, `disconnect`) — **except** the `importCsv` function in `sync.ts` (roughly lines 73-176): that's T-3-4's. Touch only your hunks there if you must, and coordinate before committing.
- New `invai-backend/src/modules/privacy/**` (the compliance-request handlers), plus a schema and migration if needed
- New `invai-backend/shopify.app.toml`
- tests next to these files

## r1 review note (architect + PM)
This card is large: 9 acceptance criteria spanning order/inventory correctness (B-28, B-63, B-04, B-99), token lifecycle (B-05) and a brand-new compliance/privacy subsystem (B-06) with its own co-reviewer. If it runs long, the tech lead should consider splitting B-06 (compliance webhooks + `modules/privacy/**`) into its own card in a later slot — the seam is clean (new module, new webhook `kind`), it just needs one hook added to `handleWebhook` in `sync.ts` to dispatch `customers/data_request`, `customers/redact` and `shop/redact` events. Not required for this pass; flagging for capacity planning.

## Evidence
`build/audit-2026-09-24.md` §A-BE B-63; backlog B-04, B-05, B-06, B-28; `research/10-marketplace-engineering-rules.md` (Shopify section).

## Acceptance criteria
1. **Paid orders only:** webhooks import only paid orders (`financial_status` paid or partially_paid). Pending or COD orders are skipped and logged. The poll uses `updated_at` and pages through everything that changed, so it catches refunds, voids and cancels.
2. **Line items:** pagination beyond 100.
3. **Throttling and PII:** the poll respects `throttleStatus`. Without Level 2 protected-customer-data access, PII fields are stored as null, not as fake values.
4. **Webhook subscriptions:**
   - Subscription failures mark the connection `degraded` with a reason, visible in `channels.health`.
   - `disconnect` unsubscribes the webhooks and revokes the token (uninstall where possible).
5. **Compliance webhooks (B-06):** always in scope (`scope.md` "always in scope: compliance", and these are also a Shopify App Store requirement, i.e. marketplace approval — see `product-manager-r1.md`).
   - `customers/data_request`, `customers/redact` and `shop/redact` are verified and deduped.
   - `redact` removes or anonymises that customer's PII in orders and addresses **synchronously, inside the webhook handler** (no batch/delay — "the required window" was untestable as written; this makes it a concrete, testable criterion: PII is gone by the time the 200 is returned), and logs it.
   - `data_request` creates a privacy-request record for the owner to fulfil.
   - `shopify.app.toml` declares them.
6. **Inventory mutation (B-04):** `setAvailability` uses `inventorySetQuantities` with `changeFromQuantity` (compare-and-set) and the `@idempotent` key. A mismatch retries once with fresh data.
7. **Expiring offline tokens (B-05):** refresh before expiry, rotate the stored encrypted token, and flag the connection when a refresh fails.
8. **Poller:** skips connections in `pending_approval`, `error` (older than a backoff) and trial-expired companies. There's no `sync_failed` spam every 10 minutes.
9. **Tests:** fetch-mocked tests cover the paid filter, pagination, throttling, the compliance handlers, `changeFromQuantity` and token refresh.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-backend, with your test DB.
- For real on your port with mock Shopify:
  - post a signed `orders/create` with pending payment (skipped) and one that's paid (imported);
  - `customers/redact` (PII gone);
  - disconnect (unsubscribe called).

## Out of scope
- UI for the connection health (B-85). A real Shopify app listing (OI-2).
