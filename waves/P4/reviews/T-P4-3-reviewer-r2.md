# Review of T-P4-3 (round 2)

- Reviewer: reviewer on Opus 5.5. Author: web-engineer on Opus 5.5. Commit `47acf01` (invai-web)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test` (invai-web, clean tree at 47acf01) | tsc clean; biome 198 files, 1 pre-existing warning; 139/139 passed |
| `scan-test-weakening.sh invai-web 47acf01~1` | no hits |
| `git show --stat 47acf01` | 5 files: i18n-es.json, en.ts, es.ts, designs.$designId.tsx, new designs-orders30.test.ts. All owned |
| nbsp byte check, `grep orders30` in es.ts and i18n-es.json | U+00A0 in all 4 es values (`_one`/`_other` in both files). Only consumer is designs.index.tsx:115, which passes `{ count: d.ordersLast30d }` |
| `Field` in components/page.tsx:58 | accepts `className` through `cn()`, so `col-span-2 sm:col-span-1` applies |
| Looked at r2-es-design-detail-390, r2-es-designs-list-1440, r2-es-design-detail-1440-bottom | see AC |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | r1 blocker fixed. At 390 es the select has its own full-width row reading "Manga izquierda", with Ancho and Alto side by side below it. At 1440 the select, width and height stay on one row of 3, as before. `loadMore` and alt fixes are unchanged from r1 |
| 2 | Yes | Unchanged from r1 (billing "entrada / salida", locale grouping) |
| 3 | Yes | en `_one`/`_other` defaults match. Plural keys are hand-synced in en.ts, es.ts and i18n-es.json; no regeneration |

## Blocking findings
none

## Checks
- [x] Owned paths only; no scope creep (the plural and nbsp were r1 optional notes)
- [x] New test is meaningful. It runs real i18next against both catalogs for counts 0, 1 and 5, plus the nbsp. It fails on base: `es.designs.orders30_other` is undefined there, and count 1 gives "1 pedidos"
- [x] No weakening. Tenancy, money and idempotency: n/a
- [x] Screenshots are from 05:13-05:14, before the 05:15 commit. The report says they were taken from the uncommitted tree that became 47acf01, and the 390 and 1440 images show exactly the committed layout. I accept them as fresh for this diff

## Optional notes (not blocking)
- At 1440 es, "N pedidos ·" can still wrap before "30 d", but the unit never splits. Fine.
- Thumbnails show alt text in the author's environment (art missing in storage); this is not caused by this card.
