---
name: camera_permission_race_pattern
description: T-23-2 camera-scan co-review — check Permissions-Policy scoping AND the close-before-grant race in getUserMedia code
metadata:
  type: project
---

T-23-2 (floor camera scanner via `BarcodeDetector`): `camera=()` → `camera=(self)` in
`vite.config.ts`/`nginx.conf.template` was the narrowest possible fix (self is the feature's own
default allowlist; no other directive touched) — approved that part outright.

The real bug was in `CameraScan.tsx`, not the header: `setOpen(true)` happens *before*
`await getUserMedia(...)`. If the dialog is closed while the browser's permission prompt is still
pending (non-blocking on Chrome/Android — the page stays interactive), `close()`'s `stop()` runs
while the stream is still `null` (no-op), then the later-resolving promise unconditionally assigns
the stream and starts the detect loop with no open-check. If the dialog component has no
`forceMount`, its `<video>` has already unmounted, so the loop can't even attach it, but never
stops the track either — camera stays live for the rest of the session.

**How to apply:** for any `getUserMedia`/`getDisplayMedia` review, don't just check "does close()
stop tracks" — check whether the stream-acquiring `await` can resolve *after* the UI already
called close(). Grep for the pattern `setOpen(true)` (or equivalent) placed before the `await`,
and confirm there's an open-ness ref checked right after the promise resolves. This is a
device-safety/hardening finding (S-44), not PII — separately verify no frame/canvas is captured,
stored or sent (check the emit/bus function the decoded value flows through).
