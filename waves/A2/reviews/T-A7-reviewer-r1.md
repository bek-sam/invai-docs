# Review of T-A7 (round 1)

- Reviewer: reviewer on opus. Author: web-engineer on Opus 5.5 (card said sonnet)
- Verdict: **changes-required**

## Evidence I re-ran (invai-web @ e206b76; no servers started)
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` / `pnpm test` | exit 0 / 0 errors, 1 old warning (`content/markdown.test.ts`) / 20 files, 131 passed |
| Ban test on a scratch archive with a planted `toLocaleDateString(undefined,` in `src/routes/`, a `toLocaleString(undefined)` in `features/today/`, and base `index.tsx` restored | each run: 1 failed (names the file), 2 passed. Clean tree passes |
| Scratch `renderToStaticMarkup(NotEnoughHistoryBanner)` | false → `role="status"` "Not enough history yet…"; true → empty (AC3) |
| Scratch `digestActionText` D2 with `params.designName:"Desert Sunset Tee"` | "See what changed" (the mover is dropped) |
| en/es flatten of generated catalogs (97 new keys) | 0 missing; 2 identical (supplier brand names, fine) |
| Diff of changed tests (base 81d27c5..e206b76) | no removed expects, no skip/only/mock |
| Screenshots looked at: today-es-1440/390, operations-es-1440, inventory-es-390 (cropped) | see findings |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Operations | Partly | sections, bottleneck, AC-B2 note, counts-only cut present; stations/vendors only; "were more often" wording present. English labels in es: finding 2 |
| 2 Inventory + Supplier trends | Yes | inventory-es-390 screenshot; export and query use the same `days`/`period` |
| 3 Not-enough-history | Yes | render probe above (not seen live; the probe covers it) |
| 4 Lifecycle badge | Yes | `designs.index.tsx`: query `enabled: can("finance.read")`, market trend wins unless `insufficient` |
| 5 CSV same filters | Yes | ops `{period, channel}`, inv `{days}`, trends `{period}` match their queries; no buyer PII is in the backend's `export-service.test.ts` (not this card's code) |
| 6 Today panel | Yes | `index.tsx`: `can("finance.read") &&` gates the mount, so no query without it; `generatedAt === null` → null; `onClick` → `mutate`, the link isn't prevented; rulings 4 and 6 met |
| 7 B-225 | Yes | `greetingDateLocale`; ban test catches a planted call (above) |
| 8 en/es, Intl | No | finding 2. Today "~$2,423.28 de impacto" is `digestMoneyLang` es-US, the house convention since 34a8fd2 and the same as the digest card beside it, so not a defect |
| 9 D2 mover | **No** | finding 1 |

## Blocking findings
1. `src/components/digest/digest-copy.ts:112-113`: `see_what_changed` ignores `params.designName`. When T-A9 sends a D2 action with a mover, Today (and the digest card) shows "See what changed". The email says "See what changed: Desert Sunset Tee moved your profit the most" (`render.ts:67-70`, key `D2 action.mover`, en+es). AC9 is unmet, and the report doesn't mention AC9. Fix: branch on `designName` with the email's en/es wording, and add a test.
2. `src/features/analytics/operations-view.tsx:88,108,159,346` render the backend's English `label` strings as they are. In Spanish, Operations shows "Unknown", "In-house", "No station" and the late-driver values "Personalized"/"Not rush"/"Waited over 24 h…" (`operations-service.ts:156-160,190,311-318`). You can see "Unknown" in the author's own `operations-es-1440-light.png` (Reprints by vendor). AC8 (es everywhere) fails for every Spanish user. Fix: translate from `row.key` for the sentinel keys (`unknown`, `in_house`, `none`) and from driver+value for the late drivers. Keep real station and vendor names as they are.

## Checks
- [x] Owned paths. One small overstep: `scripts/i18n-extra-en.json` (+4 lines, keys only) isn't on the card. Non-blocking; tech lead to ratify
- [x] Nothing outside scope; QA 3b6939e adds only the two smoke routes (no retries, sleeps or skips)
- [x] Tests not weakened; the ban test really fails on a planted call
- [x] Tenancy/idempotency n/a (web only); money via `Money`/`formatMoney`; en/es: see finding 2
- [x] Decisions: the NOT_IMPLEMENTED → hidden choice is reasonable and reported

## Optional notes (not blocking)
- inventory-es-390: "12.441,31 US$" and "1170,50 US$" run past the tile edge and touch the viewport (no split, but they overflow). For product-designer.
- `inventory-health-view.tsx:18` `formatNumber` is always en-US: "2,619" units sits next to "12.441,31 US$" in es. There's no operations-es-390 screenshot.
- The report ran the API on :3000 instead of a 31xx port. The late-drivers hint "…not what caused it" is fine as a disclaimer.
