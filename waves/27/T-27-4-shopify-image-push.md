# T-27-4: Shopify adapter: push product images (mock + live), idempotent

| Field | Value |
|---|---|
| Wave | 27 |
| Scope ref | `product/scope.md#listing-photos` (SCR-008; scope item 2 Shopify API adapter) |
| Spec | `specs/listing-photos.md` |
| Owner | integrations-engineer |
| Reviewer | reviewer (fable) |
| Co-reviewers | security-reviewer (opus, outbound writes to a shop's store, token use) |
| Risk flags | outbound, idempotency |
| Model | opus |

## Read first
- `.claude/agents/integrations-engineer.md`, `idempotent-side-effect`; `invai-backend/src/integrations/channels/{types,index}.ts`, `shopify/{client,live,mock,inventory}.ts` and their tests (the `@idempotent` and throttling patterns); research 10 Shopify sections; Shopify Admin GraphQL docs for the API version the client pins (`productCreateMedia` or `productUpdate` media input, `stagedUploadsCreate` if remote URLs aren't accepted; cite the doc URL and version).
- The contract's `pushToShopify` (`invai-contracts/src/contract/photos.ts`) for how `productRef` is chosen.

## Owned paths (edit)
- `invai-backend/src/integrations/channels/**` (adapter interface: optional method; Shopify live + mock; other channels unchanged)
- `invai-backend/shopify.app.toml` scopes, if `write_products`/`write_files` must be added (say so in the report: a scope change means shops re-consent; the owner submits app changes)

## Acceptance criteria
1. `ChannelAdapter.pushProductImages?(conn, {productGid, images:[{url, alt, filename}], idempotencyKey})` exists as in `waves/27/wave.md` (T-27-3 maps the listing to the gid); only Shopify implements it. `shopify.app.toml` lacks `write_products` today (~line 14): add it and say so; the shop re-consent is an owner step the tech lead files in the inbox.
2. Mock: records pushed images per (connection, product, filename) in its store; the same idempotency key twice → second call returns them as `skipped`, no duplicates; unknown product → typed NOT_FOUND-style error.
3. Live: GraphQL mutation(s) with alt text, user errors mapped to typed errors, throttling/backoff using the existing client helpers, dedupe on retry (query existing media by filename/alt marker before creating, or the API's idempotency directive if the pinned version supports it). Tests stub HTTP and inspect the request bodies; no real call.
4. If the needed OAuth scope isn't in the app config today, the adapter returns a typed "reconnect needed" error instead of failing silently, and the report names the scope change.
5. Existing channel tests stay green; no other channel changes.

## Verification
- `pnpm vitest run --reporter=dot src/integrations/channels 2>&1 | tail -n 40`; full backend suite once at the end (pipefail, log, timeout 600000).

## Out of scope
- The photos job (T-27-3), Etsy/Amazon/TikTok/Walmart image APIs (approvals pending; zip download covers them).

## Commit and report
- Commit own paths, co-author line; don't push. Report `invai-docs/waves/27/reports/T-27-4.md` (≤ 60 lines); reply ≤ 8 lines.
