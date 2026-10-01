# Review of T-P4-3 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: web-engineer on Opus 5.5
- Verdict: approve

Scope: co-review for copy, glossary, layout and Spanish quality (risk flag `ui`).

## Evidence I looked at
- Card `T-P4-3-web-designs-es.md`, report `reports/T-P4-3.md`.
- Diff `git -C invai-web show 85c4ed0` (es.ts, en.ts, i18n-es.json, `designs.$designId.tsx`,
  `billing.tsx`).
- Screenshots in `/tmp/p4-web/`, es and en, 1440 and 390: designs list, design detail (top and
  scrolled), billing (top and scrolled).

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes, with a note | `es-designs-list-1440/390.png`: fully Spanish, tú-form copy ("¿No necesitas un plan de pago por ahora?", "Suelta un archivo nuevo"), number/date formats look right, long design names ellipsis-truncate in the card grid without breaking layout at 390. Both fixes (`action.loadMore`, placement alt text) are correct in the diff and I confirmed the alt-text fix actually renders ("Manga izquierda") in `es-design-detail-1440-bottom.png` / `390-bottom.png`. See note below: the *other* screenshots offered as "after" evidence for the same fix (`es-design-detail-1440.png`, `-390.png`, `en-design-detail-1440.png`) are stale — they still show the raw enum "sleeve_left" in the broken-image box. Timestamps confirm it: those three are from 01:49:2x/01:49:30, the "-bottom" pair from 01:51:52, i.e. taken ~2.5 min later, after the real fix was built. Functionally the fix works; the report just left pre-fix screenshots in the evidence set next to post-fix ones under similar names. |
| 2 | Yes | `es-billing-1440/390.png`, `-bottom.png`: "1,447 entrada / 2,911 salida" (was hardcoded " in / ... out" around two already-localized numbers — now through `t("billing.ledgerTokensInOut", ...)`), "$149.00"/"$349.00" money, "13 / 10,000" usage, "Periodo 30 sep – 31 oct" date — all Spanish-formatted, no bare `toLocaleString()` found in the diff or screenshots. |
| 3 | Yes | `en-designs-list-1440.png`, `en-design-detail-1440.png` (aside from the known-stale alt-text frame, see above) show unchanged English meaning. `i18n-es.json` was hand-edited in the diff; no `scripts/gen-i18n.py` run. |

## Glossary / tú form / Spanish quality
- Tú-form imperatives used correctly throughout: "Suelta un archivo nuevo para reemplazarlo",
  "Compra un paquete de créditos", "¿Necesitas más este mes?".
- "Nicho" (niche) isn't in the glossary; it's a reasonable plain translation and not a shop-specific
  term that needs a ruling.
- Billing's new key `billing.ledgerTokensInOut: "{{in}} entrada / {{out}} salida"` is clear, matches
  the existing table header style (`Tokens`), and keeps the placeholders intact.
- `placement.sleeve_left: "Manga izquierda"` (and siblings) were already correct in the catalog; the
  fix was routing the image alt text through `t()` instead of the raw enum.

## Optional notes (not blocking)
- Retake `es-design-detail-1440.png`, `es-design-detail-390.png`, `en-design-detail-1440.png` so the
  evidence set doesn't contain a stale pre-fix frame next to a correct post-fix one for the same
  finding — a future reader comparing only the "top" screenshots would conclude the alt-text bug is
  still there. Not asking for any code change; I independently confirmed the fix is correct via the
  `-bottom` screenshots.
- `action.loadMore` wasn't visually exercised (no route in this seed has a second page) — the key
  addition matches the existing pattern (`action.add`, `action.cancel`) and is low risk, but flag it
  for whoever next hits a 200+ design shop to confirm it renders without truncation.

## Checks
- [x] Only owned paths changed (per report; not re-verified by me, not my remit)
- [x] Nothing outside scope
- [x] n/a — no tests in my remit
- [x] en/es: both present and in sync across `en.ts`/`es.ts`/`i18n-es.json`; glossary words used
      correctly; money and date formats through the shared formatters, not bare `toLocaleString()`
- [x] Decisions: none needed
