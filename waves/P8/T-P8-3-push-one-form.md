# T-P8-3: T-23-6 round 3, the push check allows exactly one push form

| Field | Value |
|---|---|
| Wave | P8 |
| Scope ref | `always-in-scope: bug` (T-23-6, owner-approved 2026-09-29); owner OI-22 answer A (2026-10-01) |
| Owner | platform-sre |
| Reviewer | reviewer (fable) + security-reviewer (fable), round 3 of T-23-6 |
| Risk flags | security (hook) |
| Model | opus |

## Read first
- `.claude/agents/platform-sre.md`; card `invai-docs/waves/23/T-23-6.md`; reviews `waves/23/reviews/T-23-6-reviewer-r2.md` and `T-23-6-security-reviewer-r1.md` (S-42); OI-22 in `invai-docs/owner-inbox.md`. The Safety section of `waves/P7/T-P7-4-hook-gaps.md` applies (temp copy first; the guard fails closed for the whole team).
- Starts after T-P8-2 has installed its change: begin from the live `.claude/hooks/guard-bash.py`.

## Owned paths (edit)
- `.claude/hooks/guard-bash.py` (push check only), `.claude/hooks/invai_hooklib.py` if needed, `.claude/hooks/tests/**`, the backups `invai-docs/team/hooks/**` (identical at the end); `invai-infra/scripts/gate.sh`, `invai-infra/scripts/gate/**`, `invai-infra/README.md` only if the push message or usage text must change.

## Acceptance criteria
1. A `git push` that targets a code repo (`invai-backend`, `-web`, `-floor`, `-ui`, `-contracts`, `-imaging`, `-infra`) is allowed only in this form, as the whole Bash command with nothing before or after it (no `;`, `&&`, `|`, redirect, `$(...)`, backticks, subshell, `bash -c`, env prefix): `git -C /Users/bekbolsun/invai/<repo> push origin <ref>`, where `<repo>` is a literal absolute path to one of the code repos (no `~`, `$`, `{}`, `..`, globs) and `<ref>` is `main` or `<sha>:main` (a hex SHA of 7-40 chars). Then the existing stamp check applies (stamp present, under 24 h, records the commit being pushed).
2. Every other push form is refused with one clear message that names the allowed form, for any repo the guard can't positively identify as `invai-docs` (docs pushes keep working, including `git -C /Users/bekbolsun/invai/invai-docs push origin main`). Anything that looks like a push inside `$(...)`, `bash -c`, `eval`, `xargs`, a pipe or a script is refused (S-42).
3. Existing guards are unchanged: forced pushes (`-f`, `--force`, `+ref`, `--force-with-lease`), tag pushes, `--mirror`, `--all`, `--delete`, deploys, `aws`, secrets. The folder-guessing code (`_push_target_dir` and helpers) that the new form makes unnecessary is removed, not left as a second path.
4. Tests: allow the exact form with a fresh stamp (both `main` and `<sha>:main`); deny it with a stale or old stamp; deny `cd <repo> && git push origin main`, `git push origin main` with no `-C`, `... 2>&1 | tail -3`, `~/invai/...`, `{...}` paths, `$(git -C ... push ...)`, `bash -c '...push...'`, a relative `-C`, a forced push in the exact form; allow the docs push. Every existing test either passes or is replaced by an equal-or-stricter one (list any replaced test and why).
5. `README.md` in `invai-infra` and the guard's deny message tell the user the one form.

## Verification
- Temp copy `/tmp/p8-3-hooks/` first; `python3 -B -m unittest discover -s <dir>/tests 2>&1 | tail -n 5` for the temp copy, the live copy and `invai-docs/team/hooks/`; `diff -rq` live vs backup.
- After installing, prove normal work passes: `git -C /Users/bekbolsun/invai/invai-docs status --short`.
- Do not push anything and do not create a real stamp for a real repo; use `INVAI_GATE_STAMP_PATH` and fixture repos in tests.
- If you change `gate.sh`: `cd invai-infra && pnpm typecheck && pnpm lint 2>&1 | tail -n 20`.

## Commit
- `invai-docs`: only `team/hooks/**` and your report. `invai-infra`: only gate paths you changed (likely none). Attribution line at the end. Don't stage `learn/**`. Don't push; only the tech lead pushes after the gate.

## Report
- `invai-docs/waves/P8/reports/T-P8-3.md`, `verify-and-report` format, at most 60 lines. Record every PID you start.
