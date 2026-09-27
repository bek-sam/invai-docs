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

For quick Playwright scripts outside `e2e/`, `invai-web` only has `@playwright/test`, not the
`playwright` package — `import { chromium } from "@playwright/test"`.
