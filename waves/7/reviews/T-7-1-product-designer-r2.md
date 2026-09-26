# Review of T-7-1 (round 2)

- Reviewer: product-designer on Sonnet 5
- Author: integrations-engineer + web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-web` worktree @`a915bdd`: `tsc --noEmit`, `biome check .`, `vite build`, `vitest run` | build/tests pass (76/76); `tsc`'s 8 errors are pre-existing on the parent commit (confirmed by the reviewer's file), unrelated to this card's `es.ts`-only diff |
| `git show a915bdd -- src/i18n/es.ts` | read in full |
| Diffed all four `shipping.exportWhere.*` strings between `en.ts` and `a915bdd`'s `es.ts` | all four now differ (Etsy, Walmart already did from r1; Amazon and TikTok now do too) |

## Acceptance criteria (design-relevant slice)
| # | Met? | Evidence |
|---|---|---|
| 3. Short en/es instructions per channel | **Yes** | Amazon: "Amazon: en Seller Central → Orders → Upload Order Related Files → Shipping Confirmation, sube este archivo." TikTok: "TikTok Shop: en Seller Center → Orders → Manage orders → Upload → Add Tracking No., sube este archivo." Both now carry a real Spanish instruction ("sube este archivo" / "upload this file") wrapped around the literal English menu path, matching the pattern already used for Etsy and Walmart. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`i18n/es.ts`, 3 lines).
- [x] Nothing outside scope.
- [x] No weakened tests (no test files touched in this diff).
- [x] en/es text: the r1 finding is resolved. The convention (English UI labels like "Seller Central"/"Seller Center"/"Add Tracking No." left untranslated since that's literally what the merchant will see in that marketplace's own English-language seller console, with the connecting instruction in Spanish) is applied consistently across all four channels now.

## Optional notes (not blocking)
- Still recommend fixing the "1 shipments exported" pluralization from r1 in a future pass; not part of this round's fix and not blocking.
