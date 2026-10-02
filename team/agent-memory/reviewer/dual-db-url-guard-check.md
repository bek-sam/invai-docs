---
name: dual-db-url-guard-check
description: Seed/reset "is this the shared DB" guards must check every pool the script writes through (DATABASE_URL and MIGRATION_DATABASE_URL); probe the mixed case
metadata:
  type: feedback
---
2026-10-01 T-P6-1: the seed guard only checked MIGRATION_DATABASE_URL. The seed also writes users through the auth `db` pool (DATABASE_URL, src/db/client.ts:8), so with DATABASE_URL=scratch and MIGRATION=invai the guard passed. Blocked on AC5 (architect R3).

**Why:** agents often export only one of the two URLs and keep the other from `.env`. A mixed run lands in two databases at once.

**How to apply:** for any guard in front of a db script, list which pools the script writes through (`systemDb` = MIGRATION, `db`/auth = DATABASE). Probe the guard with a throwaway tsx script that calls it exactly as main() does, with the URLs mixed. That is safe: it never runs the real seed against the shared `invai`. Also: the argv[1] main-guard (`fileURLToPath(import.meta.url) === process.argv[1]`) works from a symlinked /tmp path under tsx. See [[destructive-guard-review]].
