# Review of T-A7 (round 2)

- Reviewer: reviewer on opus. Author: web-engineer on Opus 5.5. Diff: invai-web fdce8c3 (8 files, +138/-7)
- Verdict: **approve**

## Evidence I re-ran (invai-web @ fdce8c3; no servers started)
| Command / check | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` / `pnpm test` | exit 0 / 194 files, 1 old warning (`content/markdown.test.ts`) / 20 files, 133 passed |
| `scan-test-weakening.sh invai-web e206b76` | no hits; 2 tests added, none changed |
| `scripts/i18n-es-missing.json` | absent. New keys are in both generated `en.ts` and `es.ts` |
| Backend cross-check `operations-service.ts:156-160,189-190,311,366`; `digest/detectors.ts:105-119`, `render.ts:67-69` | sentinel keys `none`/`unknown`/`in_house`, driver values `yes`/`no` and `params.designName` all match what the web keys on |
| Screenshots r2 `operations-es-1440`, `inventory-es-390` | "Desconocido", "Sin estación" path, all late-driver values in Spanish, real names (QC 1, Sun City DTF) kept; the 390 money tiles fit |

## Round-1 findings
1. AC9 (D2 mover): **fixed.** `digest-copy.ts:112-119` uses `params.designName` and falls back to the plain text when it's missing. The en/es strings are word for word the email's `D2 action.mover`. Unit tests cover the cases with and without a mover (en only; the es string is in `i18n-es.json:623` and `es.ts:753`).
2. AC8 (ops labels): **fixed.** `operations-view.tsx:22-40` looks up the text by `row.key`, and by `driver`+`value` for late drivers. It never matches on the English label. Channel values reuse `channel.*` keys, and every channel enum has an es key. Real station and vendor names pass through unchanged.

## Checks
- [x] Owned paths: `scripts/i18n-extra-en.json` is now granted (wave.md line 51). `shared.tsx` is in the feature folder
- [x] Scope: the `KpiTile` size step answers the r1 optional note, and only this feature uses it
- [x] No regressions: all 20 test files pass. Tenancy and idempotency don't apply (web only)

## Optional notes (not blocking)
- A D2 mover with key `unmapped` carries the backend's label as `designName`. If that label is English, it shows as-is in es, the same as in the email. That belongs to the backend or the digest.
