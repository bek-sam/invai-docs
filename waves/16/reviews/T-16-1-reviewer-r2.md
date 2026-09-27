# Review of T-16-1 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 43 tests in 7.2s  OK` |
| `git -C invai-docs show 0fb800b --stat` | touches `invai_hooklib.py`, `verify-gate.py`, `tests/test_fast_check.py`, `tests/test_verify_hooks.py`, `settings.json` (T-16-1's owned files/grant) plus `guard-bash.py`, `guard-memory-path.py`, `tests/test_guard.py`, `tests/test_memory_path.py` (T-16-2's, reviewed separately in `T-16-2-reviewer-r2.md`), and both cards' reports |
| Old-vs-new `parse_verifications` on the reviewer's exact truncated-pipe case (below) | old code wrongly credited it; new code doesn't — confirms the change is a tightening |
| My own JSON probes into `track-verify.py` for the here-string re-lex (`bash <<< 'pnpm typecheck && pnpm lint'`, `cat <<< '...'` to a non-shell) | matched `test_here_string_to_a_shell_counts` |

### Confirming the changed test is stricter, not weaker
`test_separate_commands_and_forms_count` used to run `pnpm --dir invai-backend lint 2>&1 | tail -3` with an
innocuous `stdout` and expected it to count (the old code trusted the output unless a `FAIL_MARKERS` regex
matched). It now requires `set -eo pipefail;` first. I extracted the round-1 `invai_hooklib.py`
(`git show e97c71a:team/hooks/invai_hooklib.py`) and ran both versions on the exact case the round-1 security
finding was about — a real failure hidden by truncation:
```
cmd = "pnpm test | head -3"
out = " RUN  v5.0.0\n ✓ src/a.test.ts (3)"   # no failure marker text, but head -3 could have cut off a real failure
OLD parse_verifications(cmd, ".../invai-backend", out) -> [('.../invai-backend', 'backend', 'test')]   # wrongly credited
NEW parse_verifications(cmd, ".../invai-backend")      -> []                                            # not credited
```
This proves the change closes a real gap (a piped, truncated failing run could get false credit) rather than
just moving the goalposts. The new tests (`test_piped_run_is_not_counted_without_pipefail`,
`test_piped_run_counts_under_pipefail`, `test_pipefail_must_come_first_and_stay_on`) cover: no pipefail (block),
pipefail set first (counts), and pipefail turned back off or declared after the pipe (still blocks). All pass.

## Acceptance criteria
Unchanged from round 1 except where the round-2 diff touches behavior; all still met:
| # | Met? | Evidence |
|---|---|---|
| 1–7 (fast check, fail-open, tracker, gate, no false blocks, tests, settings) | yes | full suite green; my round-1 probes (worktree edit, `cd`/`-C` forms, failed run, `stop_hook_active`, docs-only, malformed input) still hold — nothing in this diff touches `post-edit-check.py` |
| Piped checks require `set -o pipefail` (new, from the round-1 security finding) | yes | table above, plus the three new tests |
| Here-strings/heredocs fed to a shell are re-lexed for the tracker too | yes | `test_here_string_to_a_shell_counts`; a here-string to a non-shell (`cat <<<`) still doesn't count, matching the parallel fix in `guard-bash.py` |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed for T-16-1 (`invai_hooklib.py`, `verify-gate.py`, `tests/test_fast_check.py`, `tests/test_verify_hooks.py`, `settings.json` — the new `guard-memory-path.py` entry inside `settings.json` is T-16-2's per the 2026-09-26 grant, not a T-16-1 change)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and the one changed assertion (`test_separate_commands_and_forms_count`) and the renamed/expanded piped-run tests are strictly stricter (proven above), not weaker; no `.skip`/`.only`
- [x] Tenancy / idempotency / money / en-es — not applicable (process/tooling card)
- [x] Decisions recorded where needed — n/a, same reasoning as round 1

## Optional notes (not blocking)
- `test_fast_check.py`'s settings assertion now indexes `PreToolUse[0]` instead of requiring the array to have
  exactly one entry, because `guard-memory-path.py` added a second `PreToolUse` hook. The comparison itself
  (the guard entry, byte for byte) is unchanged — this is an adaptation to a real new entry, not a loosened
  check.
