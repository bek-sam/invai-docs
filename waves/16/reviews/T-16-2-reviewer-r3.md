# Review of T-16-2 (round 3)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: escalate (round 3; per `independent-review`, round 3 is always escalate to the tech lead, regardless of outcome)

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 44 tests in 7.9s  OK` |
| `git -C invai-docs show d4627a2 --stat` | only `team/hooks/guard-memory-path.py`, `team/hooks/tests/test_memory_path.py`, `waves/16/reports/T-16-2.md` — all T-16-2's owned/granted paths |
| My exact round-2 reproduction (`.claude/agent-memory/platform-sre/notes.md`, `cwd=.../invai-docs/waves/16`, `CLAUDE_PROJECT_DIR=/Users/bekbolsun/invai`) | now `rc=2`, denied with the correct target path — **the round-2 blocking finding is fixed** |
| Same path from the project root (`cwd=/Users/bekbolsun/invai`) | `rc=0`, allowed, as it should be |
| `../.claude/agent-memory/x/y.md` from `waves/16` (climbs to `invai-docs/waves/.claude`) | denied with the correct target path |
| The original round-1 here-string bypasses and the round-2 `npx`/wrapper bypasses (re-run once more) | still all deny/ask, no regression |

## My round 2 finding: status
**Fixed.** `guard-memory-path.py` now resolves `path` against `cwd` with `os.path.realpath` *before* checking
for the `/.claude/agent-memory/` marker, instead of pattern-matching the raw, unresolved string. The bare
relative form `agent-brief.md` documents (`.claude/agent-memory/<role>/MEMORY.md`) is caught when it would land
outside `$CLAUDE_PROJECT_DIR/.claude/agent-memory/`, and still allowed when it correctly resolves inside it.
`test_relative_paths_are_resolved_against_cwd_first` covers 7 sub-cases (bare relative and `./`-prefixed, from
both a subfolder and the root, plus `../` forms that climb back to or short of the root) and all pass.

## Acceptance / grant criteria
| # | Met? | Evidence |
|---|---|---|
| `guard-memory-path.py` catches the relative, brief-documented path form from a subfolder cwd (round-2 blocking finding) | yes | repro above, `test_relative_paths_are_resolved_against_cwd_first` |
| No regression on round-1/round-2 fixes (here-string bypass, `npx` wrapper bypass) | yes | re-ran both probe scripts, all still correct |
| Full hook test suite passes | yes | 44 tests, OK |

## Blocking findings
None found in this round's diff.

## Checks
- [x] Only owned paths changed (`git -C invai-docs show d4627a2 --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the fix; the new sub-cases are a genuine addition, not a loosening of any existing assertion
- [x] `guard-memory-path.py` still fails open on malformed input (`test_fails_open` unchanged, still green)
- [x] Decisions — n/a

## Optional notes (not blocking)
- The report cites "the guard held on 24 of the security reviewer's 25 round-2 bypass attempts" for
  `guard-bash.py`. That is security-reviewer's own co-review thread; I have not seen their round-2 file and am
  not evaluating that count here — the tech lead should confirm security-reviewer's own verdict separately
  before treating `guard-bash.py` itself as settled.
- My own still-open, non-blocking note from round 2 stands: `bash <<< "$(echo 'git push')"` remains an
  out-of-reach, composed-indirection bypass of `guard-bash.py` (not `guard-memory-path.py`), consistent with
  the report's disclosed "still out of reach" list.

## Why `escalate` despite no new blocking finding
This is T-16-2's third review round (round 1: changes-required; round 2: changes-required). The
`independent-review` playbook caps review at 2 rounds: round 3 is always `escalate` to the tech lead, even when
the latest fix looks clean, so a human/tech-lead decision closes out the card rather than a third reviewer
cycle. My technical assessment above is that the round-2 finding is resolved and I found no new blocking issue,
which the tech lead can weigh directly.
