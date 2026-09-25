# Review of T-2-6 (round 1) — invai-infra `148df7d`

- Reviewer: platform-sre + security-reviewer on Claude Sonnet 5
- Author: qa-engineer on Fable (flagged in the commit message for platform-sre review, since
  `invai-infra` is not qa-engineer's owned repo)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-infra show --stat 148df7d` | `scripts/dev.sh \| 6 ++++++`, 1 file changed — only touches the one script |
| `git -C invai-infra show 148df7d` (full diff, read) | adds `export MOCK_CARRIER_TRANSIT_HOURS="${MOCK_CARRIER_TRANSIT_HOURS:-0.001}"` before the `concurrently` block that starts api/worker/imaging/web/floor |
| `grep -n "dev.sh" invai-infra/package.json` | only reference is `"dev:all": "bash scripts/dev.sh"` — a local, developer-invoked script |
| `grep -n "MOCK_CARRIER\|dev.sh" invai-infra/sst.config.ts` | no hits — `sst.config.ts` (the deploy definition) never sources or execs `dev.sh`, and sets its own `environment` blocks for the deployed API/worker containers independently |
| `cat invai-infra/.github/workflows/deploy.yml` | the only CI deploy path; checks out sibling repos, runs `pnpm install`, then `pnpm exec sst deploy --stage …`. Never invokes `scripts/dev.sh` or references `MOCK_CARRIER_TRANSIT_HOURS`. |
| `find invai-infra -iname "Dockerfile*" \| grep -v node_modules` | only match is under `.sst/platform/dist/dockerfiles` (SST's own generated tooling, not a project Dockerfile that sources `dev.sh`) |
| `grep -n "MOCK_CARRIER_TRANSIT_HOURS" -r invai-backend/src \| grep -v test` | `src/modules/shipping/service.ts:76`: `export const MOCK_TRANSIT_HOURS = Number(process.env.MOCK_CARRIER_TRANSIT_HOURS ?? 2);` |
| `grep -n "MOCK_TRANSIT_HOURS" -r invai-backend/src` | consumed once, `src/modules/shipping/jobs.ts:114`: `{ delay: MOCK_TRANSIT_HOURS * 3600_000 }` (BullMQ job delay in ms) |
| `node -e "console.log(0.001 * 3600_000)"` | `3600` exactly — no floating-point drift; `0.001h` → a 3.6s delay |

## What it does and where it can reach
`scripts/dev.sh` exports `MOCK_CARRIER_TRANSIT_HOURS="${MOCK_CARRIER_TRANSIT_HOURS:-0.001}"` only into
the shell environment of the `concurrently`-spawned local processes it starts (api, worker, imaging,
web, floor), and only when invoked directly (`./scripts/dev.sh`) or via `pnpm dev:all`. It is:
- **Not sourced or referenced by `sst.config.ts`** — the deploy stack defines its own `environment: {…}`
  blocks per component and has no dependency on this script or its exports.
- **Not referenced by any Dockerfile** in the repo (the only `Dockerfile*` matches are SST's own
  vendored build tooling under `.sst/`, unrelated).
- **Not referenced by `.github/workflows/deploy.yml`**, the only CI/deploy workflow in this repo — it
  builds and deploys via `sst deploy` directly, with no shell step that touches `dev.sh` or this var.

So a real deploy (staging or production, via the `Deploy` workflow) cannot pick this default up through
any code path in this diff. There is no route from this line to a shipped/production carrier-timing
behavior.

## Overridable?
Yes — `"${MOCK_CARRIER_TRANSIT_HOURS:-0.001}"` is bash parameter expansion with a default: if the
variable is already set in the invoking shell's environment, that value passes through unchanged; the
literal `0.001` is used only when it's unset. An agent or developer needing the real 2h default (or any
other value) for a specific local run can still do `MOCK_CARRIER_TRANSIT_HOURS=2 pnpm dev:all` (or export
it beforehand) and this line will not clobber it.

## Backend parsing: does 0.001h work, int or float?
`Number(process.env.MOCK_CARRIER_TRANSIT_HOURS ?? 2)` — `Number()`, not `parseInt`, so it parses the
full decimal value, not just an integer prefix. `MOCK_TRANSIT_HOURS` (0.001) is then multiplied by
`3600_000` in `shipping/jobs.ts:114` to get the BullMQ delay in milliseconds: `0.001 * 3_600_000 = 3600`
exactly (verified above — no floating-point rounding surprises at this particular value), i.e. a 3.6s
delay before the mock carrier's scan fires. That's comfortably inside the e2e `poll()` helper's default
60s timeout (`invai-web/e2e/helpers/api.ts:123`, unaffected by this commit) with wide margin, and non-zero
per the qa report's stated reasoning (avoiding a same-tick race with the browser suite's own network
round-trips). If the env var were instead parsed with `parseInt(process.env.MOCK_CARRIER_TRANSIT_HOURS ?? "2", 10)`,
`0.001` would truncate to `0` and produce a same-tick fire; that is not what's implemented, so this
concern doesn't apply here, but it's worth this repo's backend owner keeping `Number()` (not `parseInt`)
if that line is ever touched again.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| Dev-only, no production reach | Yes | No reference in `sst.config.ts`, no Dockerfile, no CI deploy workflow step; only reachable via `pnpm dev:all` / direct script invocation |
| Overridable | Yes | `${VAR:-default}` bash idiom preserves any pre-set value |
| Backend parses 0.001h correctly, and as a float | Yes | `Number()` parses the decimal; delay computation is exact at this value (`3600`ms) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`scripts/dev.sh` only, 6 lines added)
- [x] Nothing outside scope
- [x] N/A — no tests touched in this repo by this diff
- [x] Not a tenant table / no idempotency surface; env-var default only, correctly comment-explained and dev-scoped
- [x] Decisions: none needed — this is a dev-ergonomics default, not a product/architecture decision; commit message correctly flags it for platform-sre sign-off since `invai-infra` isn't the author's owned repo

## Optional notes (not blocking)
- Consider adding a one-line comment in `sst.config.ts` (or the runbook) near where the real
  `MOCK_CARRIER_TRANSIT_HOURS` / carrier config would eventually live, noting that `dev.sh`'s default is
  local-only and deploy must set its own value (or omit it to keep the backend's real 2h default) — purely
  documentation, not a code change, and not required for this to be safe today.
- `invai-docs/build/runbook.md` env-var reference (if it lists `MOCK_CARRIER_TRANSIT_HOURS`) could note
  the new local default for discoverability; not required to approve.

## Verdict rationale
The change is narrowly scoped to a local dev script, has no code path into `sst.config.ts`, any
Dockerfile, or the CI deploy workflow, remains overridable, and the backend parses the fractional-hour
value correctly (float via `Number()`, not truncated by `parseInt`) with an exact, verified millisecond
delay. No security or platform-reach concerns. Approved.
