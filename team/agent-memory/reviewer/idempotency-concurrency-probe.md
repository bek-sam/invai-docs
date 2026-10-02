---
name: idempotency-concurrency-probe
description: Fast way to prove "one per key under concurrent calls" for claim-call-record services (SCAN forms, label buys) in a review worktree
metadata:
  type: feedback
---

2026-09-29 T-22-3: to prove a claim/call/record service is idempotent under concurrency, copy the card's
test file to a scratch `zz-review-*.test.ts` in your review worktree (reuses its fakes and fixtures),
append a test that wraps the fake carrier call in a 300 ms delay and fires 8 calls with
`Promise.allSettled`. Assert: 1 carrier call, 1 row, every rejection is `CONFLICT`. Delete the file after.
Also: `pnpm typecheck/lint` refuse to run in a worktree with a symlinked `node_modules` ("workspace hoist
directory is not a real directory"); run `./node_modules/.bin/tsc --noEmit` and `biome check .` directly.
The scan script's base (`<first sha>~1`) can pull in other cards' interleaved commits; filter by
`git show --name-only` per reviewed sha. See [[env-backend-worktree-review]].
