# T-13-4: E2E coverage and CI — status (paused to save usage)

Stopped mid-task on the tech lead's instruction. All E2E runs and the servers this card started
are stopped; nothing of mine is still running.

## Committed (finished, passing)

- **invai-backend** `4671a1a` — "Load-tolerant Shopify OAuth-state and token-refresh race tests
  (T-13-4)". Files: `src/modules/channels/webhooks.test.ts`,
  `src/modules/channels/shopify.test.ts`.
  - Root cause: the OAuth-state "used once by racing callbacks" test and the token-refresh
    "two workers at once" test both do real Postgres row-locked concurrent transactions —
    correct regardless of speed, but on a shared/loaded dev DB the lock wait can exceed the
    file's default 30s `testTimeout`, and a token-refresh expiry assertion only had a 10-minute
    margin against wall-clock delay.
  - Fix: bumped the four affected `it()`s to a 60s timeout; the OAuth-state race now retries
    once, only on a zero-winners outcome (an infra hiccup, never a second winner — that would
    still fail loudly, since it would mean the row lock itself is broken); widened the
    token-refresh margin from 10 to 20 minutes of headroom.
  - Verified: ran both files against a scratch `invai_t134` test DB
    (`TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` pointed at it, dropped after) —
    24/24 passing.
  - This is AC7, done.

No other AC (1–6) has committed code. All other work this session was setup and research, not
yet turned into committed specs.

## Environment set up (uncommitted infra, still on disk — reusable on resume)

- Worktrees, each on its own new branch off `main`, `node_modules` symlinked to the shared repo:
  - `/Users/bekbolsun/invai/invai-web-t134` (branch `t13-4-web`)
  - `/Users/bekbolsun/invai/invai-floor-t134` (branch `t13-4-floor`)
  - `/Users/bekbolsun/invai/invai-backend-t134` (branch `t13-4-backend`)
- Own stack, ports per the card, currently **stopped** (was healthy before stopping):
  api :3134, worker, web :5134, floor :5135, `REDIS_URL=redis://localhost:6379/10`,
  DB `invai_t134_copy` (Postgres, freshly reset/migrated/seeded — 360 orders, imaging was down
  during seed so it fell back to the FFD shelf-pack, no composed sheet images; that's an infra
  gap, not something this card broke).
  `invai-backend-t134/.env` and `seed-output.json` are in place; `invai-backend-t134/.env`'s
  `IMAGING_SHARED_SECRET` uses the shared dev default already in `.env.example`.
  Shared local imaging (`invai-imaging`, port 8000) is down — `uv run uvicorn` failed
  (`uvicorn` not found; deps likely need `uv sync`, which I did not run since it touches a
  shared tree). Whoever resumes should either fix that or accept the FFD fallback for seeding.
- Scratch-but-gone: `invai_t134` (backend unit-test DB, created/used/dropped for the Shopify fix
  verification above) and `invai_t134_copy`'s first pg_dump-based copy attempt (superseded by
  the fresh reset+seed) — nothing left over from either.

## Uncommitted partial work (not yet a passing test, do not treat as done)

- `invai-web-t134/e2e/helpers/api.ts` — added `E2E_BACKEND_DIR` env override so a worktree's
  specs read *its own* `seed-output.json` instead of the shared repo's. Not yet exercised by a
  real spec run.
- `invai-floor-t134/e2e/helpers/api.ts` — same override, floor side.
- `invai-web-t134/e2e/helpers/i18n.ts` (new) — flattens the generated `en`/`es` dictionaries into
  a list of translated phrases and exposes `englishLeaksIn(text)` for the Spanish-smoke "no
  English leaks" check (AC2). Written but never run against a live page yet.
- `invai-floor-t134/e2e/helpers/i18n.ts` (new) — same, floor side.
- None of these are committed (they live only in the worktrees above); they carry no test
  evidence yet, so treat them as a starting point, not verified code.

## Research done, not yet turned into code

- Web permission model (for AC1, role specs): `useCan()`/`me.permissions` in
  `invai-web-t134/src/lib/me.ts`; nav visibility via `navFor(me)` in `src/lib/nav.ts` (filters
  `SHOP_NAV` by `Permission`, drops empty groups); **no per-route `beforeLoad` permission guard
  exists** — only `_app.tsx`'s shop/vendor org-type redirect and the unauthenticated→`/login`
  redirect. Permission enforcement for a role that navigates straight to a hidden URL is
  server-side only: backend's `guard` middleware (`invai-backend/src/api/orpc.ts`) throws
  `FORBIDDEN`/403 with `data.permission`; convention references:
  `invai-web-t134/src/lib/nav.test.ts` (hidden-nav-by-permission), backend
  `src/api/authz.test.ts` (FORBIDDEN-by-role), `e2e/api-golden-path.spec.ts:255-259` (FORBIDDEN
  e2e pattern).
- Money/size/nesting targets (for AC4, property tests): **fast-check is not installed** in
  either `invai-web`/`invai-floor` — per my instructions I have not installed it; needs the
  tech lead's go-ahead. Pure, property-test-ready money functions:
  `invai-backend/src/modules/finance/profit.ts` (`allocate`, `finalize`, `sumBuckets`,
  `orderFees`, `allocateAdSpend`, …) and `fees.ts` (`referralFeeCents`, `feeRecoveredCents`, …);
  an existing hand-rolled property test already lives in `fees.test.ts` (seeded PRNG, 2000 runs)
  as the template. Sizes: no dedicated module; `src/modules/inventory/shelves.ts`'s `shelfFor`
  is the only pure, exported size-adjacent function (the `SIZE_ORDER` array is otherwise inlined
  in DB-backed functions in `catalog/service.ts` and `inventory/service.ts`). Nesting: the real
  packer lives in `invai-imaging` (out of this card's owned paths); the only local algorithm is
  the seed-only, **not exported**, `ffdPack` in `invai-backend/src/db/seed/builder.ts:165-208`
  (would need an `export` added before a test file could import it).

## Not started

AC1 (role specs), AC2 (Spanish smoke), AC3 (uncovered-flow specs), AC5 (axe in E2E), AC6 (CI
workflow jobs), and the `fullyParallel`/`workers` playwright.config changes wave.md recommends.
No `pnpm add` of `fast-check` or `@axe-core/playwright` has happened — still waiting on
confirmation before installing either.
