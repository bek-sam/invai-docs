# Review of T-P5-5 (round 1)

- Reviewer: reviewer on claude-opus-5.5
- Author: web-engineer on claude-opus-5.5
- Verdict: changes-required

## Evidence I re-ran (own worktree `/tmp/p5-rev-t5` at 44c04c1 = invai-web HEAD, node_modules symlinked, removed after)
| Command | Result |
|---|---|
| `tsc --noEmit` / `biome check .` / `vitest run --reporter=dot` | clean / 1 old warning (`src/content/markdown.test.ts:106`, untouched) / 23 files, 156 passed |
| Product files reverted to `44c04c1~1`, new tests run | 15 of 20 failed (`timelineReasonLabel is not a function`, alertDetail asserts) |
| Mutation: `alertDetail` params branch disabled | 3 of 10 failed with assertion errors (`to contain '#1042'`, `'Gildan…'`) |
| Probe: real i18next en+es catalogs, all 14 alert codes, 22 timeline codes, an unknown code, missing `vendorName` | every code translated in es, no raw key, no es==en; unknown code -> title fallback / `null`; **missing vendorName -> broken line (finding 1)** |
| Flattened en.ts / es.ts / `scripts/i18n-es.json` | 39 new keys in each, identical sets, json==es; reused `reprintReason/holdReason/cancelReason/sheetState/channel` keys exist for every enum value; `i18n-es-missing.json` absent |
| `scan-test-weakening.sh invai-web 44c04c1~1` | no hits |
| psql (read-only) order `113-2322494-1004602` transitions | `imported->ready` and `imported->needs_mapping` have `reason` NULL; on_sheet/transfer_in carry sheet reasons |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | No | Lines come from `messageCode` via a `Partial<Record>` lookup (R1 ok); Intl dates in `timeZone` + active language; `_one/_other` verified with real i18next. Fallback without params is correct. But a missing key isn't handled: see finding 1. |
| 2 | Yes | All 22 `TIMELINE_REASON_CODES` covered, incl. `mapped`; unknown code -> `null` -> `extractTimelineReason`. The "Importado -> Listo" rows in `order-timeline-es-1440.png` show no reason because the stored reason is NULL (seed rows), not a missed code. |
| 3 | Partly | es screenshots (`alerts-panel-es-390`, `order-timeline-es-390/1440`) have no raw keys or English; wraps fine. Fails for the vendor-unknown line (finding 1). |
| 4 | Yes | Tests red on base and under mutation (above); i18n files in sync. |

## Blocking findings
1. `invai-web/src/routes/_app/index.tsx:522-533` (`vendor_email_unconfirmed` / `vendor_email_failed`) — every builder substitutes `p.x ?? ""`, so a missing key leaves a hole. T-P5-4 r2 (`invai-backend/src/modules/vendors/delivery.ts:242`) deliberately omits `vendorName` when the vendor is unknown. Scenario: a sheet email outcome is `unknown` for a sheet with no vendor name; the office user in es reads "Hoja 2026-10-01 #1: no pudimos confirmar que el correo a  se haya enviado." (en: "the email to  was sent"). Fix: a vendorless variant ("the email to the vendor" / "el correo al proveedor") when `vendorName` is absent, plus a test with real catalogs for it.

## Checks
- [x] Only owned paths changed (8 files: `routes/_app/index.tsx` + `-index.test.ts`, `features/orders/**`, en/es, `i18n-es.json`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none weakened (scan clean, red on base)
- [x] Tenancy / idempotency / money: n/a (client rendering only); en/es: see finding 1
- [x] Decisions: none needed (ruling R1 followed)

## Optional notes (not blocking)
- `timeline-reason.test.ts` fake `t` echoes raw values, so it asserts "On hold: buyer_request"; one real-catalog es case would cover the reuse.
- At 390 px `line-clamp-2` cuts the ship-by date off most order alerts (`alerts-panel-es-390.png`); for product-designer.
- Processes: none started; worktree removed.
