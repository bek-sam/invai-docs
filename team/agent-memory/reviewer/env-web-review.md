---
name: env-web-review
description: How to stand up a live web+API review environment for invai-web cards (ports, DB, CORS)
metadata:
  type: feedback
---

When exercising an `invai-web` card live on a spare API port: `pnpm db:migrate` reads
`MIGRATION_DATABASE_URL`, not `DATABASE_URL` (`invai-backend/src/db/migrate.ts`) — set both to the
scratch DB or the migration silently runs against the wrong database and reports "up to date".

`vite preview` on a non-default port needs the API's CORS to allow it: start the API with
`WEB_ORIGIN=http://localhost:<preview-port>` (`invai-backend/src/api/app.ts`'s `cors()` only allows
`env.WEB_ORIGIN`/`env.FLOOR_ORIGIN`), otherwise every request fails with a CORS error that looks
like a broken build, not a config gap. Also rebuild `dist/` fresh (`rm -rf dist && VITE_API_URL=...
pnpm build`) before trusting a `vite preview` run — a stale `dist/` from an earlier build with a
different `VITE_API_URL` can silently serve the wrong baked-in API origin (grep
`dist/assets/env-*.js` for the port to confirm).

For quick Playwright scripts outside `e2e/`, `invai-web` only has `@playwright/test` hoisted to a
top-level `node_modules` symlink (bare `playwright` is only nested in the pnpm store, unresolvable
by a bare import) — `import { chromium } from "@playwright/test"`. But a script living outside the
repo (e.g. a reviewer's scratchpad) can't resolve *either* bare specifier at all: Node resolves
bare imports by walking up from the importing file's own directory, and a `/tmp` script has no
`node_modules` ancestor. Either put the script inside the repo temporarily (then delete it before
committing anything — never commit a reviewer scratch file), or import the fully-resolved absolute
path into the pnpm store (`.../node_modules/.pnpm/playwright@<ver>/node_modules/playwright/index.mjs`)
from the scratchpad script.

Login form fields in `invai-web` use `id="email"`/`id="password"` (`src/routes/login.tsx`), not a
`name` attribute — `page.fill('#email', ...)`, not `input[name="email"]`. Also
`page.waitForURL('${base}/**')` matches `/login` itself (it's a subpath of base), so it resolves
instantly on a *failed* sign-in too; wait for a real signal instead
(`page.waitForFunction(() => !location.pathname.startsWith("/login"))`).

oRPC RPC calls over curl: the path is `/rpc/<namespace>/<procedure>` (not `/api/rpc/...`), and the
POST body must be wrapped as `{"json": {...}}` (oRPC's batch envelope), even for an empty input
(`{"json":{}}`) — an unwrapped body fails Zod's "expected object" check before your own auth/permission
code ever runs, which can look like a routing bug. The app's own language toggle persists to
`localStorage["invai.lang"]` (`src/i18n/index.ts`), not the generic i18next `i18nextLng` key; setting
the wrong key silently leaves the app in whatever `navigator.language` implies.
