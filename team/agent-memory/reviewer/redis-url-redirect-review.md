---
name: redis-url-redirect-review
description: How to prove which Redis DB a test run really uses (MONITOR per-db prefix) and probe URL-parsing guards against ioredis's own parser
metadata:
  type: feedback
---

2026-09-29 T-23-0 r1: `valkey-cli monitor` (read-only, backgrounded during the test run) prefixes each
command with `[<db> <client>]`, so it proves which DB a test's commands really hit. Each ioredis client
sends `HELLO 3` on DB 0 before `SELECT n`; that is expected, not a leak. For any guard that parses a
Redis URL's DB, check it against what ioredis 6 actually does (`parseInt(pathname.slice(1), 10)`,
`Redis.js:725`), not `Number()`: `/0/` and `/0.5` stayed on DB 0 even though the guard said "non-zero".
**Why:** the tech lead asked "no path can leave tests on DB 0". A probe that booted env.ts, built an
ioredis client and ran `CLIENT INFO` showed the gap in minutes.
**How to apply:** for env/URL redirect cards, probe odd spellings through the real client library.
Related: [[env-backend-worktree-review]].

2026-09-29 T-23-0 r2: since B-205, a plain `pnpm test` uses DB 15, and other agents' plain runs use it too.
Before a plain run, check `valkey-cli client list | grep db=15` and `ps aux | grep vitest`, and wait for
any other run to finish. Don't flush DB 15 afterwards if it holds other agents' keys. macOS has no
`timeout`: use `docker exec <ctr> timeout N valkey-cli monitor`. The guard hook blocks the p-kill command.
