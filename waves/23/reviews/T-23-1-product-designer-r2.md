# Review of T-23-1 (round 2)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show 34a8fd2 -- src` | billing.tsx: 3 `<Money>` usages → `formatMoney(cents,"USD",digestMoneyLang(i18n.language))`, tabular-nums span, `Money` import dropped; shipping.tsx: `TabsList` wrapped in `-mx-1 overflow-x-auto px-1` (same pattern as `orders/index.tsx:282`) |
| Read `billing-es-390-full.png` | "$149.00/mes", "$349.00/mes", "$699.00/mes", "$0.10 por etiqueta", "$10.48 en tarifas de etiquetas" — all es-US period-decimal, matches page's `localeNumber` counts ("352 / 10,000") — finding 1 resolved |
| Read `shipping-es-390-scrolled.png` | scrolled tab strip shows "Envío de rastreo" fully, unclipped, at 390px; no page-level overflow — finding 2 resolved |
| Read `pers-photo-slot-after-upload.png` | broken-image icon in Live preview, as author reports |
| `grep -n "img-src\|prodCsp" invai-web/vite.config.ts` | dev CSP: `img-src 'self' data: blob: ${S3_ORIGIN}`; prod/preview CSP: `img-src 'self' data: blob: https:` (no plain `http:`) |
| `git -C invai-web log --oneline --follow -p -- vite.config.ts \| grep img-src` | `https:`-only prod img-src line introduced at `5896ba5` ("T-12-5, B-24"), predates this card |
| `git -C invai-web show d7029ff --stat` | this card's only `vite.config.ts` commit is the vendor-chunk split (T-23-1, B-107) — doesn't touch `img-src` |

## Photo-preview CSP claim: accepted
The author's explanation checks out against history, not just their word: the strict `img-src 'self' data: blob: https:` line is in the file at `5896ba5` (T-12-5), five commits before this card, and this card's only touch of `vite.config.ts` is the unrelated vendor-chunk split. Local MinIO is HTTP-only in this dev stack; a real deployment's object store is always HTTPS, so the policy is correct for production and only breaks when a `vite preview` (production-CSP) build is pointed at local HTTP MinIO — an artifact of this test rig, not a code defect, and not owned by this card. Not blocking.

## Acceptance criteria (this round's scope)
| # | Met? | Evidence |
|---|---|---|
| 6 | yes | billing es-US money confirmed (shot above); no more comma-decimal mixing |
| 8 | yes | shipping tabs reachable at 390px, no clipping, no page h-scroll |

## Checks
- [x] Only owned paths changed (`invai-web/src/routes/_app/settings/billing.tsx`, `invai-web/src/routes/_app/shipping.tsx`)
- [x] Both r1 blocking findings fixed and verified with screenshots, not just claimed
- [x] Status/money never rely on an untranslated or inconsistent locale convention

## Optional notes (not blocking)
- The CSP/MinIO local-preview gap is real and worth a platform-sre note so it doesn't keep costing review cycles, but it predates and is outside this card.
