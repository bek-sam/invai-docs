---
name: sheet-build-worker-race
description: gang-sheet utilization on a fresh-seed golden-path run is non-deterministic — races the worker's post-seed outbox backlog drain, not a code bug in CI scripts
metadata:
  type: project
---

On a fresh seed + immediate golden-path run, `api-golden-path.spec.ts` step 5 (and its
`golden-path.spec.ts` browser twin) asserts every "full" (>=100in) gang sheet nests at >= 80%
utilization. This is flaky by a real timing race, not deterministic seed randomness (seed has no
`Math.random`/`faker` calls at all — checked `grep -rn "Math.random" invai-backend/src/db/seed/`).

**Why:** The test calls `production.batches.build` manually, pulling from the company's backlog of
"ready, due soon" items. Right after a fresh seed, the worker is draining a large backlog of outbox
events (~5,000+) released by the seed itself; that drain races the test's own build call for the same
item pool. Which items land on the test's sheet — and therefore its nesting efficiency — varies by real
wall-clock timing between two runs of *identical* seed data: observed 0.7951 (fail) on one
`run-e2e.sh` run and 0.8603/0.8942 (pass) on the next, same code, same seed. Confirmed by rerunning the
whole script twice against fresh databases.

**How to apply:** Don't chase this as a CI-script ordering bug (starting the worker later doesn't
remove the race, it only changes its shape — see B2 in T-23-7 round 2, which fixed a *different*
worker-timing race in `market.sweep` by delaying the worker start, and this one showed up anyway on one
of two runs afterward). If it recurs, it's a `production.batches` vs. outbox-relay/worker race — flag
to backend-engineer (production module) or qa-engineer, not something `invai-infra/scripts/ci/**` can
fix without either padding every CI run with an artificial wait or the product code itself waiting for
the backlog to settle before letting a manual build claim items.
