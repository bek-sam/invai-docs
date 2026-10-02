---
name: project-scratch-stack-tips
description: T-P4-1 tips for a scratch API+worker stack and one-off tsx scripts outside the repo
metadata:
  type: project
---

- A nohup'd worker has no port: find its PID with `lsof -t /tmp/<its log>` (the process holding your log open), not by command line.
- One-off tsx scripts in /tmp must be `.mts` (top-level await) and import repo code and packages by absolute path (`.../invai-backend/node_modules/drizzle-orm/index.js`).
- `importNormalizedOrders` returns parse errors in `result.errors` (all counters 0), e.g. `buyerName` must be a string.

**Why:** cost several retries on T-P4-1's AC6 re-import check. **How to apply:** scratch exercises on a pg_dump copy of dev.
