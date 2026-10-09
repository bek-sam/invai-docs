# T-29-5: Guard: no script-path false positives in heredoc text; scratchpad writes allowed

| Field | Value |
|---|---|
| Wave | 29 |
| Scope ref | `always-in-scope: reliability` (team tooling; the guard enforces owner rules) |
| Spec | none; backlog B-298, lessons 2026-10-09 wave 28 (guard heredoc and scratchpad rows) |
| Owner | platform-sre |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (opus): the guard is a security control; any loosening needs its approval |
| Risk flags | security control |
| Model | sonnet |

## Owned paths (edit)
- `.claude/hooks/guard-bash.py`, `.claude/hooks/guard-paths.py`, `.claude/hooks/invai_hooklib.py`
- `.claude/hooks/tests/**` (new tests in a new file `test_w29_5.py`; existing tests only gain cases, none removed or loosened)

## Read-only paths
- `.claude/settings.json`, every other hook, every code repo, `invai-docs/**` except your report

## Depends on
- none. Note: every agent in this wave runs under these hooks. Commit only when your full hook test suite passes, so a half-edited guard never blocks the team.

## Acceptance criteria
1. Given a heredoc whose body is data for a non-interpreter (`cat <<'EOF' > file`, `git commit -F - <<EOF`, `tee`, a `python - <<EOF` is NOT data), when the body contains path-like tokens (`../x`, `./src/a.ts`, TS `import ... from "../db"`), then those tokens are not treated as script paths to run, and the command is allowed if nothing else in it is blocked.
2. **No weakening.** A heredoc fed to an interpreter (`bash`, `sh`, `zsh`, `python`, `python3`, `node`, `tsx`, `uv run python`, `pnpm exec tsx`, `ssh`, `eval`, `source /dev/stdin`, `xargs sh`) is still scanned exactly as today, and every blocked command inside it is still denied. The write-then-run rule stays: writing a script file and running it in the same command is still checked. Every existing test passes unchanged.
3. Given a Write or Edit to the session scratchpad (`/private/tmp/claude-<uid>/<project>/<session>/scratchpad/**`, matched by pattern, not a hard-coded session id), when any role writes there, then `guard-paths.py` allows it. Running a script from the scratchpad is still checked by `guard-bash.py` like any other script (its content is read and scanned).
4. A blocked command in a heredoc body that is only text (for example a doc quoting `git push --force`) is allowed only when the heredoc goes to a non-interpreter; state the exact rule in the module docstring.
5. Tests: one test per AC case above, including at least 6 interpreter-heredoc deny cases and 6 data-heredoc allow cases, and 3 scratchpad cases (Write allowed, Write to a look-alike path outside `/private/tmp/claude-*` denied, a scratchpad script containing a blocked command denied when run).

## Verification
- `cd /Users/bekbolsun/invai/.claude/hooks && python3 -m pytest -q tests 2>&1 | tail -n 15` (or the runner the existing tests use; say which), all pass.
- Exercise for real: pipe sample hook JSON payloads into `guard-bash.py` and `guard-paths.py` for each AC and show the decisions.

## Out of scope
- Owned-path enforcement for other roles (B-47), any change to blocked command lists, push or gate rules.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
