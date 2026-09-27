---
name: verify-and-report
description: Finish any InvAI task by running the definition-of-done checks in every touched repo, exercising the change for real (curl, script or browser with screenshots), and writing an evidence report the reviewer can re-run. Use at the end of every card, fix or audit, or when asked "is it done", "verify" or "report back".
---

# Verify and report

The work is proven by commands anyone can re-run, and the report says honestly what passed, what failed and
what is left.

## When to use
- Last step of every card, before handing to the `reviewer`.
- After fixing review findings (round 2).
- After any audit or drill (the report format is the same).

## Steps
1. **Set up the shell.** `export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"`, then
   `node --version` must print v24.
2. **Run the repo checks** in every repo you touched (`CLAUDE.md` definition of done):
   | Repo | Command |
   |---|---|
   | contracts, ui, backend | `pnpm typecheck && pnpm lint && pnpm test` |
   | web, floor | `pnpm typecheck && pnpm lint && pnpm test && pnpm build` |
   | imaging | `uv run ruff check . && uv run pytest` |
   | infra | `pnpm typecheck && pnpm lint` |
   Backend tests use the `invai_test` database through `src/test/fixtures.ts`; they don't touch the shared dev
   DB. Keep the last lines of each output (test counts, errors).
3. **Exercise it for real.** Compiling is not verification.
   - **API:** start your own API on a free port so you don't fight other agents' `tsx watch`:
     `PORT=31xx pnpm dev:api` in `invai-backend` (pick 3101–3199; check with `lsof -iTCP:31xx -sTCP:LISTEN`).
     Sign in as the right role and call the procedure with curl. Seed logins: `owner@desertbloom.test` /
     `demo1234!` (also `admin@`, `office@`, `designer@`, `presser@`, `packer@`, `receiver@desertbloom.test`,
     `vendor@suncitydtf.test`). Floor PINs 1111–1188; the station token is in
     `invai-backend/seed-output.json`.
   - **Permissions:** call it once as a role that must be refused, and check you get `FORBIDDEN` (or
     `NOT_FOUND` for another tenant's id).
   - **UI:** open the screen in the browser at 1440 px and 390 px (web) or 1280×800 (floor), in English and
     Spanish, take screenshots and **look at them**: numbers, images, order numbers, untranslated keys.
   - **Jobs:** trigger the event, then check the result row in the DB and the worker log; run it twice and
     check there is one effect.
   - **Imaging:** call the endpoint on `:8000` and open the output file.
4. **Golden path.** If the card touches a golden-path area (import, SKU map, proof, sheet build, vendor
   portal, receiving, floor, labels, profit, AI draft, assistant, tenant isolation), run `run-golden-path` or
   ask QA for a slot. Never `pnpm db:reset` the shared dev DB while other agents are running.
5. **Clean up.** Stop every process you started (`lsof -iTCP:31xx -sTCP:LISTEN` → kill the PID), delete temp
   files, and leave the shared dev DB usable.
6. **Check ownership.** `git -C <repo> diff --stat origin/main` lists only your owned paths
   (`respect-ownership`).
7. **Write the report** below, as your final message to the tech lead (the tech lead files it with the card).
   Paste real output, trimmed; never paraphrase a failure into a pass.
8. **Save what you learned.** Before your final reply, add 0–3 entries to your agent memory
   (`.claude/agent-memory/<your role>/MEMORY.md`): a mistake you made and how you fixed it, or a non-obvious
   fact about your area that the next card will need. One line each, starting with the date and card
   (`2026-09-26 T-17-2: ...`). No PII, secrets or customer data. Fix or delete an entry that turned out wrong;
   keep the file under 150 lines. Something every role should know also goes to `log-lesson`.

## Report format
```
# Report: T-<n>-<k> <title>
Author: <role> on <model>

## Built
- <what changed, one line per behavior> (files: <repo>/<path>)

## Acceptance criteria
| # | Met? | Evidence (command or screenshot) |

## Checks I ran
| Repo | Command | Result (last lines) |

## Exercised for real
- <curl/script/browser step> → <observed result>
- Refused case: <role> → <error code>

## Decisions
- <choice and why>; recorded in decisions/NNNN-<slug>.md (if cross-cutting)

## Known gaps and follow-ups
- <gap, risk, owner>

## Blocked by other owners
- <file:line, problem, suggested change, owner role>

## Processes and data
- Stopped: <list>. Shared dev DB: untouched / reseeded at <time>.
```

## Rules
- MUST report failures with the actual output. A red check you couldn't fix goes in "Known gaps", not silence.
- MUST NOT claim "tested" for anything you didn't run in this session.
- MUST NOT fix a failing check by weakening a test or a lint rule. If a test is wrong, say why in the report
  and let the reviewer judge; if a control must weaken, `escalate-to-owner`.
- MUST keep PII out of the report and screenshots (seed data only).
- Retry a request that died because `tsx watch` restarted the API once; if it dies again, it's a real failure
  (`team/lessons.md`).

## Done when
- Every repo check in step 2 passed in every touched repo, with output in the report.
- At least one real exercise per acceptance criterion, plus one refused case for any permissioned procedure.
- The report has every section filled or marked "none".
- No process you started is still running.

## References
- `CLAUDE.md` (definition of done, environment, ports)
- `invai-docs/waves/templates/review.md` (what the reviewer will re-run)
- `invai-docs/build/qa-report.md` §4 (E2E commands), `invai-docs/build/runbook.md`
- Related: `run-golden-path`, `independent-review`, `respect-ownership`
