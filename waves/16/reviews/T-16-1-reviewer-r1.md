# Review of T-16-1 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 35 tests in 6.923s  OK` (30 from T-16-1 + 5 from T-16-2, all pass) |
| `diff <(cat .claude/hooks/guard-bash.py) <(cat invai-docs/team/hooks/guard-bash.py)` (confirm nothing installed live) | live `.claude/hooks/` has no `post-edit-check.py`/`track-verify.py`/`verify-gate.py`, and live `.claude/settings.json` still only registers the PreToolUse guard — matches the report's "nothing installed" claim |
| `git -C invai-docs show e97c71a --stat` | only owned paths: `team/hooks/{invai_hooklib,post-edit-check,track-verify,verify-gate}.py`, `team/hooks/tests/{test_fast_check,test_verify_hooks}.py`, `team/settings.json`, `waves/16/reports/T-16-1.md` |
| My own JSON probes into `track-verify.py`/`verify-gate.py`/`post-edit-check.py` (scratch dir under `/private/tmp/.../scratchpad/probe`, `INVAI_HOOK_STATE_DIR` pointed at scratch, never `.claude/state`) — see below | all matched the card's acceptance criteria |
| Malformed JSON (`""`, `"not json"`, `"[1,2,3]"`, `'{"tool_input": 7}'`, `"null"`) fed to all three hooks | every case: `rc=0`, empty stdout (fails open, silent) |

### My own exercises (cases the author's report didn't show verbatim)
1. **Edit in a worktree path** (`.../invai-backend-T-9-9/src/a.ts`, a `.git` *file* not a directory, as a real worktree has): `track-verify.py` recorded it under `kind: backend`; the following `SubagentStop` blocked with `node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check . && node_modules/.bin/vitest run` (never `pnpm`), matching the waves-6/7 lesson.
2. **`cd invai-backend && pnpm test`**: only `ok.test` was set (not `typecheck`/`lint`); the gate still blocked and named only the missing two.
3. **`pnpm -C invai-web build`**: correctly attributed to `invai-web`, `ok.build` set.
4. **A failed test run** (`PostToolUseFailure` event for `cd invai-backend && pnpm test`): `ok` stayed `{}`; not counted, matching "failures don't count".
5. **`stop_hook_active: true`**: `verify-gate.py` returned nothing (allowed), even with pending unverified edits.
6. **Docs-only edit by the main session** (`invai-docs/team/lessons.md`): no state file was created at all, and the following `Stop` was silent.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Fast check (Biome file-only read-only, imaging ruff, typecheck <8s, ≤40 lines file:line first, other files <100ms) | yes | `test_ts_lint_and_type_errors_reach_the_model_file_line_first`, `test_python_in_imaging_uses_ruff`, `test_output_is_capped_at_40_lines`, `test_docs_and_other_files_exit_fast_and_silent` all green in my run; times table in the report is plausible (native TS 7 compiler, all repos <1.5s) |
| 2 Fails open, ≤20s timeout, comment on the guard difference | yes | malformed-input probe above (rc=0, silent); `settings.json` timeout 20; docstring in `post-edit-check.py` states the fail-open/fail-closed distinction explicitly |
| 3 Tracker per session+agent, repos/worktrees, verify forms, state in `.claude/state/`, pruned at 2 days, atomic | yes | my worktree probe (1) plus `test_state_is_atomic_json_and_old_files_are_pruned`, `test_concurrent_updates_keep_every_repo` |
| 4 Gate blocks once with commands+honesty line; `stop_hook_active` allows; read-only/docs never block; web/floor need build | yes | my probes (2,3,5,6) plus `test_code_edit_without_checks_blocks_once_with_commands`, `test_web_needs_build` |
| 5 No false blocks | yes | probe 6, `test_read_only_agent_never_blocks` |
| 6 Tests cover each required case | yes | 30 tests enumerated in the report, all pass; I independently fed equivalent JSON by hand for 6 of them and got matching results |
| 7 `settings.json` registers the hooks, guard byte-for-byte unchanged | yes | `test_settings_timeout_and_fail_open_comment` compares the PreToolUse entry exactly; I also diffed the live guard against the team copy (only the T-16-2 additions differ, all inside the guard's own docstring/rules — not touched by this card) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git -C invai-docs show e97c71a --stat`; `invai_hooklib.py` is covered by the wave.md 2026-09-26 grant)
- [x] Nothing outside scope (no live `.claude/` install, no other repo touched)
- [x] Tests exercise the behavior, and none were weakened (new test suite, nothing pre-existing to loosen; no `.skip`/`.only`)
- [x] Tenancy / idempotency / money / en-es — not applicable (process/tooling card, no product code)
- [x] Decisions recorded where needed — the shared `invai_hooklib.py` split and the "block once keyed to edit state" choice are explained in the report; both are local implementation choices, not cross-cutting product decisions, so a `decisions/NNNN` entry isn't required

## Optional notes (not blocking)
- The report's "Blocked by other owners" note about `sync.sh` copying `hooks/*` (deleting `hooks/tests/`) describes a bug that was already fixed at `1c14f5d` (T-16-3 r2, sync.sh now copies `hooks/*.py`), **2.5 minutes before** this card's commit (`e97c71a`). The current `invai-docs/team/sync.sh` already does the right thing. Worth a one-line correction next time the report is touched, but it doesn't affect this card's own files and isn't blocking.
- The fast check runs a full-repo `tsc` on every edit; in a shared tree it can surface another agent's in-progress type errors under the edited file's report. This is disclosed as a known gap and mitigated with a note in the output ("from your change, or another agent's work in progress"); acceptable.
