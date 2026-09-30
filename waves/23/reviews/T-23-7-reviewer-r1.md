# Review of T-23-7 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Sonnet
- Verdict: **changes-required**

Commits reviewed (unpushed): contracts `553c6d9`, ui `d333016`, backend `8f509e5`, web `e2cde5a`,
floor `f8af015`, imaging `f61b058`, infra `9fe0c55`. No written author report was filed in
`waves/23/reports/`; I judged the card, the diffs, the tech lead's summary in `wave.md` and the author's
own local-run logs (`ci-e2e-logs/`, `run-e2e-stdout.log` in the session scratchpad, 19:31-19:36 CDT).
I did not run `run-e2e.sh` (it takes the default ports; tech lead's instruction); it was reviewed by reading
and through those logs.

## Evidence I re-ran
| Command | Result |
|---|---|
| `gh run list -R bek-sam/invai-<repo> --limit 5` (7 repos) | ui: last 4 pushes **success**; contracts, imaging: success; backend: failure at `pnpm test`; web, floor: failure at `pnpm build` (VITE_API_URL missing) |
| `gh run view <id> --json jobs` for backend 36649568130, web 36601725422, floor 36292917235, ui 36251508016 | In every run the sibling checkout **with `ssh-key: secrets.*_DEPLOY_KEY` succeeded** (`Run actions/checkout@v4 success`, fallback `skipped`). Failures are later (test/build), never the checkout |
| `gh secret list -R bek-sam/invai-{backend,web,floor,ui}` | `CONTRACTS_DEPLOY_KEY` in all four; `UI_DEPLOY_KEY` in web and floor (set 2026-09-24) |
| `gh api repos/<action>/commits/<tag> --jq .sha` + tag lookup, 5 actions | checkout `11d5960…` = v4 / v4.4.0; pnpm/action-setup `b906aff…` = v4 / v4.3.0; setup-node `49933ea…` = v4 / v4.4.0; setup-uv `d0cc045…` = v6 / v6.8.0; upload-artifact `ea165f8…` = v4 / v4.6.2. All pins match their comments |
| `actionlint` v1.7.12 (downloaded to scratchpad), 9 workflows | clean on all 9 (6 `ci.yml`, 3 `e2e.yml`) |
| `grep uses: … \| grep -v @<40-hex>` on the 9 changed workflows | no unpinned `uses:` (only `invai-infra/.github/workflows/deploy.yml`, read-only and out of scope, is unpinned) |
| `grep -E 'secrets\.\|pull_request_target\|deploy\|: write\|write-all\|a​ws\|s​st '` on the 9 workflows | no hits |
| `diff` backend/web/floor `e2e.yml` | identical except the self/sibling checkout swap, `package_json_file`, `.nvmrc` and a comment |
| `vite build` floor with `VITE_API_URL` unset → set (outDir in scratchpad) | unset: throws in `requireApiOrigin`; set: builds (`sw.js` generated) |
| `vite build` web with `VITE_API_URL=http://localhost:3000` (outDir in scratchpad) | rc=0, `built in 1.74s` |
| `bash -n invai-infra/scripts/ci/run-e2e.sh` | ok |
| `invai-infra`: `pnpm typecheck && pnpm lint` | `tsc --noEmit` clean; `biome check .` 4 files, no fixes |
| `scan-test-weakening.sh <repo> origin/main` (7 repos) | only hit: "CI config loosened" in ui/backend/web/floor `ci.yml`, which is the **removal** of `continue-on-error: true` (a tightening). No test files touched |
| `git diff --stat origin/main` in each repo | only `.github/workflows/{ci,e2e}.yml` and `invai-infra/scripts/ci/run-e2e.sh` from this card (other infra/web commits belong to T-23-6, T-24-1) |
| Author's `ci-e2e-logs/web-e2e.log` | `9 failed / 1 skipped / 21 passed (3.9m)`: digest-dates 5, digest 3, market.spec.ts:91 1 |
| Author's `ci-e2e-logs/migrate.log` | `[migrate] up to date (invai_ci_local)`: the proof DB was already migrated |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | **No** | `workflow_dispatch` added; lint/typecheck/test steps unchanged; `VITE_API_URL` set in web/floor (build proven above). But in ui/backend/web/floor the sibling checkouts no longer carry a credential, so every run fails at checkout and never reaches lint/typecheck/tests (B1). |
| 2 | **No** | Workflows and script have the right shape (siblings at `main`, Postgres+pgvector, Valkey, MinIO, imaging, migrate, seed, api/worker/web/floor, three suites, upload on failure). But the script's start-up order produces a stack on which 6 tests beyond the known digest-dates issue fail, so the job is red on every run (B2). |
| 3 | Yes | SHA pins verified against upstream tags (5 actions); top-level `permissions: contents: read` in all 9 workflows, no job-level `permissions`; no `secrets.`, no `pull_request_target`, no deploy/cloud steps. Container images pinned by digest too. |
| 4 | Partly | actionlint clean (re-ran). The local proof ran, but on an already-migrated DB, with the machine's Mailpit reachable on :1025, and with 9 red tests, so it does not prove the CI path (B2, note N2). |

## Blocking findings
1. **`invai-ui/.github/workflows/ci.yml:26`, `invai-backend/.github/workflows/ci.yml:68`,
   `invai-web/.github/workflows/ci.yml:28,34`, `invai-floor/.github/workflows/ci.yml:28,34`: removing the
   working `ssh-key: ${{ secrets.CONTRACTS_DEPLOY_KEY }}` / `UI_DEPLOY_KEY` is a regression and a scope
   change, not consistency.** Evidence: the secrets exist (`gh secret list`), and in every recent run of
   ui, backend, web and floor the keyed sibling checkout succeeded; ui CI is green on its last 4 pushes. The
   default `GITHUB_TOKEN` is scoped to the running repo, so `actions/checkout` of `bek-sam/invai-contracts`
   with no key fails. Failure scenario: the tech lead pushes this card; invai-ui's CI, green today, goes red
   at "Check out invai-contracts" on this and every later push, and backend/web/floor stop reaching lint,
   typecheck and tests at all, so CI checks nothing until the owner acts. AC3's "no secrets" reads as "add
   no new secrets / no deploy secrets"; it does not ask to remove existing read-only deploy keys that CI
   depends on. Fix: keep `ref: main` if you like, but restore `ssh-key: ${{ secrets.CONTRACTS_DEPLOY_KEY }}`
   / `${{ secrets.UI_DEPLOY_KEY }}` on those checkouts (and use them in the three `e2e.yml` for contracts
   and ui). If you believe AC3 really means removing them, that is a control/scope question for the tech
   lead before pushing, not a unilateral change. The remaining e2e sibling checkouts (backend, web, floor,
   imaging, infra) still need an owner-provided read credential: raise that as an OI, as the wave log says.

2. **`invai-infra/scripts/ci/run-e2e.sh:84-105`: the stack order makes the E2E job red on every run, and
   the "9 pre-existing failures" claim is contradicted by the wave 22 gate.** The gate on a fresh seed
   (`waves/22/reviews/gate.md`) had only `digest-dates.spec.ts` failing (3), with `market.spec.ts` 5/5 and
   `digest.spec.ts` 10/10. The author's run of this script has 9: digest-dates **5**, digest **3**, and
   `market.spec.ts:91`. The script starts the worker before migrate and seed and never restarts it, while
   `run-golden-path` step 5 requires restarting the apps after the seed "so no worker holds jobs from before
   the reset". The `market.spec.ts:91` failure matches a documented cause exactly (`build/qa-report.md:487`:
   "on a fresh seed with a worker running, `market.sweep` treats the day as done after the
   outbox-triggered `computeSignals` and never enqueues `refreshDemand` … `market.spec.ts:91` red"; see
   `marketSweep` in `invai-backend/src/modules/market/jobs.ts:543-566`). Failure scenario: after the push,
   the E2E workflow in backend, web and floor fails on every push with ~9 known-red tests. A real golden-path
   regression then looks the same as the noise, and people learn to ignore the red E2E check, which defeats
   B-22. Fix, inside owned paths: follow the gate procedure (migrate and seed first with imaging up, then
   start or restart api/worker, plus any market/digest step the gate uses), and show a local run where only
   failures proven pre-existing on the same procedure remain, each named with its gate or backlog id. If
   something stays red that can't be fixed in `scripts/ci/**`, take it to the tech lead; don't exclude specs
   yourself (that weakens a test).

## Checks
- [x] Only owned paths changed (`git diff --stat`): `.github/workflows/{ci,e2e}.yml` in 6 repos and `invai-infra/scripts/ci/run-e2e.sh`. `deploy.yml` untouched.
- [ ] Nothing outside scope: removing the deploy-key checkouts (B1) goes beyond the card and breaks working CI.
- [x] Tests exercise the behavior, and none were weakened: no test files touched; the only scan hit is a removed `continue-on-error` (tightening). The suites are run in full, nothing excluded.
- [x] Tenancy, idempotency, money, en/es: n/a (CI config and a shell script only). Upload-on-failure paths are logs, Playwright reports and traces of a throwaway seeded CI DB (seed data only, dummy CI secrets that are already in the file); `.git` (with the checkout token) is not in the upload paths.
- [x] Decisions recorded where needed: none required, but B1's reading of AC3 needs a tech-lead ruling if the author keeps it.

## Optional notes (not blocking)
- N1 `run-e2e.sh:34-45` trap: kills only its own recorded PIDs (good; `exec` in the subshell makes `$!` the real process, and the pnpm shims `exec node`). `tsx` still forks a child node, and the SIGKILL 1 s after SIGTERM can orphan it on a slow shutdown when run locally. Harmless on a GitHub runner. Consider waiting on the PIDs before the KILL pass.
- N2 The local proof started against a DB that was already migrated (`migrate.log`: "up to date") and with the machine's Mailpit on :1025. In CI the DB is empty when api/worker start, and there is no Mailpit, so the seed's vendor sheet email (`gate.md`: "sent once during the seed's own vendor send") hits a refused SMTP connection. The `e2e.yml:14-17` comment says nothing on the golden path needs mail; consider a digest-pinned Mailpit service or a proof run without :1025 to back that claim.
- N3 `run-e2e.sh:24` prepends `$HOME/.local/share/pnpm` to PATH; harmless on a runner (dir absent), fine to keep for local runs.
- N4 The three `e2e.yml` run the full stack on every push to each of three repos; a cross-repo wave push runs it 3 times. Acceptable for now; a `concurrency:` group would save minutes.
- N5 Ports are parameterized (`API_PORT`, `IMAGING_PORT`, `WEB_PORT`, `FLOOR_PORT`, `E2E_*_URL`); `VITE_API_URL`, DB and Redis URLs come from the caller's env, as the header says. No hard-coded machine paths.

## Processes and data
- Started: only `vite build` runs into scratchpad out-dirs (removed) and a scratchpad copy of actionlint. No servers, no DB or Redis writes. Shared dev DB untouched.
