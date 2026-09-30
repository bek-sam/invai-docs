# Review of T-23-7 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Sonnet
- Verdict: **approve**

Round-2 commits reviewed (unpushed), each diffed against its r1 SHA: contracts `553c6d9..7ee15b6`,
ui `d333016..952c174`, backend `8f509e5..cd5252a`, web `e2cde5a..54b64d7`, floor `f8af015..a902ec3`,
imaging `f61b058..58b67ee`, infra `9fe0c55..490884d` (infra range also has `3215fc6`, which is T-23-6 and not
reviewed here). Inputs: the card, the r1 findings (B1, B2), security r1 (S-40, S-41), the tech lead's
rulings at the bottom of `wave.md`, and the author report `waves/23/reports/T-23-7.md`.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git log --oneline <r1>..<r2>` and `git diff --stat` in all 7 repos | one round-2 commit per repo. contracts, ui, imaging: only `.github/workflows/ci.yml`. backend, web, floor: only `.github/workflows/{ci,e2e}.yml`. infra `490884d`: only `scripts/ci/run-e2e.sh`. **Backend `cd5252a` touches only `.github/`; no product code in any repo** |
| `git show <r1>~1:.github/workflows/ci.yml \| grep -nE 'repository:\|ssh-key'` vs the same on HEAD (6 repos) | before round 1: ui and backend key the contracts checkouts with `CONTRACTS_DEPLOY_KEY`. web and floor key contracts with `CONTRACTS_DEPLOY_KEY` and ui with `UI_DEPLOY_KEY`. contracts and imaging have no sibling checkout. HEAD has the **same key on the same sibling in every repo, and no others**. Before round 1 each sibling had 2 steps (branch attempt plus a `main` fallback). Now it has one keyed step at `ref: main`, which the ruling allows |
| e2e.yml diffs (backend, web, floor) | contracts and ui checkouts reuse the same two existing keys. The other siblings (backend/web/floor/imaging/infra) have no credential, as the ruling says (OI-21). No new `secrets.*` name anywhere |
| `sed -n 1,12p e2e.yml` (3 repos) | `on:` has **only `workflow_dispatch:`**, and `push:` was removed. A comment points at OI-21 |
| per workflow: count of `actions/checkout@` vs `persist-credentials: false` | contracts 1/1, ui 2/2, backend 2/2, web 3/3, floor 3/3, imaging 1/1, the 3 e2e.yml 7/7 each. **30/30** (S-41 closed) |
| Redaction `sed` from `run-e2e.sh:106-109`, run on 200 synthetic copies of the seed's real `console.log` block (`src/db/seed/index.ts:193-195`). Tokens were built exactly like `issueStationToken`: `st1.<uuid>.<randomBytes(32) base64url>`, with all 8 `role=pin` pairs | macOS BSD sed: 0 `st1.` left, 0 `demo1234`, 0 `=NNNN`, 0 PIN values, 200 `[redacted-station-token]`. busybox sed (alpine:3): 0 leaked lines. The regex charset `[A-Za-z0-9_-]` covers the base64url secret and the UUID |
| `grep -rlE 'demo1234\|st1\.[A-Za-z0-9_-]{8}\|[a-z]=1[1-8]{3}'` over every file in the author's run logs (`scratchpad/ci-e2e-r2/*`, `ci-e2e-r3/*`: seed, api, worker, web, floor, imaging, e2e logs) | no file matches. `ci-e2e-r3/seed.log:33-37` shows the redacted block. **S-40 closed** |
| Upload-artifact paths in e2e.yml | `.ci-e2e-logs/**` and the web/floor `e2e/.report`, `e2e/.results`. `seed-output.json` (the cleartext token) is not uploaded |
| `grep -n 'start\|starting' run-e2e.sh` | order: imaging (84) → api (88) → migrate → seed (piped through the redaction) → **worker (118)** → web (121) → floor (134). The worker starts only after migrate and seed have exited 0 (`PIPESTATUS[0]` still reads the seed's own exit code with the 3-stage pipe). **B2 closed** |
| Read `invai-floor/vite.config.ts:8,27-34` and `src/lib/config.ts:1` | confirmed: dev CSP is `connect-src 'self'` (same-origin `/rpc` proxy to `VITE_API_PROXY`), while the client uses an absolute `VITE_API_URL` when it is set. The fix (`unset VITE_API_URL`, `VITE_API_PROXY=http://localhost:$API_PORT` for the floor process only) lives **only in `run-e2e.sh:134-138`**. Floor code is unchanged |
| "market.sweep outbox race" fix | this is only the worker move above (`run-e2e.sh`). No backend change |
| `actionlint` v1.7.12 on all 9 workflows | clean, 9/9 |
| `bash -n invai-infra/scripts/ci/run-e2e.sh` | ok |
| `scan-test-weakening.sh <repo> origin/main` (7 repos) | contracts, imaging: no hits. ui/backend/web/floor: only the removed `continue-on-error: true` in `ci.yml` (a tightening, same as r1). backend untracked `src/test/db-safety*.ts` is T-23-0's work in progress, not this card's. infra: a `gate.sh` line from T-23-6. No test files touched by this card |
| Author's Run 2 logs (`scratchpad/ci-e2e-r3/`) | `api-golden-path.log`: 13 passed. `web-e2e.log`: 31 passed / 3 failed / 1 skipped, and all 3 failures are `digest-dates.spec.ts` (B-207, which matches the wave 22 gate). `floor-e2e.log`: 3 passed |
| `lsof -iTCP:{3000,8000,5173,5174} -sTCP:LISTEN` | all free. I **did not** run `run-e2e.sh` myself. The script's seed writes `invai-backend/seed-output.json` (the shared file the E2E helpers read), so a local run clobbers it (see R1). I judged the run from the author's logs instead, as the brief allowed |
| `ls -la invai-backend/seed-output.json`; dev DB `companies` and `station_tokens` lookup | see R1: the shared file was overwritten at 20:03 by the author's proof run |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `push` and `workflow_dispatch` are unchanged in all 6 `ci.yml`. The sibling checkouts carry the same deploy keys that were green before round 1 (the r1 `gh run view` evidence: keyed checkouts succeeded). `VITE_API_URL` is set for the web/floor build (r1 build proof). imaging runs ruff and pytest |
| 2 | Yes, as ruled | The job shape is unchanged from r1 and correct. Triggers are `workflow_dispatch` only until OI-21, per the tech lead's ruling. Start order is fixed (worker after seed). Author Run 2: API 13/13, browser 31 pass with only B-207's 3 failures, floor 3/3 (logs read). Nothing was excluded or skipped |
| 3 | Yes | SHA pins are unchanged from r1 (verified upstream in r1). Top-level `contents: read`. The only secrets are the two existing read-only deploy keys, restored under the AC3 ruling ("no new secrets, none in run steps"). No `pull_request_target`, no deploy or `aws` steps. `persist-credentials: false` on all 30 checkouts |
| 4 | Yes | actionlint is clean (re-ran). There are two local proof runs on fresh scratch DBs. The report says the first real CI run is observed after the tech lead's push |

## Blocking findings
None. B1, B2, S-40 and S-41 are closed (evidence above).

## Operational finding for the tech lead (not a code defect, needs action now)
- **R1: the author's local proof overwrote the shared `invai-backend/seed-output.json`.** It was written at
  2026-09-29 20:03 CDT, the same minute as `ci-e2e-r3/seed.log`. It now holds shopId `095267a9…`, which
  doesn't exist in the dev DB (Desert Bloom there is `dd412bf7…`, created 19:02 CDT). Its station token
  matches 0 rows in dev `station_tokens` (I checked both hash forms). The report says "Shared dev DB …
  untouched", but the DB is untouched and this file is not. Impact: until the next gate reseed, the floor
  E2E (`invai-floor/e2e/helpers/api.ts:32`), the web API helpers (`invai-web/e2e/helpers/api.ts:103`) and
  any agent using the station token against the dev stack will fail auth. Fix: reseed at the gate, or
  issue a new token and rewrite the file. Follow-up for platform-sre: when not in CI,
  `run-e2e.sh` should set `SEED_OUTPUT_FILE` or refuse to run. The E2E helpers read the fixed path, so
  proof runs belong in a separate workspace copy.

## Checks
- [x] Only owned paths changed (`git diff --stat`): `.github/workflows/**` in 6 repos and `invai-infra/scripts/ci/run-e2e.sh`. No product code.
- [x] Nothing outside scope: the floor `VITE_API_URL`/proxy fix stays in the script (owned). The B-208 sheet race was filed, not "fixed" in product code.
- [x] Tests exercise the behavior, and none were weakened: no test files touched, no spec exclusions, and the script still exits non-zero on B-207.
- [x] Tenancy, idempotency, money, en/es: n/a (CI config and a shell script). The uploaded artifacts now have the seed secrets redacted.
- [x] Decisions recorded where needed: the tech lead's rulings (AC3 keys, dispatch-only until OI-21) are in `wave.md`. OI-21 is open.

## Optional notes (not blocking)
- N1 `e2e.yml:181` (backend, web, floor): the comment still says "imaging, api, worker, migrates, seeds". The order is now api → migrate → seed → worker. Fix the comment when next in the file.
- N2 The PIN rule `s/([a-z0-9]+)=[0-9]{4}/…/` also hides any 4-digit `key=value` in the seed's log lines. That over-redaction is harmless.
- N3 Playwright traces in the artifact can carry the CI seed's station token in request headers. It is a throwaway DB in CI with a 7-day retention. It's security's call whether that needs anything.
- N4 Floor dev mode with `VITE_API_URL` set is broken by its own CSP (a latent floor dev-experience issue). Worth a backlog line for the floor owner. The script workaround is right for this card.
- N5 B-208 (0.7951 sheet utilization after the post-seed drain) is a real gate flake risk now that the worker drains the backlog while the suites run. It's tracked, and E2E stays manual until OI-21.

## Processes and data
- Started: none. No servers, no DB/Redis/S3 writes. One `alpine:3` container ran the sed test and was removed (`--rm`), plus scratchpad files. Read-only `psql` selects on the dev DB. Shared dev DB untouched by me. R1 above is pre-existing.
