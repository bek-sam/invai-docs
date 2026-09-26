# Review of T-6-4 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer (backend `0e2822e`) + web-engineer (web `4817a72`) on Opus
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-backend-r-t64` (worktree @ `0e2822e`) `tsc --noEmit` | clean |
| `invai-backend-r-t64` `biome check .` | clean (256 files) |
| `invai-backend-r-t64` `tsup` (build) | success |
| `invai-backend-r-t64` `vitest run src/ai src/modules/ai` | 20/20 passing |
| `invai-backend-r-t64` (checked out to `6f957fe`, includes the migration fix) full `vitest run` | **511/511 passing** (matches the card's "511+ after 6f957fe"; at `0e2822e` alone, before the migration fix, it's 443/511 with 68 pre-existing `exported_at`/`refund_events` failures — not this card's, confirmed by diffing) |
| `invai-web-r-t64` (worktree @ `4817a72`) `tsc --noEmit` | 1 pre-existing error, `order-actions.tsx:79` (`FlagCode` missing `channel_edit_after_press`) — confirmed unowned by this card (`git diff f2ef447 4817a72 -- src/features/orders/order-actions.tsx` is empty) and already fixed on top-of-wave commit `b93f554` |
| `invai-web-r-t64` `biome check .` | clean (143 files) |
| `invai-web-r-t64` `vite build` | success |
| `invai-web-r-t64` `vitest run` | 76/76 passing |
| `scan-test-weakening.sh invai-backend-r-t64 3feb9ff` | 2 hits, both read and cleared (below) |
| `scan-test-weakening.sh invai-web-r-t64 f2ef447` | no hits |
| New backend tests run against `git archive 3feb9ff` (pre-card code) | **5/5 fail** as expected: real-SKU export, Shopify grouping, `CHANNEL_MISMATCH`, `publishDraft` CSV fallback, AC7 mock-forcing — the new tests are not tautological |

**Scan hits, read:**
1. `expect(rows[0]?.Title).toBeTruthy()` (`service.test.ts:311`) — a secondary check next to `rows[1]?.Title` being `""`; the real proof for real SKUs is the exact-match `expect(rows.map(r=>r.sku).sort()).toEqual([...skus].sort())` two lines below. Not weak on its own merit.
2. `if (env.mocks.ai) return mockProvider;` (`gateway.ts:29`, matched the scan's generic `if .*mock` production-code heuristic) — this is the pre-existing mock-provider switch (`env.mocks.ai ? mockProvider : anthropicProvider`), just split across two lines to add the AC7 branch below it. Not a test-only branch; it's the standing "no real key ⇒ mock" pattern documented in `CLAUDE.md`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Copy buttons | Yes | `drafts.$draftId.tsx`: `CopyIconButton` shown only when `draft.status === "approved"`, on title/tags/description, `navigator.clipboard.writeText` + toast; i18n keys present en/es. |
| 2. `exportCsv` rewrite | **Partially** — real SKUs: yes (see below and base-code test proof). Shopify branch: **new but not usable as shipped** — blocking finding #1. |
| 3. Publish status | Yes | New `PublishStatusSection` polls `ai.listings.publishStatus` every 2s while `publishing`, shows badge/error/pending-approval note/link; replaces the old `draft.publishedUrl` snippet. |
| 4. Credits ledger | Yes | `billing.tsx`'s `CreditLedgerTable` on `ai.credits.ledger`, infinite scroll, when/kind/model/tokens/credits columns, i18n present. |
| 5. B-101 | Mostly yes: | |
| — dead publish branch removed | Yes | `git diff` shows the whole `MaybeUpsert`/`getChannelAdapter`/`adapter.upsertListing`/`JSON.parse(conn.credentials)` block deleted; every channel now goes through `variantRowsForDraft` + `exportCsv`. |
| — stream charges on disconnect | Yes, for the common case | `runAssistant`'s `finally` now closes the inner generator and calls `finishJob` with `usageSoFar` (fed by a new `onUsage` callback the provider fires after each completed turn) and `stopReason: "aborted"`; `ask()`'s own `finally` mirrors this for its outer generator. Confirmed the mechanism (oRPC's `eventIterator` calls `.return()` on disconnect) is the one actually exercised — not assumed. **Caveat, not blocking:** if the disconnect happens *mid*-turn (the common case for a long assistant answer) rather than between tool-loop turns, `usageSoFar` only reflects the last *completed* turn's usage — any tokens Anthropic generated (and may bill) after that point aren't counted. This is a real accounting gap but a large improvement over the prior "stuck running, never charged" bug, and verifying Anthropic's actual billing behavior on a client-aborted stream isn't possible in this mock-only environment. Worth a follow-up card. |
| — no blank assistant messages on failure | Yes | `ask()`'s `finally` deletes the eagerly-inserted assistant row when `failed && !text && !toolCalls.length`. Note: this condition is keyed on `failed` (an exception), not on the disconnect path — a disconnect with zero text yielded still leaves a blank row. The AC's wording is "failed turns," which this satisfies; flagging the disconnect case as an optional note, not a blocker, since it's the same shape of bug but wasn't asked for here. |
| — dead routes removed | Yes | `tags`/`sku_suggestion`/`personalization_check` removed from `AiRoute`/`ROUTES`; confirmed no other reference to them anywhere in `src/ai`/`src/modules/ai`. |
| 6. Tests/evals pass | Yes | 20/20 (`src/ai`+`src/modules/ai`), 511/511 full backend (post-migration-fix), 76/76 web. |
| 7 (T-6-5). Demo guard | Yes | `aiProvider(companyId)` forces mock when `isSampleWorkspace(companyId)`, reusing T-6-5's helper (not reimplemented); `finishJob`'s cost now keys off `result.model === MOCK_MODEL`, not `env.mocks.ai`, so a sample workspace's cost is $0 for either reason. Test flips `env.mocks.ai=false` and proves a sample company still gets mock while a real one gets `anthropic`; fails on base code. |

## Blocking findings
1. **`invai-backend-r-t64/src/modules/ai/service.ts:784-814` (`variantRowsForDraft`) and `:708-746` (Shopify branch of `exportCsv`)** — the new Shopify CSV branch cannot actually distinguish variants on import. `variantRowsForDraft` selects `colorCode`/`sizeCode` from `blankVariants` (line 794-795) but discards both and returns only `{ content, sku }` (line 814); `exportCsv`'s Shopify branch then hardcodes `"Option1 Value": ""` on the first row of every `Handle` (line 729) and omits `Option1 Value` entirely on every continuation row (lines 738-743, filled as `""` by `toCsv`). Shopify's product-CSV importer distinguishes variants under one `Handle` by their option values, not by SKU alone — every row in a multi-variant listing therefore carries the same (blank) `Option1 Value`. **Failure scenario:** a shop approves a Shopify draft for a 6-color × 6-size product, exports the "36-row" CSV the report describes, and uploads it to Shopify's own bulk product importer; Shopify sees 36 rows under one `Handle` with an identical blank size/color value and either rejects the file (duplicate variant combination) or silently keeps only the last row, losing 35 of the 36 SKUs — the exact problem AC2 was written to fix, just moved from "no Shopify branch" to "a Shopify branch that doesn't work." No test in `service.test.ts` checks `Option1 Value` content (only `Handle`, `Variant SKU`, and that `Title` is blank on row 2+), so this passed CI and the author's own curl verification, which checked row count and SKUs but not option values.
   - Fix: thread `colorCode`/`sizeCode` (or the variant's display `color`/`size`) through `variantRowsForDraft`'s return type into `exportCsv`'s rows, and set `Option1 Name`/`Option1 Value` (and a second option for the other axis, e.g. `Option2 Name: "Color"`/`Option2 Value`) per row, not just on the handle's first row.

## Checks
- [x] Only owned paths changed — backend: `src/ai/**`, `src/modules/ai/**` only (`git diff --stat 3feb9ff 0e2822e`, both files match). Web: listings routes, `settings/billing.tsx`, i18n only (`git diff --stat f2ef447 4817a72`).
- [x] Nothing outside scope — no contract/db changes; report correctly explains why `CREDIT_KINDS`/schemas were left alone.
- [x] Tests exercise the behavior, and none were weakened — scan hits read above, both cleared; new tests proven to fail on pre-card code.
- [x] Tenancy / idempotency / money in cents / en+es text — N/A new tables; no new webhooks; credits are integer counts (not cents, correct per contract); i18n keys added 1:1 in en/es, no raw English found in the diff.
- [x] Decisions recorded where needed — none needed; nothing here reopens a prior decision.

## Optional notes (not blocking)
- `production_partner: "DTF transfer printer"` in the Etsy CSV branch is unchanged, pre-existing (present verbatim in `3feb9ff`) — this is the already-known M-23 gap (a text column, not Etsy's structured `production_partner_ids`, and wrong for an in-house printer). Out of this card's scope (AC2 asked for real SKUs/Shopify branch only), but flagging again since compliance-officer's review covers CSV format.
- Mid-turn disconnect token accounting (see AC5 note above) — worth a follow-up card, not a blocker for this one.
- `ask()`'s empty-message cleanup doesn't cover the disconnect path (only `failed`) — optional, same shape of bug, not asked for by AC5's literal wording.
- Screenshots: the task named 3 screenshots to review; none exist on disk (the report says "6 screenshots taken, not saved to disk"). I relied on code + test evidence instead of a live browser pass, given the machine load; nothing in the diff suggests a UI issue the code review wouldn't have caught, but this is a real evidence gap worth closing before push.
