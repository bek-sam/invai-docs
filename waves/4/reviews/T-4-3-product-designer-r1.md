# Review of T-4-3 (round 1)

- Reviewer: product-designer on Opus
- Author: floor-engineer on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Same setup as the primary review: worktree `invai-floor-r43-review` @ `04b34d9`, live API on `:3192` against DB copy `invai_r43_copy`, floor on `:5192` | up |
| Signed in as `receiver@desertbloom.test` (PIN 1177) via a `receiving`-kind station, at 1280×800 | lands straight on Receiving |
| Walked Purchase orders, Vendor transfers, Stock count in **English** at 1280×800: scan hint, list, partial receipt, over-receipt warning, cap-to-ordered, complete, sheet-by-transfer scan, mark received, count with differences, count saved | all screens render correctly, large clear type, station-header pattern (`StationHeader` from `@invai/ui`) reused unchanged from the other stations |
| Switched to **Spanish** (ES toggle) at 1280×800, repeated: PO partial receipt with a double tap, forced a real offline drop (unreachable Vite proxy) mid-receipt, watched "Sin conexión" / "Guardado sin conexión" / "Faltan N" / reconnection, vendor sheet received, stock count saved | full ES coverage: `floor.receiving.*` (58 keys) reads as real, idiomatic Spanish, not machine-translated — correct shop vocabulary (prenda, hoja, transferencias, proveedor, órdenes de compra), matches the glossary words called out in the report |
| `grep -n` for hard-coded English in `src/stations/receiving/*.tsx` outside `t(...)` | none |
| Visual check of touch targets: `Stepper` −/+ buttons (`size-16` = 64 px), `BigButton` primary actions (`h-16`–`h-24`), list rows (`min-h-20`) | all meet the 64 px+ floor target rule |
| Checked color+icon+words on every result state (FlashBar `role="alert"`, ok/warn/blocked tones with icons `TriangleAlert`/`PackageCheck`/etc., `feedback()` sound on every scan result) | present, not color-alone |
| Checked keyboard-only path: every scan goes through `useScan`/the simulate-scan box, buttons have `tabIndex={-1}` so the scanner's Enter doesn't fire a focused button by accident | consistent with the rest of the floor app's pattern |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 5. Quality: en and es, tablet layout, large touch targets, same station-header pattern | Yes | Full en/es walk above at 1280×800; `StationHeader` reused unmodified (not re-implemented); 64 px+ targets throughout; the receiving tab fits the existing station-tile pattern |
| 1–4 (functional criteria) | Deferred to the primary and inventory reviews | I focus on UI/UX per my co-review role; I independently confirmed the flows render correctly in both languages while exercising them, but defer the transactional correctness verdict |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — `invai-ui` was not touched by this card at all (confirmed no diff outside `invai-floor`)
- [x] Nothing outside scope
- [x] en/es text complete, real Spanish (not literal translation), no raw English found in the new files
- [x] Accessibility: `role="alert"` on the flash bar, `aria-label` on every stepper/icon-only button, color+icon+word on every result, 64 px+ targets, visible focus states inherited from `@invai/ui` primitives (Radix/Base UI), keyboard-only scan path preserved

## Optional notes (not blocking)
- `@invai/ui`'s `StationHeader` hard-codes "Online"/"Offline" in English, visible even when the rest of the screen is in Spanish. This is **my own component** (`invai-ui`, not `invai-floor`), so it's a finding against my backlog, not this card — the author correctly reported it as a finding rather than editing outside their owned paths. I'll pick it up.
- The station-tile grid (`StationShell.tsx`'s `grid-cols-2`) leaves Receiving alone on the last row, since it's a 5th tile in a 2-column grid. Also outside this card's 2-line grant; noted for whoever next touches that file (T-4-4 or a design pass).
- The sync badge's copy ("1 escaneo por sincronizar" for a receipt) belongs to T-4-2's `SyncStatus.tsx`; the author flagged it correctly rather than editing a file they don't own.
- None of the above block this card — they're all either pre-existing, owned by files outside `invai-floor`, or explicitly outside the 2-line grant this card was given.
