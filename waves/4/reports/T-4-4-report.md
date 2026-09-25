# Report: T-4-4 Pack station uses pack-complete; floor polish
Author: floor-engineer, Claude Opus 5.5

## Status: built and verified, NOT committed
- **The commit was denied by the permission classifier** ("Modify Shared Resources") when I ran `git commit` in `invai-floor`. I didn't retry it by any other route.
- All changes are **unstaged** in the shared working trees. They sit on top of `invai-floor` `a0d88bd` (T-4-2 r2) and `invai-ui` `e7a7e31`.
- Nothing else is in either tree, so every diff there is T-4-4's.
- The index is clean, so another agent's `git commit` can't pick up my files by accident.
- The ready commands are under "To commit" below.

## Intake
- Card: T-4-4. Owner: floor-engineer. Scope ref: `scope.md#mvp-in` item 5. Backlog: B-94, B-105 (without the camera scanner), B-33.
- Owned: `invai-floor/src/stations/{Pack,Press,Qc,Pick}Station.tsx`, `src/components/ProblemDialog.tsx`, `src/scan/result.ts`, `vite.config.ts`, `index.html`, `public/**`, `src/i18n/**`, `e2e/floor.spec.ts`, and `invai-ui/src/floor/station-header.tsx` (the Online/Offline strings).
- Cross-owner grants, all from the tech lead in this session:
  - T-4-2 files, committed after T-4-2 landed:
    - `src/outbox/db.ts`, `src/outbox/outbox.ts`, `src/app/actions.ts`: the `packOrder` command kind.
    - `src/components/SyncStatus.tsx`: one `case`.
  - Files no card owns:
    - `src/api/{types,rpc,demo}.ts`: `FloorApi.packOrder`.
    - `src/main.tsx` (`registerSW` line plus one import).
    - New `src/components/UpdatePrompt.tsx`.
    - `src/screens/StationShell.tsx`: one import, plus `<UpdatePrompt />` in the two headers.
  - Also outside the list:
    - New `src/api/packOrder.test.ts`: tests for the granted api and outbox lines.
    - `src/scan/pressFlow.test.ts`: one assertion changed, see Decisions.
- Risk flags: ui, floor-correctness. Co-reviewers: product-designer and qa-engineer.

## Built
- **Mark packed calls the server** (`PackStation.tsx`):
  - It sends `packOrder({ orderId, idempotencyKey })` through the outbox. The key is new on every tap and is the outbox entry id. A refusal stores nothing on the server, so "Check again" must be a new request.
  - `packed: true` shows "Order X packed" plus the label, as before.
  - Units missing: a full-screen red **NOT READY TO PACK** / **NO SE PUEDE EMPACAR**. It lists each missing unit with design, blank and a translated state (for example "Pressed" / "Prensado"). Its buttons are "Back to the order", "Check again" and, for leads only, "Hand to lead".
  - This replaces the old client-only check and its "Pack anyway" button.
  - The client `releaseBin` on finish is gone, because the server releases the tote.
- **Hand to lead** (decision 0010):
  - The button renders only when `session.permissions` includes `production.override` (owner, admin). Packers never see it.
  - It opens a dialog with a required reason (max 500) and calls `packOrder({ ..., override: { reason } })`.
  - `packed: false` plus `override` shows an amber **Handed to lead** / **Pasado al encargado** screen: "Order X is not packed. Put the tote aside for the lead." Then the station clears.
- **Results, not errors:** `rpc.ts` maps a `PACK_INCOMPLETE` 409 to `{ packed: false, missing, override: null }`, so a blocked pack never parks an outbox entry.
- **Offline:**
  - A pack saved offline shows **SAVED: NOT CHECKED YET** ("keep the order together").
  - If it replays short, `outbox.ts` parks it as `blocked` with the code `pack_incomplete`. The existing alert fires, and the problems list shows "Mark packed · The server BLOCKED it: units of the order are still missing".
  - `CONFLICT` on `packOrder` (on hold, or a key reused) is a real refusal. It is no longer treated as "already applied".
  - An on-screen `CONFLICT` shows "Order X can't be packed now (on hold or cancelled)…".
- **Progress survives a reload:**
  - The order in progress (units, tote, scanned ids) is saved to IndexedDB (`kv` key `packProgress`) on every change.
  - It is restored on mount, with the notice "Picked up where you left off", and cleared on packed, handed, queued or Cancel.
  - Units that reach the pack list later are merged into the order in progress.
- **Service worker never reloads by itself:**
  - `registerType: "prompt"`. The built `sw.js` calls `skipWaiting()` only on a `SKIP_WAITING` message.
  - `UpdatePrompt` shows an "Update app" / "Actualizar app" header button. The update is applied only on that tap.
  - `onNeedReload` reloads only if this tablet asked, so an update from another tab can't reload mid-pack.
- **Problem dialog:** all 12 contract `REPRINT_REASONS` in en and es, in a 4×3 grid of 96 px buttons. The old "stain → blank_damaged + note" mapping is replaced by `blank_damaged` ("Shirt damaged or stained").
- **QC and press truth:**
  - QC done shows "Sent" / "Enviado" or the queued line.
  - A refusal shows the title **NOT SAVED** with the reason translated by code (`refusalText()` in `result.ts`), never the pass/fail title.
  - Press "Problem" shows success, queued or refused truthfully. With no unit it shows "Scan the transfer first…" instead of dropping it silently.
- **No English leaks:**
  - The station header reads `common.online` / `common.offline` from the ui catalog, so Spanish shows "En línea" / "Sin conexión".
  - Server `message`s are no longer shown (`viewFromResult` sets `message: null`). The reason key plus the needs/scanned lines carry the detail.
  - `String(err)` is replaced by `floor.error.local`.
  - Pick, QC and press failures are translated through `floor.outbox.code.<CODE>`, and `BIN_OCCUPIED` is added.
- **PWA:**
  - `pwa-192.png`, `pwa-512.png`, `pwa-maskable-512.png` (full bleed, bars inside the safe zone) and `apple-touch-icon.png` (180, opaque), rendered from `icon.svg` with Chromium.
  - The manifest lists them; `index.html` adds `apple-touch-icon`, `theme-color` and an SVG favicon.
  - `setupI18n()` sets `<html lang>` from the device language before the first render.
- **i18n:** removed the unused `header.failed_*` and `press.replayBlocked`, and removed `pack.missingWarn`, `pack.packAnyway` and `reason.stain`.
- **Demo backend** (`?demo=1`) follows the same `packOrder` rules:
  - refuses when units are missing;
  - override for owner and admin only (demo login now gives them `production.override`);
  - key replay;
  - a handed order leaves the pack list.
- **`wrong_style` regression check:** still end to end. The en/es keys are untouched, the press E2E asserts "Wrong style", and T-4-1 re-checked `matcher.test.ts`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1a Mark packed calls packOrder; missing units listed and blocking | Yes | `e2e/floor.spec.ts`; `en-2-blocked-owner.png`, `es-7-blocked-packer.png` |
| 1b Hand to lead: override roles only, reason, `packed:false`+`override` → "Handed to lead", station cleared | Yes | `en/es-3-hand-dialog.png`, `en/es-4-handed.png`; packer screen has no button (`es-7`, asserted); DB below |
| 1c Progress survives reload, cleared on completion | Yes | `floor.spec.ts` reloads mid-order ("1 of 2" restored) and after completion (nothing restored) |
| 1d SW prompts, never auto-reloads | Yes | `registerType: "prompt"`; `dist/sw.js` skipWaiting only on message; `UpdatePrompt` + `onNeedReload` guard. The update-available path itself was not triggered in a browser (needs two builds served over a real SW); see gaps |
| 2 Problem dialog: 12 reasons en+es | Yes | `en/es-5-problem-reasons.png` |
| 3 QC/press truth; translated rejection; problem without item not dropped | Yes | code paths in `QcStation.tsx` / `PressStation.tsx`; `packOrder.test.ts`; the rejected-QC screen was not screenshotted (no easy live trigger) |
| 4 No English leaks (header, server messages, `String(err)`, `BIN_OCCUPIED`) | Yes | `es-6-offline-header.png` ("Sin conexión"); all es shots show no English |
| 5 `wrong_style` regression | Yes | `press.spec.ts` green ("Wrong style") |
| 6 PWA PNG/apple-touch icons; `<html lang>` from device | Yes | `dist/manifest.webmanifest` icons; `dist/index.html` has apple-touch; screenshot runs assert `document.documentElement.lang` = `es` / `en` before login |
| 7 E2E: pack with a missing unit (blocked), then complete | Yes | `e2e/floor.spec.ts` green |

## Checks I ran
| Repo | Command | Result |
|---|---|---|
| invai-floor (shared tree, my diff on `a0d88bd`) | `pnpm typecheck && pnpm lint && pnpm test && pnpm build` | clean / 72 files clean / 7 files, 82 tests passed / built |
| invai-floor | `playwright test` (all specs) against API :3140 + floor :5144 on a fresh `invai_t44_copy` | 3 passed: `floor.spec.ts`, `offline.spec.ts` (T-4-2), `press.spec.ts` |
| invai-ui | `pnpm typecheck && pnpm lint && pnpm test` | clean / 53 files clean / 4 files, 20 tests passed |
| bundle | gzip of `dist/assets/index-*.js` | 265.9 KB, against 262.7 KB at HEAD: **+3.2 KB, no new dependency**. It was already over the 150 KB budget before this card |

- An earlier full-suite run failed `press.spec.ts`: "a single-unit transfer_in order is waiting at the press". My screenshot runs had used up those seed orders.
- On a re-copied DB, all 3 specs passed.

## Exercised for real (API :3140 + worker, Redis db 4, `invai_t44_copy` migrated through 0016; floor :5144)
- **Blocked, then packed** (`floor.spec.ts`):
  - Setup: a 2-unit order, with one unit QC-passed and the other still `pressed`.
  - The tablet's pack list is made stale on purpose: a Playwright route adds the order. The real server only lists fully packed orders, so a short order reaches a tablet only through a stale list.
  - Scan one unit, then Mark packed. The real server answers `PACK_INCOMPLETE`, and the screen lists the missing unit as "Pressed".
  - Reload: the order comes back at 1 of 2. QC-pass the last unit, then Mark packed: packed.
  - `orders.get` shows `ready_to_ship` and every unit `packed`.
- **Hand to lead, as owner** (en and es runs). DB check:
  ```
  3104010619|in_production|Se perdió la transferencia|Riley Owner
  3104010175|in_production|Transfer lost, reprint coming|Riley Owner
  order.handed_to_lead | order.pack_override (1 unit(s) missing: …)
  ```
  The status stays `in_production`, the missing unit stays `pressed`, and `packOverride` is set.
- **Refused case:** as packer (PIN 1166), the Hand to lead button is absent (asserted). In the demo backend, a packer override throws `FORBIDDEN` (unit test). T-4-1 covered the server 403 for a packer.
- **Offline** (a temporary spec, deleted afterwards):
  - Offline, Mark packed on a complete order and on a short order. Both show "SAVED: NOT CHECKED YET" (`en-9`).
  - Back online: the complete order became `ready_to_ship`. The short one raised the alert (`en-10`), stays `in_production`, and is listed as blocked, with only "Remove" for a lead (`en-11`).
- **Demo mode** (`?demo=1`, en and es): scan 1 of #1050's 3 units, then Mark packed, then blocked, then Hand to lead dialog (`en/es-3`).
- Screenshots are at 1280×800 in `invai-docs/waves/4/reports/T-4-4/`, en-1…11 and es-1…8. I looked at all of them.
  - The first hand-dialog capture was mid fade-in, so the dialog looked behind the panel. I recaptured it after it settled, and the stacking is correct.

## Decisions
- **`packOrder` goes through the outbox, and a refusal is a result.** "Every write goes through the outbox" still holds: strict order behind queued QC passes, a durable key, and an offline pack that replays. A short pack is a business outcome like BLOCKED, so it must not park an entry for a lead in normal online use. The tech lead approved this design.
- **A new key per tap.** The backend stores only effective results, but the outbox's unique `id` index would turn a same-key re-enqueue into a no-op. That would break "Check again".
- **Mark packed stays enabled after one scan** (as before), and the server decides. The backend deliberately adds pack scans for packed units the packer didn't scan one by one (T-4-1 decision).
- **The server's English `message` is dropped from the press result** instead of shown under the translated reason. I changed `src/scan/pressFlow.test.ts:160` from `message: "server text"` to `message: null`. That test pinned the old leak, which AC 4 removes.
- **The E2E fakes a stale pack list** with `page.route`. No API can make a packed unit un-packed, and the server's pack queue hides short orders. The server's check itself is real.
- **The icons were generated once** with Playwright's Chromium, since there is no image tool on the machine. No build-time dependency was added.

## Known gaps and follow-ups
- **Not committed** (permission denial). The lead or owner needs to run the commit below.
- **The update prompt's live path was not exercised** in a browser. That needs a production build served twice with a changed SW. The code path is the plugin's documented `onNeedRefresh` / `onNeedReload`, and the built `sw.js` was checked.
- **A replayed short pack is alerted under T-4-2's title** "N offline scan(s) was/were rejected". The wording says "scan" for a Mark packed entry. The row itself reads correctly. This is a copy tweak for T-4-2's `outbox.alert.title`, if wanted.
- **`BIN_OCCUPIED` text is generic** ("that tote holds another order"). The outbox entry doesn't keep the error's `data.orderNo`, so `pick.binOccupied` (which names the order) stays unused.
- **The pack list is refreshed only by the existing queue invalidation.** A short order handed over on another tablet disappears on the next refresh.
- **Product-designer review:** the Problem dialog now has 12 buttons (4×3, 96 px). "Hand to lead" is the third button on the red panel.

## Blocked by other owners
- None open. Every cross-owner line was granted, as listed above.

## To commit (exact)
```
cd invai-floor
git add index.html vite.config.ts public/apple-touch-icon.png public/pwa-192.png public/pwa-512.png \
  public/pwa-maskable-512.png src/api/demo.ts src/api/rpc.ts src/api/types.ts src/api/packOrder.test.ts \
  src/app/actions.ts src/components/ProblemDialog.tsx src/components/SyncStatus.tsx \
  src/components/UpdatePrompt.tsx src/i18n/en.ts src/i18n/es.ts src/i18n/index.ts src/main.tsx \
  src/outbox/db.ts src/outbox/outbox.ts src/scan/pressFlow.test.ts src/scan/result.ts \
  src/screens/StationShell.tsx src/stations/PackStation.tsx src/stations/PickStation.tsx \
  src/stations/PressStation.tsx src/stations/QcStation.tsx e2e/floor.spec.ts
git diff --cached --stat   # 28 files, +1008 / -133
git commit -m "Floor: pack station asks the server (packOrder), hand to lead, floor polish (T-4-4)" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
cd ../invai-ui
git add src/floor/station-header.tsx
git commit -m "Floor header: Online/Offline through i18n (T-4-4)" \
  -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
Run it before T-4-3 or anyone else edits those paths. Otherwise stage by hunk.

## Processes and data
- **Stopped:** my API :3140, worker (Redis db 4) and floor dev server :5144. Ports are free.
- **Dropped:** `invai_t44_copy`. Valkey db 4 flushed.
- **Removed:** worktree `invai-floor-T-4-4`, the temporary baseline worktree, and the temporary screenshot/offline specs.
- **Shared dev DB `invai`:** untouched. It was used only as the template for the copy.
- **Unstaged changes:** in `invai-floor` (28 paths) and `invai-ui` (1 path).
