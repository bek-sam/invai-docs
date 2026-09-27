---
name: lib-queues-opens-real-redis-on-import
description: importing src/lib/queues.ts (even just for permanentFailure) connects a real ioredis client at module load, which hangs a one-off tsx script
metadata:
  type: feedback
---

`invai-backend/src/lib/queues.ts` does `export const redis = new Redis(env.REDIS_URL, ...)` at
module top level. Any file that imports from it — even just for `permanentFailure` — opens a real
Redis connection as a side effect of import. A one-off `tsx` exercise script that imports such a
module (directly or transitively) will run `main()` to completion, print its output, and then
hang forever on that open handle instead of exiting, because nothing calls `process.exit()`.

**Why:** Lost time on T-18-2's verification script (`src/integrations/market/http.ts` imports
`permanentFailure` from `lib/queues.ts`); the background run showed zero bytes of output for
minutes even though the script had actually finished — Node just never flushed/exited.

**How to apply:** Any throwaway `tsx` script that imports something from `src/lib/queues.ts`,
`src/integrations/suppliers/ratelimit.ts`, or anything else that opens a Redis/DB connection at
import time needs an explicit `process.exit(0)` after its `main()` promise resolves. Don't assume
a quiet background task means "still running" — check whether the imported modules hold open
handles first.
