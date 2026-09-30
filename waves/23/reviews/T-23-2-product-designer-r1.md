# Review of T-23-2 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-floor show 382ad42` | read full diff (i18n, CameraScan.tsx, common.tsx, result.ts, PickStation.tsx, PressStation.tsx, StationShell.tsx) |
| `grep REPRINT_REASONS src/schemas/production.ts` (contracts) | `under_cure`/`cracking` are real contract values; floor labels match exactly |
| `pnpm dev --port 5190` (floor, demo mode, no other agent's ports touched) | started/stopped cleanly (PID 74189); no browser device was available in this session to capture screenshots, and the author's referenced PNGs aren't present anywhere on disk — verdict is from code-level trace of the rendered strings/tone/component logic below, not eyes-on pixels |

## UX checklist
| Item | Result |
|---|---|
| QC-reason dialog: big targets, glossary words | Pass — unchanged `BigButton`s; new `reason.under_cure`/`reason.cracking` labels are plain and match glossary tone |
| Maintenance BLOCKED: distinct from success, exact copy | Pass — `mismatch.station_maintenance` en/es text matches the card exactly; renders through `ResultPanel` (red/danger, `XCircle`, "BLOCKED" vs green/`CheckCircle2`/"PRESS") and `feedback("error")`; offline replay parks it via the existing generic outbox-alert path |
| Transfer-age badge: warning, not block | Pass — `AgeWarning` is amber + `TriangleAlert` icon + text (not color alone), shown on pick rows, press queue, `TransferCard`, and the PRESS result panel; never gates a scan |
| Shelf + bin on pick list | Pass functionally, see note below |
| Camera button/dialog/fallback | Pass — `window.BarcodeDetector` is checked before any `getUserMedia` call (toast fallback, zero camera calls when absent); clear en/es fallback and permission-denied text; `Dialog`/`DialogTitle` accessible name present |

## Blocking findings
none

## Optional notes (not blocking)
1. `src/stations/PickStation.tsx` — the new `pick.binLabel` ("Bin {{bin}}" / "Compartimento {{bin}}") is a **new, un-vetted shop word**: the catalog elsewhere always calls the same concept "tote"/"caja" (`location.bin`, `pack.useTote`, etc.), and the very same pick row already shows a second, different bin code per order (`i.binCode` → destination tote, unlabeled arrow). Two different "bin" codes on one row, one newly named "Compartimento", risks a presser confusing pick-from vs put-into. Not blocking — a wrong pick is still caught by press-station scan match — but it's a real glossary miss (`write-plain-language-copy`: new shop words need product-designer sign-off). Recommend a fast-follow: rename to something disambiguating (e.g. "Shelf bin") and add the term to `glossary.md`.
2. `src/screens/StationShell.tsx` — `<CameraScan>` uses `Button size="xl"` (56 px), under the 64 px floor minimum (`add-ui-component` skill). It matches the *existing* header buttons (lock, settings) at the same size, so this card didn't introduce the gap — worth a header-wide audit, not a fix here.
3. `vite.config.ts`/`nginx.conf.template` Permissions-Policy change is outside this card's owned paths; author flagged it themselves. Not a UX issue — flagging for the primary reviewer's ownership/scope check.
