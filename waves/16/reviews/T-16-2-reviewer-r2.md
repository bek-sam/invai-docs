# Review of T-16-2 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 43 tests in 7.2s  OK` |
| `git -C invai-docs show 0fb800b --stat` | `guard-bash.py`, `guard-memory-path.py`, `tests/test_guard.py`, `tests/test_memory_path.py` all inside T-16-2's owned paths and the round-2 grant |
| Re-tallied `CASES` in `test_guard.py` | 147 rows (100 deny / 32 allow / 15 ask) — matches the report exactly |
| Re-ran my round-1 bypass script (`heredoc_check.py`) against the new `guard-bash.py` | all 5 round-1 bypasses (`bash/sh/zsh <<< 'git push/stash/reset --hard/add -A/pkill'`) now **deny**, confirming finding 1 is fixed |
| Re-ran my round-1 `npx pnpm install` / `corepack pnpm install` optional note | both now **ask**, along with `pnpx`, `bunx`, `npx --yes`, `pnpm dlx`, `pnpm exec`, `yarn exec`, `npm exec --` forms I tried myself — the optional note is resolved |
| New adversarial probes against the round-2 fix (my own, not in the table) — see below | found one new gap in `guard-memory-path.py` |
| Manual verification with real `bash -c` that `source <<< '...'` and `. <<< '...'` are harmless (bash requires a filename for `source`/`.`, so redirecting stdin does nothing) | confirms these are not bypasses, unlike round 1's finding |

### My new adversarial cases against `guard-bash.py` (all now correctly denied/asked)
`bash <<< 'bash <<< "git push"'` (nested) → deny. `BASH<<<'git push'` (uppercase, no spaces) → deny.
`bash <<< '   git    push  '` (extra whitespace) → deny. `npm exec --yes -- git push` → deny.
`pnpm --dir . exec git push` → deny. `yarn exec git push` → deny. `pnpm dlx -- pnpm install` → ask.

One case still gets through, in the same "determined bypass" category the report already discloses as out of
reach (base64+eval, source, aliases): `bash <<< "$(echo 'git push')"` → **allow**. I confirmed with real bash
that this genuinely runs `git push` (the command substitution produces the string first, then the here-string
feeds it to `bash`). This needs two composed indirection tricks (an explicit `echo` plus a here-string) rather
than the round-1 finding's single, everyday-looking construct, so I'm not blocking on it — see optional notes.

### A real gap in the new `guard-memory-path.py` (blocking)
The grant's own motivating bug is: "An agent started from a subfolder writes its memory into that subfolder's
`.claude/`" (docstring, `guard-memory-path.py:5-7`). The hook's own short-circuit check operates on the **raw,
unresolved** `file_path` text, not the resolved absolute path:
```python
MARK = "/.claude/agent-memory/"
...
if not isinstance(path, str) or MARK not in path.replace(os.sep, "/"):
    return
```
`agent-brief.md` documents the standard memory path as **relative, with no leading slash**: "Your role's memory
is `.claude/agent-memory/<role>/MEMORY.md`." When an agent's `cwd` is a subfolder (exactly the bug scenario)
and it writes to that exact, brief-documented relative path, `MARK` (`"/.claude/agent-memory/"`, with a leading
slash) is **not a substring** of `.claude/agent-memory/<role>/MEMORY.md` (no leading slash), so the hook
returns before ever computing `full`/`home` and allows the write silently.

I reproduced it directly:
```
CLAUDE_PROJECT_DIR=/Users/bekbolsun/invai
tool_input.file_path = ".claude/agent-memory/platform-sre/notes.md"
cwd = "/Users/bekbolsun/invai/invai-docs/waves/16"
-> rc=0 (allowed), even though the file resolves to
   .../invai-docs/waves/16/.claude/agent-memory/platform-sre/notes.md — the exact bug this hook exists to catch.
```
By contrast, `./.claude/agent-memory/...` (with a `./` prefix) **is** caught, because the raw text then does
contain `/.claude/agent-memory/`. So the hook's coverage depends on incidental leading-slash punctuation in the
caller's string, not on where the file actually resolves to. `test_memory_path.py`'s "relative" case
(`"invai-docs/.claude/agent-memory/qa-engineer/x.md"`) happens to have a directory before `.claude`, so it
passes by accident and doesn't exercise the bare, brief-documented form.

**Failure scenario:** `platform-sre`, resumed inside `invai-docs/waves/17/` for a later card, follows the brief
literally and writes `.claude/agent-memory/platform-sre/MEMORY.md`. The hook allows it, the memory lands in
`invai-docs/waves/17/.claude/agent-memory/platform-sre/MEMORY.md`, and no later run ever loads it — reproducing
the exact incident (`waves/16/.claude`, `waves/17/.claude`, `invai-docs/.claude` I noticed as untracked,
unexplained directories while reviewing round 1) that this hook was written to stop.

## Acceptance / grant criteria
| # | Met? | Evidence |
|---|---|---|
| Round-1 finding 1 (here-string bypass of R1–R4) fixed | yes | W01–W14 pass; my own re-probe confirms |
| Security r1 finding (`npx` wrapper bypass) fixed | yes | N01–N21 pass; my own re-probe confirms |
| Optional note (`npx`/`corepack pnpm install`) resolved | yes | now `ask`, confirmed myself |
| `guard-memory-path.py` matches its grant (PreToolUse on `Write\|Edit\|MultiEdit`, denies writes outside `$CLAUDE_PROJECT_DIR/.claude/agent-memory/`, fails open, registered in `settings.json`) | **partially** | matches the grant's shape, but doesn't catch the relative-path form the grant's own motivating bug (and the org's documented memory-path convention) actually produces — see blocking finding |
| ≥40-case adversarial table still passes, still fails closed on malformed input | yes | 147 cases tallied, `test_malformed_input_is_denied` green |

## Blocking findings
1. **`invai-docs/team/hooks/guard-memory-path.py:16,23`** — the `MARK = "/.claude/agent-memory/"` substring
   check runs on the raw `file_path` before path resolution, so a relative path with no leading slash before
   `.claude` (the exact form `agent-brief.md` documents: `.claude/agent-memory/<role>/MEMORY.md`) is never
   caught, even though it resolves into the wrong subfolder when `cwd` isn't the project root. Failure
   scenario above. Fix: compute `full` (the realpath) first, then check `MARK in full.replace(os.sep, "/")`
   (or just check whether `full` is outside `home`) instead of pre-filtering on the unresolved string.

## Checks
- [x] Only owned paths changed (`git -C invai-docs show 0fb800b --stat`, T-16-2's files plus the grant)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; the 35 new W/N cases are a genuine expansion; `test_memory_path.py`'s 5 tests
      are real but don't hit the gap above (its one "relative" case has an extra path segment that hides it)
- [x] Fails closed on `guard-bash.py` malformed input (confirmed); `guard-memory-path.py` fails open by design
      (documented as "a nudge, not a security control") — consistent with its own stated scope
- [ ] The new hook actually catches its own motivating bug in the common (brief-documented) form — **not met**

## Optional notes (not blocking)
- `bash <<< "$(echo 'git push')"` (command substitution composed with a here-string) still bypasses R1. This is
  the same class of gap already disclosed ("still out of reach: source, aliases and functions, base64 + eval")
  — it requires deliberately composing two indirection tricks rather than the round-1 finding's single, everyday
  construct. Worth a mention next to the existing "still out of reach" list in the report, not a blocker.
- `source <<< '...'` and `. <<< '...'` are allowed and I checked they are genuinely harmless: real bash requires
  a filename argument for `source`/`.`, so stdin redirection does nothing (`source: filename argument required`).
  Not a finding.
