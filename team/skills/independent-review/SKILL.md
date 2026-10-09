---
name: independent-review
description: Review one finished InvAI task card with fresh context, read-only on code — re-run the checks, verify each acceptance criterion, scan for weakened tests, check owned paths and scope, block only on real issues, and write the verdict with evidence to invai-docs/waves/<n>/reviews/. Use for every card before push, for risk-flag co-reviews, and for "review", "approve" or "check this diff".
---

# Independent review

Nothing reaches `main` unless a different agent re-ran the evidence and found no blocking issue, and the
verdict file proves it.

## When to use
- Every card, as soon as its author hands over the report (wave step 5).
- As a co-reviewer only for real risk (`operating-system.md`, "Who reviews whom", decision 0019): contract
  changes, migrations, security flags, prompts, new screens or components. The primary reviewer also covers UI,
  consumer impact and golden-path risk for everything else.
- Round 2, after the author fixed round-1 findings.

## Inputs (and only these)
- The task card `invai-docs/waves/<n>/T-<n>-<k>-<slug>.md` and the spec it links.
- The diff in each touched repo.
- The author's report (`verify-and-report` format).
Never the author's chat, reasoning or plan. If you were spawned with the author's context, stop and ask the
tech lead for a fresh reviewer. For high-risk flags (tenancy, pii, auth, payments, webhooks, files) use a
different model from the author's (card "Model"; Fable ↔ Opus).

## Steps
1. **Set up.** `export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"`. Copy the template:
   `invai-docs/waves/templates/review.md` → `invai-docs/waves/<n>/reviews/T-<n>-<k>-<role>-r<round>.md`, where
   `<role>` is your role (`reviewer`, `security-reviewer`, …). Every reviewing role, primary or co-reviewer,
   writes its own file. This file is the only thing you write.
2. **Read the card cold.** Owned paths, read-only paths, acceptance criteria, verification commands, out of
   scope, risk flags. Restate each criterion as an observable result before looking at the code.
3. **Get the diff** in each repo the card names:
   ```
   git -C <repo> log --oneline origin/main..HEAD
   git -C <repo> diff --stat origin/main
   git -C <repo> diff origin/main -- <paths>
   git -C <repo> status --short            # uncommitted or untracked work counts too
   ```
   If other cards' commits share the repo, review only this card's commits and files; ask the tech lead for
   the commit list when unclear.
4. **Ownership and scope.** Every path in `--stat` must match the card's owned globs. Every change must serve
   an acceptance criterion; anything else is scope creep. Both block.
5. **Re-run the checks yourself.** Don't trust the report's output.
   - Each touched repo: `pnpm typecheck && pnpm lint`, plus the test files the diff adds or changes and the
     tests of every module it touches (`pnpm vitest run --reporter=dot <paths>`); backend always adds
     `src/db/rls-coverage.test.ts src/api/authz.test.ts`. Web/floor also `pnpm build`; imaging
     `uv run ruff check . && uv run pytest <touched tests>`; infra `pnpm typecheck && pnpm lint`.
   - The card's own verification commands.
   - A round 2 or test-only diff gets the same `pnpm typecheck && pnpm lint`: vitest does not typecheck
     (lesson 2026-10-09 wave 29).
   - For a guard, filter, skip rule or delete predicate: mutate it once in a scratch worktree (always on,
     always off, filter removed) and confirm a test goes red; a suite that stays green blocks (lessons
     2026-10-09 waves 28–29).
   - The full suites and E2E run once per wave at the integration gate (`run-golden-path`, decision 0019),
     not in each review. Run the full suite yourself only when the diff touches shared code (`src/lib`,
     `src/db`, `src/api`, the worker) or the card's report shows a full-suite failure.
   Record every command and its last lines in "Evidence I re-ran".
6. **Exercise the behavior.** Start your own API (`PORT=31xx pnpm dev:api`, a free port in 3101–3199), sign in
   as the card's role (seed logins in `CLAUDE.md`), and hit each acceptance criterion with curl or the
   browser. Always try one refused case: a role without the permission (`FORBIDDEN`) and another tenant's id
   (`NOT_FOUND`, never `FORBIDDEN`). For jobs and webhooks, send the same input twice and check one effect.
   Stop what you started.
7. **Scan for weakened tests** in each repo (run from the workspace root):
   ```
   .claude/skills/independent-review/scan-test-weakening.sh <repo> origin/main
   ```
   Read every hit. A hit is blocking when it removes or loosens a check of behavior the card touches without
   an equal or stronger check elsewhere: `.skip`/`.only`/`fixme`, a leftover `it.fails`/`test.fail` acceptance
   marker, a deleted or loosened assertion, `vi.mock` of the unit under test, a test-only branch in production
   code, a rewritten snapshot or screenshot, a relaxed config (`exclude`, `retries`, `continue-on-error`).
8. **Do the new tests fail without the change?** For any new or changed test that is the main proof of a
   criterion, run it against the base code, outside the repo:
   ```
   R=/tmp/review-T-<n>-<k>; mkdir -p $R
   git -C <repo> archive origin/main | tar -x -C $R
   ln -s "$PWD/<repo>/node_modules" $R/node_modules; cp <repo>/.env $R/ 2>/dev/null
   cp <repo>/<test file> $R/<same path>
   (cd $R && ./node_modules/.bin/vitest run <test file>)    # must FAIL
   rm -rf $R
   ```
   This works for the Vitest repos; for pytest or Playwright tests, ask QA to run the equivalent. A test
   that passes on the old code proves nothing: blocking if it is the only evidence for a criterion.
9. **Walk the checklist** in the template, using `invai-docs/research/12-security-quality-playbook.md` §4 for
   detail:
   - tenancy: `withTenant` on request paths, any new `withSystem` has a reason comment
     (`grep -n "withSystem(" <diff files>`), new tables have `company_id` + RLS + a `company_id`-leading
     index, `pnpm test src/db/rls-coverage.test.ts src/api/authz.test.ts` green;
   - idempotency: webhooks, payments, label buys, tracking pushes and scans use keys; jobs are safe to replay
     (run-twice test);
   - money in integer cents, sizes in unrounded inches, en and es strings, no PII in logs, prompts or
     analytics, Zod on every external input;
   - InvAI invariants: a floor mismatch still blocks; one order item = one unit; pack semantics
     (`decisions/0002`); stock push opt-in (`0003`); the mock provider still works; contract changes are
     additive.
10. **Decide.** Blocking findings are only: correctness, an unmet acceptance criterion, security, tenancy,
    idempotency, ownership, scope, or a weakened test. Everything else is an optional note. Each blocking
    finding: `file:line — what is wrong, and a concrete failure scenario` ("a presser at shop B scans shop A's
    transfer id and gets PRESS instead of BLOCKED").
    - `approve`: no blocking findings, evidence complete.
    - `changes-required`: at least one blocking finding (round 1, or round 2 with new findings only).
    - `escalate`: round 2 still has blocking findings, a disagreement on scope or risk, or a fix would weaken
      a control or test. The tech lead takes it; the owner gets it through `escalate-to-owner` when it's scope
      or risk.
11. **Write the verdict file** (every template section; "none" where empty), then report the path and verdict
    to the tech lead. Commit only that file (`git -C invai-docs add waves/<n>/reviews/<file>`), never anything
    else; the tech lead pushes. A card may be pushed only when every required reviewer's latest file says
    `approve`.
12. **Save what you learned.** Add 0–3 one-line entries to `.claude/agent-memory/<your role>/MEMORY.md`:
    a defect pattern you caught that the next review should look for, or a check that proved useful. Start each
    with the date and card. No PII or secrets. Keep the file under 150 lines.

## Rules
- MUST NOT edit code, tests, fixtures, configs or docs outside `invai-docs/waves/*/reviews/`. Findings go in
  the review; the owner fixes (`team/lessons.md`, 2026-09-24).
- MUST list every command you re-ran with its result. A verdict without evidence is not a review.
- MUST NOT approve on the author's word. Unverified criterion = not met.
- MUST NOT block on style, naming or taste. Put them under "Optional notes".
- MUST NOT go past 2 rounds. Round 3 is always `escalate`.
- MUST leave the shared dev DB usable and stop every process you started.

## Done when
- `invai-docs/waves/<n>/reviews/T-<n>-<k>-<role>-r<round>.md` exists with reviewer and author roles and models, a
  verdict, the evidence table, every acceptance criterion marked with evidence, every checklist box ticked or
  explained, and blocking findings with `file:line` and a failure scenario.
- The scan script ran in every touched repo and its hits are addressed in the file.
- The tech lead has the path and the verdict.

## References
- `invai-docs/waves/templates/review.md` (the verdict format)
- `scan-test-weakening.sh` (this folder): read-only diff scan, exit 1 = hits to read
- `invai-docs/team/operating-system.md` ("Who reviews whom", review rules)
- `invai-docs/research/12-security-quality-playbook.md` §4 (full checklist), §3.5 (flaky-test policy)
- `.claude/agents/reviewer.md`; related: `tenant-isolation-audit`, `threat-model-change`, `run-golden-path`
