---
name: run-golden-path
description: Prove InvAI still works end to end. Clean start, fresh reset/migrate/seed of the local dev DB, then the API golden path, browser golden path plus screens smoke, and the floor tablet suite, with evidence and cleanup. Use at the wave integration gate, before a release, demo or pilot, after touching a golden-path area, or when asked to "run E2E" or "golden path".
---

# Run the golden path

On a freshly seeded stack, all 13 golden-path steps pass through the API and the browser, every screen loads
clean, and the floor blocks a wrong blank, with the output saved as evidence.

## When to use
- Wave step 6 (integration gate): tech lead plus QA.
- `release-checklist` and `deploy-to-environment` prerequisites.
- A card touched a golden-path area (import, SKU map, proof, sheet build, vendor portal, receiving, floor,
  label and tracking, profit, AI draft and trademark, assistant, tenant isolation).

## Before you start
- **You need the shared dev DB to yourself.** `pnpm db:reset` wipes it. Get a slot from the tech lead; no
  other agent may be running API tests against `invai` during the run. (`invai_test` is not touched.)
- Allow about 25 minutes: the seed renders real art and gang sheets through imaging (15–20 min, `runbook.md`
  §4).

## Steps
1. **Shell.** `export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"`; `node --version` →
   v24.
2. **Infra healthy.** `docker ps --format '{{.Names}} {{.Status}}' | grep local-` must show
   `local-postgres-1`, `local-valkey-1`, `local-minio-1`, `local-mailpit-1` as healthy. If Docker hangs:
   `orb stop && orb start`, then `cd invai-infra/local && docker compose up -d`.
3. **Check for stale app processes** (lesson: `tsx watch` restarts and leftover workers break E2E runs):
   ```
   lsof -iTCP:3000-3199 -sTCP:LISTEN -P      # api(s), including agents' 31xx ports
   ps aux | grep -E '[t]sx (watch )?src/(api/server|worker/index)'
   lsof -iTCP:8000 -iTCP:5173 -iTCP:5174 -sTCP:LISTEN -P
   ```
   **Stop only processes you started** (by the PIDs you recorded). Never kill another agent's 31xx API. If a
   process you didn't start holds 3000, 8000, 5173, 5174 or a stale worker, ask the tech lead to have its
   starter stop it, and wait. Never touch port 54322 (another project).
4. **Start the stack.** `cd invai-infra && pnpm dev:all` in its own terminal (infra, migrate, seed-if-missing,
   then api :3000, worker, imaging :8000, web :5173, floor :5174). Record its PID (for a background start,
   `echo $!`), and the PID of anything else you start, so you can stop exactly those later. Wait for:
   ```
   curl -sf localhost:3000/health     # "ok":true, db and redis true
   curl -sf localhost:8000/health     # "ok":true
   curl -sf -o /dev/null -w '%{http_code}\n' localhost:5173   # 200
   curl -sf -o /dev/null -w '%{http_code}\n' localhost:5174   # 200
   ```
5. **Fresh reset, migrate, seed** (imaging must be up):
   ```
   cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed
   ```
   The seed ends by writing `invai-backend/seed-output.json` (logins, PINs, the Press 1 station token). Then
   restart the apps once (Ctrl-C `pnpm dev:all`, start it again, redo the step 4 health checks) so no worker
   holds jobs from before the reset.
6. **API golden path first** (it needs untouched seed orders; about 10 s):
   ```
   cd invai-web && E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts
   ```
7. **Browser golden path and screens smoke** (about 1 min; it tolerates steps already done and checks them
   through the API):
   ```
   cd invai-web && pnpm e2e
   ```
   This runs `golden-path.spec.ts` (13 steps) and `screens.smoke.spec.ts` (27 routes plus detail pages and the
   vendor portal; fails on console errors or failed requests).
8. **Floor tablet suite** (about 3 s: pair, PIN, wrong style and size BLOCKED, right blank PRESS, QC, pack):
   ```
   cd invai-floor && pnpm e2e
   ```
9. **Look at the product,** not only the assertions. Open `invai-web/e2e/.report`
   (`pnpm exec playwright show-report e2e/.report`) and screenshots in `e2e/.results` for failures. Spot-check
   Today, an order drawer, a gang sheet (film use ≥ 80% on full sheets; short end-of-batch sheets can fall
   below, a known cosmetic issue), the label PDF and profit, in English and Spanish. Wrong numbers, broken
   images, `##` order numbers or untranslated strings are failures even when tests pass.
10. **On a failure:** keep the trace (`e2e/.results/**/trace.zip`, open with
    `pnpm exec playwright show-trace <zip>`), the API and worker log lines around it, and the step name. Retry
    once only if the log shows the API restarted mid-request (`tsx watch`). A second failure is real: find the
    layer at fault (`root-cause-bug`) and give it to the owner of that path. If the browser suite fails on a
    step the API suite already did, reseed and run `pnpm e2e` alone before calling it a product bug.
11. **Clean up.** Stop the app processes you started, by their recorded PIDs (Ctrl-C the `dev:all`
    terminal), and nothing else. Leave infra running and
    the dev DB freshly seeded, unless the tech lead asked otherwise.

## Rules
- MUST run on a fresh reset and seed. A result on a used database is not gate evidence.
- MUST run all three suites for a gate or release. A single suite is fine only for a card's own check, and the
  report must say which.
- MUST NOT add retries, sleeps or `.skip` to make a run pass. Flaky tests follow research 12 §3.5 (report as
  flaky, quarantine with an owner and issue, fix within 14 days).
- MUST NOT reset the shared dev DB without the tech lead's slot while other agents run.
- MUST stop only processes you started (record PIDs). Never kill another agent's 31xx API.
- MUST NOT remove or bypass a mock provider. The golden path runs on mocks by design.

## Done when
- API golden path 13/13, browser golden path 13/13, screens smoke all routes, floor suite all green, all on
  one fresh seed, with the last lines of each run in the report.
- Health URLs for api, imaging, web and floor were 200/ok before the run.
- Screens were looked at, and anything wrong is listed with owner and severity.
- Every process you started (recorded PIDs) is stopped, and no one else's was; the dev DB is left freshly
  seeded.
- For a QA gate: `invai-docs/build/qa-report.md` is updated (steps pass/fail, bugs fixed, remaining issues
  ranked).

## References
- `CLAUDE.md` (environment, demo data, definition of done step 3)
- `invai-docs/build/qa-report.md` §4 (the same commands, known issues)
- `invai-web/playwright.config.ts`, `invai-floor/playwright.config.ts`; env overrides `E2E_WEB_URL`,
  `E2E_API_URL`, `E2E_FLOOR_URL`
- `invai-infra/scripts/dev.sh`, `invai-docs/build/runbook.md` §4, §6
- `.claude/agents/qa-engineer.md`; related: `release-checklist`, `root-cause-bug`, `verify-and-report`
