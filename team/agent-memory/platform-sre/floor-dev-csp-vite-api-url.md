---
name: floor-dev-csp-vite-api-url
description: invai-floor's dev-mode vite server breaks if VITE_API_URL is set alongside plain `vite` (not build/preview) — CSP blocks the request
metadata:
  type: project
---

`invai-floor`'s dev CSP (`vite.config.ts` `devCsp`) is `connect-src 'self'` only, by design: dev mode
proxies `/rpc` and `/events` same-origin to `VITE_API_PROXY` (default `http://localhost:3000`,
`vite.config.ts:8`). But `invai-floor/src/lib/config.ts` reads `API_URL` unconditionally from
`VITE_API_URL` when it's set, and `src/api/rpc.ts`'s `rpcUrl()` uses that absolute URL instead of the
relative `/rpc` proxy path whenever it's non-empty. So starting plain `vite` (dev server, not
`build`/`preview`) with `VITE_API_URL` set makes every floor API call a cross-origin fetch that its own
strict dev CSP then blocks — the tablet UI shows "Can't reach the server. Check Wi-Fi and try again." on
literally the first request (station connect), and the browser network log shows **no request at all**
(a CSP block prevents dispatch; it isn't a real network error, an AbortError or a slow response).

**Why:** Found in T-23-7 round 2 while proving the B2 worker-ordering fix locally:
`invai-infra/scripts/ci/run-e2e.sh` inherits `VITE_API_URL=http://localhost:3000` at the job/env level
(needed by `ci.yml`'s `pnpm build` step for web and floor), and that same env leaked into the dev-mode
floor process the E2E script also starts. Reproduced 100% (3/3 floor spec failures, both in the full
run and isolated with only api+floor running, ruling out resource contention). Fixed by unsetting
`VITE_API_URL` specifically for the floor dev-server process in `run-e2e.sh` and exporting
`VITE_API_PROXY="http://localhost:$API_PORT"` instead. `invai-web`'s dev CSP does **not** have this
problem — its `devCsp` hardcodes `connect-src 'self' http://localhost:3000 ...` regardless of
`VITE_API_URL`, so web can safely run dev mode with `VITE_API_URL` set.

**How to apply:** Any future script or workflow that starts `invai-floor`'s plain `vite` dev server
(not `build`/`preview`) must either leave `VITE_API_URL` unset, or must not inherit a job-level
`VITE_API_URL` meant for a build step into that process's env. If floor CI/dev tooling changes again,
check `invai-floor/vite.config.ts` (`devCsp`) and `src/lib/config.ts` (`API_URL`) together before
assuming a "can't reach the server" floor failure is a real backend/network issue — check the
Playwright trace's network log first: zero entries for the failing call means CSP, not network.
