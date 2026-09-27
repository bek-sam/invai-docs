# Review of T-16-2 (round 3)

- Reviewer: security-reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 44 tests in 8.152s OK` |
| Round-2 finding reproduction + controls, fed directly to `guard-memory-path.py` | all now correct, see below |

## Round-2 finding — verified fixed
`guard-memory-path.py` now resolves `full = os.path.realpath(cwd + path)` **before** testing for `MARK`,
instead of substring-matching the raw `file_path`. Re-ran the exact reproduction:

- **A** (the bug): bare relative path `.claude/agent-memory/security-reviewer/note.md` from `cwd =
  invai-backend`, `Write` → **now exit 2**, correct message and right-path suggestion (`.../invai/.claude/agent-memory/security-reviewer/note.md`).
- **A2**: same shape via `Edit`, different role/cwd (`platform-sre` from `invai-docs/waves/16`) → **exit 2**, correct.
- **B** `./`-prefixed relative from a subfolder (already worked in round 2) → still **exit 2**.
- **C** absolute path to the wrong subfolder → still **exit 2**.
- **D** bare relative path issued *from* the project root (genuinely the right location) → **exit 0**, no false block.
- **E** `../../` traversal from a subfolder that lands back on the true home → **exit 0**, no false block.
- **F** missing `CLAUDE_PROJECT_DIR` → **exit 0**, fails open as documented.
- **H** empty-string `file_path` → **exit 0**, fails open.

One behavior changed from round 2, not a regression: **G**, a symlink inside the real home pointing outside
the project, now **allows** (was denied in round 2) — because `full` after realpath resolution
(`/private/tmp/.../outside/note.md`) no longer contains `/.claude/agent-memory/` at all, so the hook correctly
treats it as "not memory-shaped" rather than "memory in the wrong place." That's consistent with this hook's
stated job (catch memory landing in a subfolder's `.claude/`, nothing more) and its documented fail-open,
nudge-not-a-control nature; it isn't a new gap worth reopening.

The new test (`test_relative_paths_are_resolved_against_cwd_first`, 7 subcases including the exact bare-relative
and the over/under-shooting traversal cases) covers what I re-ran by hand.

## Checks
- [x] Only T-16-2's owned/granted paths changed: `guard-memory-path.py`, `tests/test_memory_path.py`,
      `waves/16/reports/T-16-2.md`
- [x] Nothing outside scope
- [x] Tests exercise the fix; no `.skip`/loosened assertions
- [x] Round-2 blocking finding closed with a live reproduction, not just a code read
- [x] No new false-blocks introduced (controls D, E, F, H all still allow correctly)

## Recommendation
Approve. Both `guard-bash.py` (approved r2, unchanged since) and `guard-memory-path.py` now hold against every
reproduction I've thrown at them across three rounds, apart from the accepted, execution-requiring limits
already on record (base64+eval, script-then-run, the `$(printf ...)` command-substitution edge from r2). T-16-2
is clear from my side.
