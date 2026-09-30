# Review of T-23-2 (round 1, co-review scope: camera Permissions-Policy + CameraScan.tsx only)

- Reviewer: security-reviewer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-floor show 382ad42 -- vite.config.ts nginx.conf.template src/components/CameraScan.tsx src/lib/barcodeDetector.d.ts` | reviewed diff directly |
| `grep -n "DialogPrimitive.Content" invai-ui/src/components/dialog.tsx` | no `forceMount`: Radix unmounts `DialogContent` (and the `<video>`) on close, confirming the race below |
| `cat invai-floor/src/scanner/bus.ts` | `emitScan` forwards only the decoded string; no frame/canvas is captured, stored or sent anywhere |

## Findings
1. **Permissions-Policy scoping — OK.** `camera=()` → `camera=(self)` in both `vite.config.ts` and `nginx.conf.template` is the narrowest change: `self` is the feature's own default allowlist, it only re-enables the top-level origin (no `*`, no cross-origin iframe), and it's the only line touched in both files — `microphone`, `geolocation`, `payment`, CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy` are byte-identical to before.
2. **`CameraScan.tsx:43-58` — camera can be left running after the dialog is closed (fails "tracks stopped on close").** `start()` sets `setOpen(true)` before `await getUserMedia(...)`. If the user closes the dialog (`close()` → `stop()`) while the *browser's* (non-blocking, e.g. Chrome/Android) permission prompt is still pending, `stop()` runs while `streamRef.current` is still `null` — a no-op. When the promise then resolves, the code unconditionally does `streamRef.current = stream; ... detectorRef.current = new Detector(); loop();`, with no check that the dialog is still open. `DialogContent` has already unmounted (no `forceMount`), so `videoRef.current` is `null` and `loop()`'s guard just re-schedules itself forever via `requestAnimationFrame` — the track is never stopped and CameraScan is mounted persistently in `StationShell`'s header, so this can run for the rest of the tablet session with no visible indicator or way to turn it off short of the OS camera toggle.
   - No PII/image data leaves the device from this path (confirmed via `bus.ts`), so I'm not treating it as a PII leak — it's a "handle the stream safely" gap, not a tenancy/auth issue.
   - **Exact fix:** track open-ness in a ref set by `close()`/the unmount effect (e.g. `openRef.current = false`), and right after `getUserMedia` resolves, check it: if the dialog was closed in the meantime, stop the newly obtained stream's tracks immediately and return, instead of assigning `streamRef`/starting `loop()`.

## Acceptance criteria (AC5 only)
| # | Met? | Evidence |
|---|---|---|
| 5 — no permission prompt until tapped | yes | `getUserMedia` only called inside `start()`, only reached after the button's `onClick`; unsupported-browser path never calls it (toast only) |
| 5 — stream/tracks handled safely | **no** | finding 2 above: close-before-grant race leaves the camera live indefinitely |

## Blocking findings
1. `invai-floor/src/components/CameraScan.tsx:43-58` — camera track can stay active after the user closes the scan dialog, if `getUserMedia` resolves after `close()` already ran. See exact fix above.

## Checks
- [x] Only owned paths in scope for this co-review reviewed (`vite.config.ts`, `nginx.conf.template` flagged by the author as outside the card's listed globs — that's for the primary reviewer's ownership call, not mine)
- [x] Permissions-Policy: narrowest possible, no other directive touched
- [ ] CameraScan.tsx handles the stream safely on every path (fails on close-during-permission-prompt)
- [x] No frame, image or PII sent, stored or logged from the camera path

## Optional notes (not blocking)
- None.
