---
name: web-build-needs-vite-api-url
description: invai-web has no local .env by default; `pnpm build` fails fast on a missing VITE_API_URL (CSP connect-src guard) unless set explicitly.
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
