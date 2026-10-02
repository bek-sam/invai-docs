---
name: test-infra-notes
description: Vitest 5 globalSetup/inject channel, and a fake-timer/ioredis interaction that hangs tests
metadata:
  type: feedback
---

From T-P1-1 (per-run test DB/Redis DB, B-228).

- `vi.useFakeTimers()`, even restricted to `toFake: ["setTimeout","clearTimeout"]`, reproducibly
  hung a real ioredis round trip (the market rate limiter's `takeToken`) made right after
  installing the fake clock. Stubbing only `global.setTimeout` to run its callback immediately
  fixed it with no such interaction — ioredis/pg hold a module-load-time reference to the real
  `setTimeout`, so faking the global doesn't touch them, but something about the fake-timer
  install itself still broke the round trip.
- Postgres advisory locks are scoped per database the locking session is connected to — serializing
  `CREATE DATABASE ... TEMPLATE` across processes needs the lock held on a connection to a *fixed*
  db (e.g. `/postgres`), not to the template itself.
- Vitest 5's `globalSetup` default export receives the `TestProject` itself as its sole argument
  (`node_modules/vitest/dist/chunks/plugin.d.*.d.ts`: `globalSetupFile.setup?.(this)`), with a
  `.provide(key, value)` method. `setupFiles` (not globalSetup) is where `inject()` works to read
  it back — this is the documented, pool-agnostic channel for globalSetup→worker data, safer than
  assuming `process.env` mutated in globalSetup propagates into a forked/threaded worker.
