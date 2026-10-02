---
name: scratch-stack-pitfalls
description: Two environment traps that make a scratch (non-default-port) web/API stack look totally broken, unrelated to the spec under test
metadata:
  type: project
---

T-23-9 (2026-09-30): when standing up a scratch API on a non-3000 port for a browser E2E run
(`invai-web` dev server + a scratch `invai-backend` API), two things bite hard, both looking like
"every test fails at login with a generic connection error":

1. **`invai-web/vite.config.ts:16,33`** hardcodes the dev-mode CSP's `connect-src` to
   `http://localhost:3000` only — it is NOT derived from `VITE_API_URL` in plain `vite`/`pnpm dev`
   mode (only the `build`/`preview` CSP reads `process.env.VITE_API_URL`, via
   `requireApiOrigin`/`connectSrc` in `src/lib/build/csp.ts`). Point a scratch API at any port other
   than :3000 and every browser `fetch`/XHR from the app is silently CSP-blocked, surfacing as the
   app's generic "No podemos conectar con InvAI" / "can't connect" fallback on every `loginAs` call —
   NOT a real bug in the spec or product logic. Confirm with `curl -si <weburl>/ | grep -i
   content-security-policy` — if `connect-src` doesn't list your API's port, that's it. Fix: run the
   scratch API on :3000 itself if free (`lsof -iTCP:3000 -sTCP:LISTEN`), not the card's suggested
   alternate port, and say so in the report. Filed as a gap for web-engineer (parameterize `devCsp`
   like `prodConnectSrc` already is).

2. **`invai-backend`'s `pnpm db:reset` also obliterates BullMQ queues** (`src/db/reset.ts:91`,
   `obliterateQueues()`) in whatever `REDIS_URL` is currently set — it does NOT scope by the target
   Postgres DB name. The `.env` default is `redis://localhost:6379` = **DB 0, the shared dev Redis**.
   Resetting a differently-named scratch Postgres DB (e.g. `invai_seed_t239`) does NOT protect the
   shared Redis: always pass `REDIS_URL=redis://localhost:6379/<private index>` (agent-brief's 1-14
   range) to EVERY backend command (`db:reset`, `db:migrate`, `db:seed`, `dev:api`) for a scratch
   stack, not just the ones that "obviously" touch Redis.

Also: `pnpm db:seed` writes the shared `invai-backend/seed-output.json` unless
`SEED_OUTPUT_FILE=<path>` is set — back it up first regardless (seed IDs turned out deterministic
across DBs in one observed run, so the file came back byte-identical, but don't rely on that).

**Why this matters:** without isolating both, a scratch stack's entire browser suite fails
identically at `loginAs`, and it's easy to misdiagnose as a real product/auth bug (chased a Vite
`e2e/.results`-triggers-reload-storm red herring first — real but not the actual cause; the CSP port
mismatch was). Check CSP and Redis DB isolation BEFORE debugging login failures on a scratch stack.
