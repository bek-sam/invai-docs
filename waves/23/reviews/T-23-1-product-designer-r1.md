# Review of T-23-1 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| Read 15 author screenshots (light/dark, en/es, 1440/390) | looked at each |
| `git diff 54b64d7 353a49d -- src` | reviewed all 18 changed files |
| Read `invai-ui/src/app/money.tsx`, `digest/digest-copy.ts` | confirmed root cause of finding 1 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | shot 14: "Use suggested address" for corrected status; verified banner for matched |
| 3 | yes | shot 04: maintenance badge = warning color + wrench icon + reason text, never color alone |
| 4 | yes | `sheets.$sheetId.tsx` countdown mm:ss, portal toast in plain language |
| 6 | partial | see finding 1; help/legal 390 (shots 10–11) clean, no h-scroll |
| 8 | partial | see finding 2 (390 layout) |

## Blocking findings
1. `invai-web/src/routes/_app/settings/billing.tsx` (Money usages, e.g. line 592) — AC6 requires es-US formatting for billing numbers. Counts were fixed (`localeNumber`, e.g. "352 / 10,000"), but plan price and label-fee amounts still use bare `i18n.language` via `<Money>`, rendering comma-decimal es style ("149,00 US$", "10,48 US$" — shot 07). Same page mixes two decimal conventions in Spanish, which is exactly the confusion `digestMoneyLang` (`digest-copy.ts:74`) was written to prevent. Fix: pass `digestMoneyLang(i18n.language)`-equivalent currency locale into these `<Money>`/`formatMoney` calls (Money's `currency` prop only sets ISO code, not locale — needs a locale prop or a local `formatMoney` call).
2. `invai-web/src/routes/_app/shipping.tsx:121–126` — adding the 5th tab ("Fin del día") overflows `TabsList` at 390 px with no scroll affordance (shot 02: "Tracking push" clipped to "E" at the viewport edge). The repo already has the fix for this exact case: `orders/index.tsx:282` wraps `TabsList` in `<div className="-mx-1 overflow-x-auto px-1">`. Apply the same wrapper here.

## Checks
- [x] Only owned paths changed (`invai-web/src/**` incl. `vite.config.ts`, flagged and justified in report)
- [x] Nothing outside scope
- [x] en/es text: all new strings have real Spanish (verified in `es.ts`); pre-existing untranslated keys (billing.*, digest list chips, etc.) are disclosed gaps, not introduced here — not blocking
- [x] Status never color-alone (maintenance badge, address-check banner both icon+color+text)

## Optional notes (not blocking)
- Shot 15 (photo upload preview) shows a broken-image icon; author attributes to a pre-existing `SignedImage` gap, but this shot appears to be from the live dev API, not the flagged prod-CSP preview build — worth a quick re-check, not blocking this card.
- AC9 resend-button scoping to `unknown`/`failed` deliveries is blocked by the same missing `Alert.data` surface as the Spanish alert text (out of round per the card); reasonable stopgap (shows whenever emailed, self-corrects via `VENDOR_USES_PORTAL` toast).
- 384 pre-existing untranslated keys (billing/digest/reprints) reported by the author for a reconciliation card — agreed, worth doing soon since it's visible on several screens shipped this wave.
