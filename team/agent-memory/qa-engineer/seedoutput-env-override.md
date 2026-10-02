---
name: seedoutput-env-override
description: seedOutput() in helpers/api.ts hardcoded the shared seed-output.json; fixed to honor E2E_SEED_OUTPUT_FILE for scratch-stack runs
metadata:
  type: project
---

2026-10-01 T-P7-1: `invai-web/e2e/helpers/api.ts`'s `seedOutput()` used to always read
`invai-backend/seed-output.json` regardless of the backend's own `SEED_OUTPUT_FILE` override, so step 8
(floor/station auth) failed with "Station token required" on every scratch-stack run (the shared file holds a
different company id's station token). Flagged but left unfixed by two earlier cards
(`waves/23/reports/T-23-8.md`, `waves/A1/reports/T-A1-report.md`) since it sat outside their owned paths — it's
in mine, so I added an `E2E_SEED_OUTPUT_FILE` env override (default unchanged). Set
`E2E_SEED_OUTPUT_FILE=<same path as the backend's SEED_OUTPUT_FILE>` on any future scratch-stack e2e run.

**Why:** the helper is QA-owned (`e2e/helpers/**`); fixing it once, generically, removes a repeat blocker for
every future scratch-stack card instead of each one re-discovering it.
**How to apply:** always pass `E2E_SEED_OUTPUT_FILE` alongside `E2E_API_URL` when running
`api-golden-path.spec.ts` (or any suite that calls `seedOutput()`) against a scratch DB.
