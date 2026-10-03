# Review of T-27-4 (round 1)

- Reviewer: reviewer on fable
- Author: integrations-engineer on opus (invai-backend `3f4deae`)
- Verdict: changes-required

## Evidence I re-ran
Committed tree only (`git archive 3f4deae` → `/tmp/review-T-27-4`, node_modules symlinked; the working tree holds another card's uncommitted `src/ai/**`), `OPENAI_API_KEY= ANTHROPIC_API_KEY=`.
| Command | Result |
|---|---|
| `tsc --noEmit` | exit 0 |
| `biome check .` | 485 files, exit 0 |
| `vitest run --reporter=dot src/integrations/channels` | 11 files, 76 passed, exit 0 |
| `git show --stat 3f4deae` | 9 files: `shopify.app.toml`, `channels/{index,types}.ts`, `channels/shopify/{common,index,live,media,media.test,mock}.ts`; no other channel touched |
| `scan-test-weakening.sh invai-backend 83ca734` | removed=0 added=131; hits are in another card's uncommitted `src/ai/images/**`; the "retries"/"throttled" names are real tests |
| Probe (temp vitest file in the copy, deleted): live adapter, product has 2 PROCESSING media with alt X; push 2 *new* files with alt X | `pushed: []`, both `skipped already_pushed` with the **same** `MediaImage/1`; no `productUpdate` sent |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `types.ts:196-258` matches wave.md; test "only Shopify implements it"; `write_products` in `shopify.app.toml:15` and `SHOPIFY_SCOPES` |
| 2 | yes | mock tests: same key twice → skipped, store holds 2; other connection separate; `Product/404` → `product_not_found` |
| 3 | **no** | bodies inspected via `fetch` stub (read vars, `productUpdate` media input, THROTTLED wait 2000 ms, userErrors → `rejected`); but the processing-media dedupe is unsound, see finding 1 |
| 4 | yes | recorded scopes without `write_products` → `reconnect_needed`, `fetchMock` not called; `ShopifyAuthError` (401/403) and `ACCESS_DENIED` detail → `reconnect_needed` |
| 5 | yes | 76 channel tests green; etsy/amazon/tiktok/walmart files unchanged |

## Blocking findings
1. `src/integrations/channels/shopify/media.ts:161` (and `:269`) — a media still processing is matched by **exact alt alone**, but alt text is one string per channel per design: `src/modules/photos/service.ts:630` writes `analysis.altText[channel]` onto every image of a set, so every image InvAI pushes to one product shares the same alt. Scenario: the shop pushes set 1 (3 photos); 20 s later, while Shopify is still fetching them (`image: null`), it pushes set 2 (3 different photos, same alt) → all 3 come back `skipped: already_pushed` with the first set's media id, nothing is sent, and T-27-3 records a success for photos that never reached the store (probe above). Same cause on a genuine retry after a lost answer: every image maps to the same `mediaId`, so stored ids are wrong. The tests hide this by giving each image a distinct alt (`media.test.ts:31-37,156`). Fix inside the adapter: a per-image marker (the card's "alt marker"), e.g. the filename stem carried in the alt or any field Shopify returns for a processing media, so the processing match is one-to-one per file; a test with identical alts across two pushes and across a retry.

## Checks
- [x] Only owned paths changed (`git show --stat`: channels/** + `shopify.app.toml`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened; `media.test.ts` fails on base trivially (`media.ts` absent), so it proves the change exists
- [x] Tenancy n/a (no DB); idempotency: mock keyed per (conn, product, filename) OK, live read-back OK by filename, broken while processing (finding 1); en messages only (adapter errors are mapped to copy by T-27-3/web; note); Zod n/a, hand validation on every input field (`validateProductImages`)
- [x] Decisions: scope change filed as OI-26 by the tech lead; no decision needed

## Optional notes (not blocking)
- `media.ts:247` attributes any media added concurrently by another app between read and mutate to this push; the alt/filename-first mapping limits it.
- The mock dedupes by filename regardless of key (a second key with the same files is also `skipped`); consistent with live, worth a sentence in the interface doc.
