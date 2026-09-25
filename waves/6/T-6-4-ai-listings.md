# T-6-4: AI listings: copy, export, publish status, credits
Scope: item 10. Backlog: B-89, B-101.

## Owned paths
- backend: `src/ai/**`, `modules/ai/**`
- web: the listings routes and features, the credits section of `settings/billing.tsx`, own i18n keys
- tests

## Acceptance criteria
1. **Copy buttons** for the title, tags and description on approved drafts for CSV channels.
2. **`exportCsv`:** new contract procedure `ai.listings.exportCsv({ draftIds, channel })` → `{ key: string }` (exact stub in `wave.md`). Backend `exportCsv()` (`modules/ai/service.ts:650`) changes signature from `(channel, content, sku)` to `(channel, rows: { content, sku }[])`, one row per **variant** (join the draft's `designId`/`productId` to `catalog.variants` for real SKUs), not one row per draft and not a placeholder SKU. Etsy already has a branch; **Shopify has none today** — it falls through to the generic fallback — so a proper Shopify product-CSV branch (one `Handle` per draft, `Variant SKU`/`Variant Price` per row) is new work, not a rename.
3. **Publish status** (`ai.listings.publishStatus`) is shown with its failures.
4. **Credits:** AI credit history (`ai.credits.ledger`).
5. **B-101:**
   - remove the dead API publish branch (`modules/ai/service.ts` ~732-747, it runs `JSON.parse` on encrypted credentials);
   - the assistant stream (`ai/gateway.ts`'s `runAssistant`, driven from `modules/ai/service.ts`'s streaming handler ~880-963) finishes its job and charges tokens even when the client disconnects — an async generator only runs its post-`yield` cleanup if something calls `.return()`/keeps iterating; verify what the router does to the generator on an aborted HTTP request before assuming a `finally` block alone fixes this;
   - failed turns don't save empty assistant messages;
   - `ai/models.ts`'s `ROUTES` has entries (`tags`, `sku_suggestion`, `personalization_check`) with no matching prompt in `ai/prompts/index.ts`'s `PROMPTS` — either add the prompts or remove the unused routes.
6. **Tests and evals:** the existing eval or mock tests still pass.

## Verify
Run tsc, lint, test and build. Browser pass on a DB copy: approve a draft, copy, export an Etsy CSV (check the SKUs), view the credits history. At most 6 screenshots.
