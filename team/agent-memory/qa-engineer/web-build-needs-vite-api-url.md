---
name: web-build-needs-vite-api-url
description: invai-web has no local .env by default; `pnpm build` fails fast on a missing VITE_API_URL (CSP connect-src guard) unless set explicitly. Also, VITE_API_URL is baked at build time only — E2E_API_URL never touches it, and the shared dist/ folder gets fought over by concurrent agents.
metadata:
  type: project
---

`invai-web` only ships `.env.example` (`VITE_API_URL=http://localhost:3000`), no `.env`. A bare
`pnpm build` (part of the repo checks in `verify-and-report` / `independent-review` /
`run-golden-path` gates) fails with `Error: VITE_API_URL must be set to build for production` from
`vite.config.ts`'s `requireApiOrigin` guard — it derives the CSP `connect-src` from it so a real
origin is pinned instead of a broad `https:`.

**Why:** this is intentional (security), not a bug — but it wastes gate time if you don't expect
it.

**How to apply:** when running the web repo's `pnpm build` check locally, pass
`VITE_API_URL=http://localhost:3000 pnpm build` explicitly rather than treating the bare-run
failure as a code regression.

**Second lesson (wave 19, running `e2e/digest.spec.ts` against an isolated stack):**
`E2E_API_URL`/`E2E_WEB_URL` only steer Playwright's own `baseURL` and the `Session` helper
(`e2e/helpers/api.ts`) — they never touch the actual React app's own API calls. Those go to
whatever `VITE_API_URL` was baked into the JS bundle at the *last* `vite build`. `invai-web`'s
`dist/` is a single shared, gitignored directory: another agent rebuilding it (their own
`VITE_API_URL`, e.g. the default `:3000`) mid-session silently redirects your browser's real
traffic to their backend while every Playwright-level check (page loads, `Session` calls) keeps
looking fine, because those never go through the bundle. Symptom: tests that touch a public,
unauthenticated fetch (like `unsubscribe.tsx`'s own `fetch`) fail with a generic client-side error,
while oRPC-backed pages can look like they pass by accident if the other agent's backend happens to
have similarly-named seed data (e.g. "Desert Bloom Tees" exists everywhere).

**How to apply:** build to an isolated `--outDir` (`vite build --outDir dist-qa<port>` with your own
`VITE_API_URL`) and serve *that* with `vite preview --outDir dist-qa<port> --port <port>`, never the
shared `dist/`. Verify with `grep -o "localhost:[0-9]*" dist-qa<port>/assets/env-*.js` before trusting
any test result.
