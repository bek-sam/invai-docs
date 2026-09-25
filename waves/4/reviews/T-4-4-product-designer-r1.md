# Review of T-4-4 (round 1)

- Reviewer: product-designer on Opus
- Author: floor-engineer on Opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Same worktree/build/lint/test setup as the primary reviewer (`invai-floor-r44` on `a0d88bd` + diff, `invai-ui-r44` on `e7a7e31` + diff) | tsc/biome/vitest/vite build all clean in both repos (see `T-4-4-reviewer-r1.md` for the full command table — not repeated here) |
| Looked at every screenshot in `invai-docs/waves/4/reports/T-4-4/` (19 files, en-1…11, es-1…8) at full resolution | done — see per-criterion notes below |
| Read `PackStation.tsx`, `ProblemDialog.tsx`, `HandToLeadDialog`, `DoneScreen`, `src/i18n/en.ts` and `es.ts` in full | done |
| Live E2E (`floor.spec.ts`, `offline.spec.ts`, `press.spec.ts`) against the real stack, port 3194/5194 | 3 passed (ran jointly with the primary review) |

## Acceptance criteria (UX-relevant)
| # | Met? | Evidence |
|---|---|---|
| 1a/1b Blocking and hand-to-lead states are unmistakable | Yes | `en-2-blocked-owner.png`/`en-7-blocked-packer.png`: full-screen red, icon (circled X) + "NOT READY TO PACK" + words, missing unit named with its state ("Pressed"). `en-4-handed.png`: full-screen amber, warning-triangle icon + "HANDED TO LEAD" + words. Color is never the only signal — icon and text both carry the meaning, consistent with the presser/packer principle (color + icon + words) |
| Hand to lead hidden for packers | Yes | `en-7-blocked-packer.png` (packer PIN 1166) shows only "Back to the order" and "Check again" — no third button. `en-2-blocked-owner.png`/`en-3-hand-dialog.png` (owner) show it. Verified in code (`session.permissions.includes("production.override")` gates the *render*, not just a disabled state — right call, since a button that always 403s for a packer is worse than no button) |
| Touch targets | Yes | Pack panel buttons are `h-24` (96 px); Problem dialog buttons are also `h-24` (96 px, 4×3 grid, `en-5-problem-reasons.png`). Both comfortably clear the floor's 64 px+ minimum |
| 2 Problem dialog: 12 reasons, en+es, readable | Yes | `en-5-problem-reasons.png`: 4×3 grid, `text-2xl leading-tight`, two-line labels wrap cleanly ("Colors look wrong", "Shirt damaged or stained", "Pressing mistake", "Customer asked" all wrap without truncation or overlap). Reasons are pulled from the contract enum (`REPRINT_REASONS`) rather than hand-maintained, so the floor list can't silently drift from what the backend accepts — a good simplification that also fixes a real gap (the old list was 6 reasons, missing half the contract's 12) |
| 3 QC "NOT SAVED" vs pass/fail title | Yes (by code read) | `QcStation.tsx` shows `floor.qc.notSaved` ("NOT SAVED"/"NO SE GUARDÓ") on any refusal, never mislabeling a rejection as a pass or fail. I did not get a live screenshot of this state (no easy trigger, per the author's own gap note) but the code path is unambiguous and the strings exist correctly in both languages |
| 4 No English leaks | Yes | Checked every Spanish screenshot (`es-1` through `es-8`): header ("Sin conexión"/"En línea"), pack titles ("NO SE PUEDE EMPACAR", "PASADO AL ENCARGADO" via `es-4` equivalent path), dialog copy, reason buttons — all Spanish, no leftover English strings or raw error codes visible anywhere |
| 6 `<html lang>` | Yes (by code read) | `setupI18n()` sets `document.documentElement.lang` synchronously from the stored device language before `initI18n()` resolves, so there's no flash of the wrong `lang` attribute at startup |

## Copy review (en/es)
Read every new/changed string in `src/i18n/en.ts` and `es.ts` side by side. All plain shop language, consistent with existing floor idiom (all-caps result titles, "shirt"/"prenda" not "unit"/"garment"):
- "NOT READY TO PACK" / "NO SE PUEDE EMPACAR" — clear, matches the existing PRESS/BLOCKED all-caps pattern.
- "SAVED: NOT CHECKED YET" / "GUARDADO: FALTA REVISAR" — good: tells the packer the save happened but the completeness check hasn't, and to keep the order together. This is exactly the nuance decision 0010 needs (a saved-but-unverified state is not the same as packed).
- "Hand to lead" / "Pasar al encargado" — "encargado" is the right register for a shop lead in Spanish (matches existing floor vocabulary for supervisory roles elsewhere in the catalog).
- The hand-to-lead dialog body ("It will not be packed or shipped until the missing shirts are packed.") is specific and sets correct expectations — it doesn't just say "sent to a lead," it says what will and won't happen, which matters given decision 0010 explicitly rules out partial shipment.
- Reason labels read naturally in both languages ("Colors look wrong"/"Colores incorrectos", "Pressing mistake"/"Error al planchar") — no literal/awkward translations.
- Pluralization is handled correctly (`incomplete_one`/`incomplete_other`, `pending_one`/`pending_other` pattern already established, followed here).

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — `invai-ui`'s one file (`src/floor/station-header.tsx`) touches exactly what the card allows ("the Online/Offline strings only"): it swaps hardcoded `"Online"`/`"Offline"` for `t("common.online")`/`t("common.offline")`, both of which **already existed** in `invai-ui`'s own locale files before this card (confirmed: `src/i18n/locales/en.json`/`es.json` already had `common.online`/`common.offline`). No new keys added, no component API changed, no other file touched.
- [x] Nothing outside scope in `invai-ui`.
- [x] States: loading (`checking`/`Loader2` spin on Mark packed), empty (`floor.common.empty`), error/blocked (red panel), partial (missing-units list), success (green "Order X packed") — all present and screenshotted.
- [x] Accessibility: color is never the only signal (icon + text on every result tone); the reason dialog's grid buttons all have visible text labels, not icon-only; the missing-units list uses a `data-testid` and readable large text, not tiny fine print.
- [x] Icons: PWA icons generated via a Playwright/Chromium render of `icon.svg` — checked all four files render correctly (192, 512, 512-maskable, 180 apple-touch), the maskable icon's content sits well inside the safe zone (checked visually), no build-time dependency added for this (one-off generation, not a recurring build step, per the report — acceptable for a one-time asset).

## Optional notes (not blocking)
- The offline-replay alert for a blocked "Mark packed" entry reuses T-4-2's generic "N offline scan(s) was/were rejected" title, which reads slightly oddly since packing isn't a "scan." The row detail underneath is correct and specific. This is T-4-2's copy to adjust, not a T-4-4 defect — the author already flagged it.
- I'd have liked a live screenshot of the QC "NOT SAVED" state and the update-prompt button in its "waiting" state, but neither is easy to trigger without extra test scaffolding, and the code path for both is unambiguous. Not blocking.
- No dark-mode screenshot was taken for the floor screens. The floor tablet flows aren't part of the usual dark-mode audit surface (owner/office desktop screens are), and nothing in the card asks for it, so this isn't a gap against this card's scope.
