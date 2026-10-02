---
name: sse-client-stop-probes
description: Probes for floor fetch-SSE client stop/retry changes (connectSse) - scratch vitest in /tmp archive, what to check
metadata:
  type: project
---
2026-10-01 T-P6-3: for connectSse (invai-floor/src/realtime/sse.ts) stop/retry changes, drop a scratch probe test into a /tmp git-archive copy (symlinked node_modules) using ReadableStream fake responses with minDelayMs:1. Check: shutdown+retry and 5xx/network errors still reconnect; a control event followed by more events in the same chunk (the parser callback keeps firing after `stopped`); an event without a `data:` line is dropped per WHATWG (confirm the backend sends `data: ""`, which Hono does). The floor build needs `VITE_API_URL=""` (vite.config guard).
**Why:** setting `stopped` in the parser callback does not end the read loop.
**How to apply:** any future floor realtime card; see [[floor-offline-replay-checks]].
