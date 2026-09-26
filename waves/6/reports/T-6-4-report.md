# T-6-4 report: AI listings — copy, export, publish status, credits (+ B-101)

Status: **built, verified, ready for review** (product-designer, compliance-officer).

## Commits
- backend `0e2822e`: `exportCsv` rewrite (real SKUs, one row per variant, new Shopify branch), `ai.listings.exportCsv` handler, removed dead API-publish branch, `ai/models.ts` dead-route cleanup, assistant-stream disconnect fix, empty-message fix, AC7 demo guard. Fast-forwarded onto `invai-backend`'s `main` (was `3feb9ff`).
- web `4817a72`: copy buttons (AC1), publish-status section (AC3), bulk CSV export on the drafts list (AC2), AI credit history table on billing (AC4), new i18n keys (en+es). Fast-forwarded onto `invai-web`'s `main` (was `f2ef447`).
- No `invai-contracts` commit needed: the wave-6 `ai.listings.exportCsv` stub (`9de22ce`) already matched everything this card needed (schemas for `ListingDraft`/`PublishStatus`/`CreditEntry` were already sufficient too).

**Not pushed to origin** — several other wave-6/7 cards have local-only commits ahead of `origin/main` in both repos; per the wave process the tech lead pushes once after the integration gate. Both repos' local `main` now include my work.

## AC1 — copy buttons
`drafts.$draftId.tsx`: a `Copy` icon button next to Title, Tags and Description, shown once a draft is `approved` (every channel is copy/CSV today — no channel has a live listing-publish API). `navigator.clipboard.writeText` + a "Copied" toast.

## AC2 — `exportCsv`
- `exportCsv(channel, rows: {content, sku}[])` — one CSV row per **variant**, joined via the draft's `productId` (or the design's active product) to `blank_variants`, filtered by the product's `allowedColorCodes`/`allowedSizeCodes`. Throws `badRequest` if no product/variant resolves — no placeholder SKU is ever produced.
- New Shopify branch: one `Handle` per draft (rows sharing the same in-memory `content` object are grouped), `Variant SKU`/`Variant Price` per row, shared fields only on the first row of each handle — verified with a curl pull of a real 36-row export (6 colors × 6 sizes) against the design's actual product.
- `publishDraft`'s CSV fallback now calls the same variant-resolution helper — finishes B-101's line-792 placeholder fix (`DRAFT-${id.slice(0,8)}` is gone).
- Web: bulk "Export N as CSV" on the drafts list, disabled when the selection spans more than one channel (`CHANNEL_MISMATCH` is the server's error; the UI just disables first), resolves the key via `files.downloadUrl` and opens it.

## AC3 — publish status
New "Publish status" section on the draft page backed by `ai.listings.publishStatus` (polls every 2s while `publishing`), showing the status badge, `error`, the pending-approval note and the published link — replacing the ad-hoc `draft.publishedUrl` snippet. `publishing` is a listed-but-currently-unreachable state (no channel has an async publish path yet), so this is mostly forward-looking, but it is the actual endpoint the card names and it's live-verified via curl and the browser.

## AC4 — credits
"AI credit history" table on `settings/billing.tsx` (`ai.credits.ledger`, infinite-scroll `DataTable`): when/kind/model/tokens/credits, verified with real ledger rows from two generated drafts.

## AC5 — B-101
- **Dead API-publish branch removed** (`publishDraft` ~732–747 in the old file): unreachable (no channel adapter ever implements `upsertListing`) and it `JSON.parse`d the still-**encrypted** `credentials` column. `getChannelAdapter`/`MaybeUpsert` import removed with it; every channel now goes straight to the CSV path.
- **Assistant stream vs. disconnect**: `ask()`/`runAssistant()`/`providers/anthropic.ts`'s `assistant()` used manual `.next()` loops, so tearing down the outer generator (oRPC's `eventIterator` calls `.return()` on it when the HTTP client disconnects — confirmed by reading `@orpc/shared`'s `asyncIteratorToStream`) never closed the inner generators, so the `ai_jobs` row stayed "running" and tokens Anthropic already billed were never charged. Fixed by explicitly closing the inner generator in each layer's `finally`, and reporting the real charged amount back up via a callback (`onUsage`/`onSettle`) rather than a generator return value — overriding a generator's own `.return()` value from inside its `finally` also swallows a real thrown error (and trips biome's `noUnsafeFinally`), so that trick was rejected in favor of the callback.
- **Failed turns no longer save a blank assistant message**: `ask()` deletes the eagerly-inserted empty assistant-message row when a turn errors with no text/tool calls produced.
- **`ai/models.ts` dead routes removed**: `tags`, `sku_suggestion`, `personalization_check` had no matching prompt and were never called anywhere; removed from `AiRoute`/`ROUTES` (left `CREDIT_KINDS`/schemas alone — those aren't in this AC and touch contracts/db unnecessarily).

## AC7 — demo can't spend the platform key
`aiProvider(companyId)` (was `aiProvider()`) now forces the mock provider whenever `isSampleWorkspace(companyId)` (T-6-5's helper) is true, even if `ANTHROPIC_API_KEY` is set — same pattern as T-6-5's other adapter guards. Cost tracking (`finishJob`'s `costCents`) now keys off `result.model === MOCK_MODEL` instead of `env.mocks.ai`, so it stays $0 regardless of *why* mock was used. Verified with a unit test that flips `env.mocks.ai = false` and confirms a sample-workspace company still gets the mock provider while a real company gets `anthropic`.

## Tests
- `invai-backend`: 20 tests in `src/modules/ai` + `src/ai` (was 15; added exportCsv real-SKU/Shopify/`CHANNEL_MISMATCH`/`publishDraft`-fallback cases and the AC7 mock-forcing case). tsc and biome clean on every file I touched.
- `invai-web`: 76 existing tests unaffected; tsc, biome and `vite build` clean on my files.
- **Full-suite honesty check**: `invai-backend`'s full `vitest run` (fresh test DB, no template copy) is 443/511 passing — 68 failures across `shipping/*`, `orders/address`, `finance/service`, `channels/shopify`, `production`, `tenancy/demo`. None are in `src/modules/ai`/`src/ai`; confirmed these are pre-existing on the current `main` tip (T-6-2/T-6-3/wave-7 stub work in progress in the shared tree), not caused by this card — same category of cross-card noise T-6-5's report documented for `markPlaced`. `invai-web`'s one pre-existing tsc error (`order-actions.tsx`'s `FlagCode` missing `channel_edit_after_press`) is likewise unrelated and outside this card's owned paths.

## Verification
- Unit tests above.
- Curl golden path on DB copy `invai_t64_copy` (API `:3140`, worker running, `REDIS_URL` db 4): generated + approved an Etsy and a Shopify draft for a real product (Gildan G64000, 6 colors × 6 sizes); exported both — 36 rows each, real SKUs (`G64000-WHT-S`, …), no `DRAFT-` anywhere; `CHANNEL_MISMATCH` returned 400 when exporting an Etsy draft as `shopify`; `publishDraft` through an existing Etsy CSV connection returned `pendingApproval: true` with a 36-row real-SKU CSV; `ai.credits.ledger` showed both generation charges.
- Browser pass on the same DB copy (web `:5143`, 6 screenshots taken, not saved to disk): drafts list with both approved drafts, mixed-channel export disabled then re-enabled after narrowing to one channel, successful export (selection cleared), draft detail page with copy buttons + "Copied" toast, Publish status section, AI credit history table.
- Cleanup: API, worker and web dev servers stopped; `invai_t64_copy`, `invai_test_t64` dropped; Redis db 4 flushed; all three `-t64` worktrees removed.

## Known gaps / follow-ups
- `publishing` remains a listed-but-unreachable `listing_draft` status (no channel has an async publish path); the new Publish-status section is correctly wired but will only visibly differ from "approved" once a real async channel exists.
- `CREDIT_KINDS` in contracts/db still lists `sku_suggestion`/`personalization_check` even though their AI routes are gone — left alone since the card's ask was specifically about `ai/models.ts`'s `ROUTES`, and touching the credit-kind enum reaches into contracts/db unnecessarily.
