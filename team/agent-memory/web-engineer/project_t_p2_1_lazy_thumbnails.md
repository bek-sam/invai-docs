---
name: project-t-p2-1-lazy-thumbnails
description: T-P2-1 (gate root-cause §1) facts — invai-ui Skeleton doesn't carry data-slot=skeleton today, and the in-memory sign-in/session rate limit resets on an API process restart.
metadata:
  type: project
---

From T-P2-1 (2026-09-30), fixing the gate failure where the catalog designs grid fired ~40
`files.downloadUrl` calls on mount (see [[feedback-orpc-queryoptions-always-aborts]]):

- `@invai/ui`'s `Skeleton` component (`invai-ui/src/components/skeleton.tsx`) as of this date is
  just `<div className="animate-pulse rounded-md bg-muted" />` — no `data-slot="skeleton"`
  attribute, and the class is `animate-pulse` not `animate-spin`. `e2e/helpers/ui.ts`'s `settled()`
  polls `[data-slot=skeleton], .animate-spin` to decide the page is done loading, so today it does
  **not** actually wait on any `<Skeleton>` the app renders — it only matches literal spinners.
  Worth knowing before trusting `settled()` to gate on a loading grid of images; already flagged to
  qa-engineer via the root-cause doc, not fixed here (out of owned paths).
- The sign-in / session-check rate limiter (decision 0008, 20/min per IP) is in-memory per API
  process. Running `pnpm e2e` against the same long-lived `pnpm dev:api` process several times in a
  row for manual verification can trip it (429s on `get-session` or the login POST) well before any
  real usage would — it looks like a login timeout or a "every screen" smoke failure. Restarting
  the API process (fresh in-memory bucket) and running once cleanly is the fix, not retrying in a
  loop.
