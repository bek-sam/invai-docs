---
name: wave-p6-t1-safe-reset-seed
description: db:reset/db:seed now refuse on a scratch DB without a pinned Redis DB / SEED_OUTPUT_FILE
metadata:
  type: project
---

T-P6-1 (2026-10-01, B-219) added `assertSafeToReset` (`src/db/reset.ts`) and `assertSafeToSeed`
(`src/db/seed/index.ts`): both are pure functions that throw before any Postgres/Redis I/O when
the target database isn't the shared `invai` and the matching safety env var (`REDIS_URL` pinned
non-zero, `SEED_OUTPUT_FILE` set) is missing. `invai` itself is always exempt, so
`invai-infra/scripts/gate.sh` and CI keep working unchanged.

**Why this needed more than "add a check":** `src/db/seed/index.ts` called `main()`
unconditionally at module scope (no `fileURLToPath` guard, unlike `reset.ts`), so importing the
module to unit-test the new pure function would have run a real seed. Added the same
`if (process.argv[1] && fileURLToPath(import.meta.url) === process.argv[1])` guard reset.ts
already used, around the `main().catch(...).finally(...)` block. `pnpm db:seed` behavior as a
script is unchanged; it's only importability that changed.

`src/env.ts`'s `isPinnedNonZeroDb` (used for `TEST_REDIS_URL`) is private/unexported and
`env.ts` is outside backend-foundation's card-owned paths for this card, so the same
positive-integer-path regex was duplicated locally in `reset.ts` as `isPinnedNonZeroRedisDb`
rather than importing it. If a third place needs this check, it's worth promoting to a shared
`src/lib` helper with its own test (per the modules README rule on cross-cutting helpers) instead
of a third copy.

**How to apply:** before adding a guard/pure-function to any script file that unconditionally
invokes `main()` at module scope, check whether the file is import-safe first. See also
[[wave-p5-seed-cleanup]] (why these two env vars matter) and the B-219 incident history
(2026-09-29 T-23-9, 2026-10-01 T-P5-1) in `invai-docs/waves/P5/wave.md`.
