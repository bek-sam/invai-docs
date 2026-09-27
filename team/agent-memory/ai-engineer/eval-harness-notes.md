---
name: eval-harness-notes
description: How to run invai-backend AI evals without touching the shared dev DB, and what typecheck/lint does not cover there
metadata:
  type: project
---

`pnpm evals` creates eval tenants in whatever DB env points at (default: the shared dev DB `invai`). Run it as `NODE_ENV=test TEST_DATABASE_URL=... TEST_MIGRATION_DATABASE_URL=... tsx evals/run.ts <route> --json <file>` to hit your own test DB instead; then merge only your route into `evals/baseline.json`.

**Why:** the agent brief requires an own test DB per card, and the eval harness has no DB flag of its own (learned on T-17-2, 2026-09-26).

**How to apply:** `evals/**` is outside the backend tsconfig and biome includes, so `pnpm typecheck`/`pnpm lint` never check eval code; running the eval is the only check. Assistant cases needing real numbers use `vars.tenant: "seeded"` (evals/assistant/seed.ts); the default eval tenant must stay empty for zero-state cases. See [[assistant-analyst-tools]].
