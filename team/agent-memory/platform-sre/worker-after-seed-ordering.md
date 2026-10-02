---
name: worker-after-seed-ordering
description: start the worker only after migrate+seed finish in any E2E/CI stack script — starting it earlier races market.sweep's "already done" check
metadata:
  type: feedback
---

Rule: in `invai-infra/scripts/ci/run-e2e.sh` (and any similar from-scratch stack start-up script),
start order must be imaging -> api -> migrate -> seed -> **worker** -> web -> floor. The worker must
never run concurrently with, or be started before, `db:seed`.

**Why:** T-23-7 review round 1 (B2): starting the worker before migrate+seed let it consume outbox
events mid-seed. `marketSweep()` (`invai-backend/src/modules/market/jobs.ts`) checks whether a shop's
`marketSignals` already has a row for today before enqueuing `refreshDemand`; if the worker's
outbox-triggered `computeSignals` ran during seeding (because the worker was already live), that row
exists by the time the sweep logic runs, so `refreshDemand` never gets enqueued — no "Sample data"
badge, `market.spec.ts` red on every run (documented cause, `qa-report.md:487`). Fixed by starting the
worker only after seed finishes, matching `run-golden-path` step 5's own restart-after-reset rule.
Confirmed fix: `market.spec.ts` went from 1 failing to 5/5 across two fresh local runs after this
change.

**How to apply:** Any new stack-bootstrap script (CI, local proof, a future `dev.sh` rewrite) that
seeds a fresh database must start its background job worker(s) after the seed step completes, never
before or concurrently. See also [[sheet-build-worker-race]] — this doesn't eliminate every
worker-vs-seed timing race, just the specific `market.sweep` one.
