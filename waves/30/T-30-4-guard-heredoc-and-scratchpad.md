# T-30-4: Guard: heredoc bodies going to a data sink are not scanned as scripts; session scratchpad writable

| Field | Value |
|---|---|
| Wave | 30 |
| Scope ref | `always-in-scope: reliability` (team tooling; the guard enforces owner rules) |
| Spec | backlog B-298; `waves/29/deferred-B-298-guard-false-positives.md` (draft, replaced by this card); `waves/29/reviews/plan-architect.md` item 10 (the allowlist design used below); lessons 2026-10-09 wave 28 rows |
| Owner | platform-sre |
| Reviewer | reviewer (opus) |
| Co-reviewers | security-reviewer (opus): the guard is a security control; any loosening needs its approval |
| Risk flags | security control |
| Model | sonnet |

Role file: `.claude/agents/platform-sre.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/platform-sre/` (read MEMORY.md first).

## Owned paths (edit)
- `.claude/hooks/guard-bash.py`, `.claude/hooks/guard-paths.py`, `.claude/hooks/invai_hooklib.py`
- `.claude/hooks/tests/test_w30_4.py` (new). Existing test files only gain cases; none removed or loosened.
- The backup copy: `invai-docs/team/hooks/**` (copy the same files after the suite passes; `invai-docs/team/sync.sh backup` copies agents and skills too, so copy only the hook files), committed in `invai-docs`.
- Report: `invai-docs/waves/30/reports/T-30-4.md`

## Read-only paths
- `.claude/settings.json`, every other hook, every code repo, `invai-docs/**` except your report and `team/hooks/**`

## Depends on
- none. Every agent in this wave runs under these hooks: install (edit `.claude/hooks`) only when your full hook test suite passes, so a half-edited guard never blocks the team. Work on copies under your session scratchpad or `/tmp/t30-4/` until then.

## Acceptance criteria
1. **Allowlist, fail closed.** A heredoc body is data only when its command is on an allowlist of data sinks: `cat` or `tee` whose output goes to a file or to the terminal and is not piped or process-substituted into anything; `git commit|tag -F -`; `gh … --body-file -`; `wc`; `grep`. Only for such a body are the script-path rules and the text rules (deploy, force-push and other blocked-command patterns) skipped. Every other heredoc is scanned exactly as today.
2. **No weakening.** Each of these is still denied when its heredoc body holds a blocked command: `bash|sh|zsh|dash|ksh|fish <<EOF`, `bash -s`, `cat <<EOF | sh`, `bash <(cat <<EOF)`, `source <(…)`, `. /dev/stdin`, `exec|env|command|nohup|timeout|sudo bash <<EOF`, `python|python3|node|tsx|perl|ruby|deno|bun|osascript <<EOF`, `uv run python -`, `pnpm exec tsx`, `npx|pnpm dlx tsx`, `awk -f -`, `docker exec -i … sh`, `xargs sh`, `ssh host <<EOF`, `eval`. A file written by a data heredoc and run later (same command or a later call) is still read and scanned by the script rules. Every existing test passes unchanged.
3. **Scratchpad.** A Write or Edit to the session scratchpad is allowed by `guard-paths.py`: the path is matched after `realpath` (`/tmp` → `/private/tmp`) as `/private/tmp/claude-<uid>/<project>/<session>/scratchpad/**`, with `<uid>` equal to `os.getuid()` and no hard-coded session id. A look-alike path outside it (another uid, `../` escapes, a symlink pointing out) is denied. Running a script from the scratchpad is still scanned by `guard-bash.py`.
4. The module docstring states the exact data-sink rule from AC1.
5. Tests in `test_w30_4.py`: every deny form in AC2 (at least 12 cases), at least 6 allow cases (a TS file with `import … from "../db"` written by `cat <<'EOF' > f.ts`, a commit message via `git commit -F -` quoting `git push --force`, a `tee` to a doc file, `gh issue create --body-file -`, `grep -c x <<EOF`, `wc -l <<EOF`), and 4 scratchpad cases (allowed Write, other-uid denied, `../` escape denied, scratchpad script with a blocked command denied when run).

## Verification
- `cd /Users/bekbolsun/invai/.claude/hooks && python3 -m pytest -q tests 2>&1 | tail -n 15` (or the runner the existing tests use; say which): all pass; give the count before and after.
- Exercise for real: pipe sample hook JSON payloads into `guard-bash.py` and `guard-paths.py` for three AC1 allows, three AC2 denies and the AC3 cases, and show the decisions.
- `diff -rq .claude/hooks invai-docs/team/hooks` shows only `__pycache__` after the backup copy.

## Out of scope
- Owned-path enforcement for other roles (B-47), any change to the blocked-command lists, push or gate rules, `settings.json`.

## Commit and report
- Commit only `invai-docs/team/hooks/**` and your report in `invai-docs` (`git add <paths>`), message ends with the attribution line. Don't push; only the tech lead pushes after the gate.
- Report ≤ 60 lines in `verify-and-report` format.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
