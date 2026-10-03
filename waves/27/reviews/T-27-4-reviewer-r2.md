# Review of T-27-4 (round 2)

- Reviewer: reviewer on fable
- Author: integrations-engineer on opus (invai-backend fix `31fb391`, on top of `3f4deae`)
- Verdict: approve

## Evidence I re-ran
Committed tree only (`git archive 31fb391` → `/tmp/review-T-27-4-r2`, node_modules symlinked, removed after), `OPENAI_API_KEY= ANTHROPIC_API_KEY=`.
| Command | Result |
|---|---|
| `tsc --noEmit` | exit 0, 0 lines |
| `vitest run --reporter=dot src/integrations/channels` | 11 files, 81 passed, exit 0 |
| `biome check src/integrations/channels` | 33 files, clean |
| `git show --stat 31fb391` | 3 files, all `channels/**`: `shopify/media.ts`, `shopify/media.test.ts`, `types.ts` (doc line only) |
| `scan-test-weakening.sh invai-backend cfd35ea` | no hits; removed=0 added=14 |
| Probe (temp vitest file in the copy, deleted): live adapter, product has 2 PROCESSING media with set 1's marker alts; push 2 new files, same base alt | both `pushed` with their own ids, `skipped: []`, sent alts carry 2 distinct markers |
| Probe: 3 PROCESSING media with marker alts, retry same 3 files | 3 `skipped` with 3 distinct `mediaId`s, no `productUpdate` |
| Probe: 2 PROCESSING media with the plain shared alt (pre-fix push) | not claimed; both new files added |

## Round-1 finding
1. **Resolved.** `media.ts:160-176` adds `altMarker` (8 hex of sha256 of the filename stem) and `shopifyAlt` (base alt cut so total ≤ 512); `findExisting` (`:179-192`) matches a processing media only by `endsWith(marker)` and skips nodes already in `claimed` (`:246-252`), so each existing media maps to at most one image; post-mutation mapping (`:299-301`) uses filename or marker. Tests now use one shared `ALT` across both pushes and the retry (`media.test.ts:83-178`).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1–2, 4–5 | yes | unchanged from r1; types.ts change is a comment only, interface identical |
| 3 | yes | dedupe is one-to-one per file while processing (probes above); 81 channel tests green |

## Checks
- [x] Only owned paths changed; nothing outside scope
- [x] No weakened tests; the new tests use identical alts, which is exactly what the r1 probe required
- [x] Tenancy n/a; idempotency: filename read-back + per-file marker, mock untouched; no PII in the marker (hash of a UUID filename)

## Optional notes (not blocking)
- Shopify shoppers using a screen reader will hear the trailing `[img xxxxxxxx]` tag in the alt text of every pushed image. If the product team minds, a follow-up could move the marker to a field Shopify exposes while processing once one is documented, or strip it with a second `productUpdate` once the media is READY.
- Two files with the same stem and different extensions in one push get the same marker and URL stem; `validateProductImages` dedupes by full filename only. Pre-existing (r1), safe while filenames are per-image UUIDs.
