# Review of T-16-2 (round 2)

- Reviewer: security-reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 43 tests in 7.206s OK` |
| 25-case adversarial re-run of round-1 findings plus the tech lead's new surface (`npx` family, `npx --yes`, `pnpm exec --`/`npm exec --`/`yarn dlx`/`pnpm dlx`, `bunx`, `pnpx`, `npx --package X -c "..."`, here-strings `<<<`, heredocs `<<EOF`/`<<-EOF`, nested quotes, a here-string piped into a shell, a here-string fed to a non-shell tool) against `guard-bash.py` | **24/25 as expected** — see below |
| `guard-memory-path.py` probed with: bare relative path, `./`-prefixed relative path, absolute path, missing `CLAUDE_PROJECT_DIR`, `..` traversal (both under- and over-shooting), a symlink escaping the real home, `Edit` vs `Write` | **new finding**, see below |

## Round-1 finding — verified fixed
Every round-1 reproduction (`npx git push origin main`, `npx git add -A`, `npx git stash`, `npx pkill -f node`,
`npx pnpm install`, `npx npm install`, `corepack pnpm install`, `npx aws s3 rm ...`) now correctly denies/asks,
matching the bare-command behavior. `aws` is now also denied at the word level (`lesson_rules`), independent
of the prefix parser, so the anchored-regex root cause is fixed structurally, not just patched for one prefix.

## New surface from the tech lead — 24/25 correct
`npx --yes git push`, `pnpm exec -- git push`, `npm exec -- git push`, `yarn dlx`/`pnpm dlx git push`, `bunx`,
`pnpx`, `npx --package foo -c "git push origin main"`, `bash <<< 'git push origin main'`,
`sh <<< "git push origin main"`, a here-string with `&&` inside it, `bash <<-EOF ... EOF`, `bash << 'EOF' ...
EOF`, a here-string with nested quotes, a here-string piped into a shell (`echo '...' | bash`) — **all
correctly deny**. `grep x <<< 'git push origin main'` (here-string fed to a non-shell) — **correctly stays
allowed**, matching the report's stated behavior (text, not executed).

One mismatch, informational only, not blocking: `bash -c "$(printf 'git %s origin main' 'push')"` is **allowed**.
The guard's `$(...)`-substitution handling recursively parses the *substitution body* (`printf 'git %s origin
main' 'push'`) as its own command, which is correctly not a push — but it has no way to know that command's
*output* becomes the literal `-c` argument, so the outer `bash -c " SUBST "` is checked against a placeholder,
not against `git push origin main`. This requires actually executing a shell builtin to know the resulting
string, which is the same class of gap as the already-disclosed base64+eval and script-file bypasses ("out of
reach of any denylist"). I'm not blocking on it, but it's worth naming next to the other accepted limits so
it isn't forgotten as new territory once the wave moves on.

## Blocking finding

1. **`invai-docs/team/hooks/guard-memory-path.py:23` — a bare relative path (no leading `/` or `./`) is invisible to the hook, and this is exactly the shape most likely to reproduce the incident the hook was built to stop.**

   `MARK = "/.claude/agent-memory/"` (with a leading slash) is checked as a plain substring of the *raw*
   `file_path` before any path resolution: `if not isinstance(path, str) or MARK not in path.replace(os.sep,
   "/"): return`. A relative path typed exactly as `.claude/agent-memory/<role>/note.md` — the natural way to
   write it, with no `./` prefix — has no `/` character immediately before `.claude`, so `MARK` is not found
   and the hook returns (allows) without ever resolving the path.

   Reproduced:
   ```
   CLAUDE_PROJECT_DIR=/Users/bekbolsun/invai python3 guard-memory-path.py <<'EOF'
   {"tool_name":"Write","tool_input":{"file_path":".claude/agent-memory/security-reviewer/note.md"},
    "cwd":"/Users/bekbolsun/invai/invai-backend"}
   EOF
   ```
   → **exit 0 (allowed)**. That resolves to `/Users/bekbolsun/invai/invai-backend/.claude/agent-memory/security-reviewer/note.md` —
   a subfolder's `.claude/`, not `$CLAUDE_PROJECT_DIR/.claude/agent-memory/` — i.e. precisely the "21 files
   landed in `invai-docs/.claude/` and `waves/1x/.claude/`" bug the docstring cites as the reason this hook
   exists. Same result for `tool_name: "Edit"`. Controls I ran alongside it behave correctly and rule out an
   over-broad fix being the answer: the identical path with a `./` prefix is denied with the right message;
   the absolute form of the same bad path is denied; `..`-traversal that truly resolves to the correct home is
   allowed (no false block); a symlink placed inside the real home that points outside the project is denied
   (realpath resolution catches it); a missing `CLAUDE_PROJECT_DIR` fails open as documented.

   This card's own round-2 report notes the mechanism first-hand: "my own platform-sre memory from round 1
   was written to `invai-docs/waves/16/.claude/agent-memory/platform-sre/`" — a relative-looking write from a
   session whose `cwd` was `invai-docs/`. The new hook, as written, would not have caught that same write if
   it were tried again from that `cwd` with a bare relative path, because the guard-memory-path check happens
   on `tool_input.file_path` before it's ever joined with `cwd`.

   **Suggested fix (for platform-sre, not mine to make):** join `path` with `cwd` (or check `os.path.isabs`)
   *before* testing for `MARK`, or simply always resolve `full = os.path.realpath(...)` first and test
   `MARK` against `full` instead of the raw `path`. Add a bare-relative-path case (no `./`, no leading `/`) to
   `test_memory_path.py` — right now all 5 tests use either an absolute path or one with a leading `./`/`../`,
   so this exact miss wasn't exercised.

## Checks
- [x] Only owned/granted paths changed: `guard-bash.py`, `guard-memory-path.py` (granted to T-16-2 per
      `wave.md`'s 2026-09-26 grant row), `tests/test_guard.py`, `tests/test_memory_path.py`
- [x] Nothing outside scope
- [x] Tests exercise the new behavior; no `.skip`/loosened assertions found
- [x] Round-1 blocking finding (the `npx`/wrapper-prefix family, including `aws`) closed with reproductions
      across the exact new surface named for this round
- [ ] The new `guard-memory-path.py` control has a real, reproducible gap in its own core check — see finding 1

## Recommendation
Send finding 1 back to platform-sre: fix the ordering (resolve-then-check, not check-then-resolve) in
`guard-memory-path.py`, add the bare-relative-path test case, and I'll re-run the same reproduction before
approving. The `guard-bash.py` half of this card (the actual security control) is now solid against everything
tried across both rounds except the disclosed, accepted, execution-requiring limits.
