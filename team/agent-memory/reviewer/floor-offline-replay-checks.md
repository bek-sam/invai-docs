---
name: floor-offline-replay-checks
description: Floor scan gates (maintenance, holds, windows) must be judged at the client scannedAt, not only "now" — probe offline replay with a past scannedAt
metadata:
  type: feedback
---

2026-09-29 T-22-4 r1 (changes-required): the station-maintenance block checked only for a window open *now*. A scan made offline during the window and synced after it ended pressed normally (scratch probe with a past `scannedAt`). The matcher already trusts `scannedAt` for stale-scan logic (`matcher.ts`), so time-windowed gates should too.

**Why:** floor tablets queue scans offline (outbox) and replay them later with the original `scannedAt`. A gate that reads only current state misses the offline case, and that case is exactly what the tech lead asks about.
**How to apply:** for any new floor gate, write a scratch probe (in a `git archive` copy, own DB) that starts the gate, ends it, then replays a scan with a `scannedAt` inside the window. Also probe a floor-session ctx with no `input.stationId` (`ctx.station` fallback) and concurrent start/end. See [[idempotency-concurrency-probe]], [[env-backend-worktree-review]].

2026-09-29 T-23-2 r1 (approve): when the floor-side change is pure display/plumbing over an already-reviewed backend enum value (here `station_maintenance` riding the existing generic `mismatch`→`blocked` tone/outbox-park path), a live demo-mode probe is enough — no need to re-derive the offline-replay case if the backend gate was already probed under the originating card (cross-reference its review). Live-probing `invai-floor`'s demo API: log in via `page.getByRole('button', { name: '<digit>' })` × 4 + `Confirm`, then pick a station; demo `uid(prefix, n)` ids are deterministic (`00000000-0000-4000-8<prefix:3hex>-<n:12hex>`, n = 1-based call order of `item()`/`blank()` in `demo.ts`) so you can type a specific order's transfer/blank code via `page.keyboard.type(id) + Enter` without touching the UI list. For a camera-permission-timing probe, launch Chromium with `--use-fake-device-for-media-stream --use-fake-ui-for-media-stream` and wrap `navigator.mediaDevices.getUserMedia` via `page.addInitScript` + `context.exposeFunction` to count calls before/after the tap.
