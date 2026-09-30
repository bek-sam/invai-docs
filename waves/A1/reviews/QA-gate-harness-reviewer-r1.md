# Review of QA gate-harness fix (A1 integration gate, round 1)

- Reviewer: reviewer on Sonnet 5
- Author: qa-engineer
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show 369705f` | Only `playwright.config.ts` changed; 7 insertions, 2 deletions |
| `git -C invai-floor show 72a842d` | Only `playwright.config.ts` changed; 7 insertions, 2 deletions |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web 369705f~1` | no hits (exit 0) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor 72a842d~1` | no hits (exit 0) |
| `git -C invai-web status --short` / `invai-floor status --short` | clean, nothing stray |
| `invai-web: pnpm typecheck` | pass, exit 0 |
| `invai-web: pnpm lint` | pass, exit 0; 1 pre-existing warning in an unrelated markdown-parser test file (not touched by this diff, not new) |
| `invai-floor: pnpm typecheck && pnpm lint` | both pass, no warnings |
| `invai-web: npx playwright test --list` | 35 tests in 5 files, config parses cleanly |
| `ls /Users/bekbolsun/invai/.e2e-out` | `.e2e-out/invai-web` exists at the workspace root, which is not a git repo (`invai/` itself is not `.git`-tracked) and sits outside both `invai-web/` and `invai-floor/` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| Output dirs outside `src` and outside anything Vite watches | Yes | Both configs now resolve to `../.e2e-out/<repo>/{results,report}`, i.e. `<workspace root>/.e2e-out/...` — one level above the repo root, outside the tree each repo's Vite dev server watches (no `vite.config.ts` was touched or needed to be; the fix is stronger than adding `watch.ignored` since the files never land inside the watched tree at all) |
| Still gitignored or outside the repo | Yes | Outside the repo entirely (outside any of the 8 separate git repos, since `invai/` is not itself a repo). The old `e2e/.report/`/`e2e/.results/` gitignore lines are now dead but harmless (already flagged by QA's own report as a non-blocking cleanup item for the repo owners) |
| No test/retry/timeout/skip weakened | Yes | Diff shows only the `reporter.outputFolder` and `outputDir` lines changed; `retries: 0`, `workers: 1`, `expect.timeout`, `fullyParallel` all untouched in both files. Scan script: no hits in either repo |
| Only the granted file changed | Yes | `git diff --stat` for both commits: exactly one file, `playwright.config.ts`, in each repo. The grant also named `.gitignore` as optionally in scope; it wasn't touched, which is fine since the new path sits outside the repo and needs no ignore entry |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots)
- [x] Tenancy / idempotency / money / en-es — not applicable, config-only change to a test harness, no product code touched
- [x] Decisions recorded where needed — not applicable, a harness fix under an explicit tech-lead grant, not a cross-cutting decision

## Optional notes (not blocking)
- The dead gitignore lines (`invai-web/.gitignore:11-12`, `invai-floor/.gitignore:10-11`) and the stale path references QA already listed (CI workflow upload globs, `run-e2e.sh` log message, `run-golden-path` SKILL.md) are real but out of this grant's scope; route them to their owners as QA's report already recommends.
