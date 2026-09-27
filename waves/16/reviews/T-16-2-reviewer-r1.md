# Review of T-16-2 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 35 tests in 6.933s  OK` |
| `git -C invai-docs show 59f8d31 --stat` | only owned paths: `team/hooks/guard-bash.py`, `team/hooks/tests/test_guard.py`, `waves/16/reports/T-16-2.md` |
| Re-tallied `CASES` in `test_guard.py` by hand | 112 rows, 76 deny / 27 allow / 9 ask — matches the report exactly |
| My own adversarial probe script (`adversarial.py`, `heredoc_check.py`, scratch dir) feeding `guard-bash.py` cases not in the table | found a real bypass (below) |
| Malformed input (7 shapes incl. non-string `command`, list `tool_input`, non-string `agent_type`) | all denied (`rc=2`) — fails closed, confirmed |

### My adversarial cases
Ran directly against `invai-docs/team/hooks/guard-bash.py` (not the live, still-old `.claude/hooks/guard-bash.py`), each as `agent_type: backend-engineer`:

| Command | Expected | Got |
|---|---|---|
| `xargs git push` | deny | deny |
| `echo hi \| xargs -n1 git push` | deny | deny |
| `find . -exec sh -c 'git push' \;` | deny | deny |
| `git -c core.pager=cat push` | deny | deny |
| `true && git push` | deny | deny |
| `git config --get alias.p` (read-only alias query) | allow | allow |
| **`bash <<< 'git push origin main'`** | deny | **allow** |
| **`bash <<< 'git stash'`** | deny | **allow** |
| **`bash <<< 'git reset --hard'`** | deny | **allow** |
| **`sh <<< 'git add -A'`** | deny | **allow** |
| **`zsh <<< 'pkill node'`** | deny | **allow** |
| `bash << 'EOF'\ngit push\nEOF` (real heredoc, not here-string) | deny | deny (caught only because `\n` is textually replaced with `;` before lexing, not because the heredoc body is understood) |
| `watch -n1 git push` | (already a disclosed known gap) | allow |
| `alias g=git; g push` | (already a disclosed known gap) | allow |
| `npx pnpm install`, `corepack pnpm install` | ask (R5) | allow (undisclosed gap, see notes) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Deny `git push` unless main session / `tech-lead` | **no** | Denied for direct invocation (P01–P20 pass), but bypassed by `bash <<< 'git push'` — see blocking finding 1 |
| 2 Deny stash/reset --hard/checkout --/restore/clean -f | **no**, same root cause | `bash <<< 'git stash'` / `'git reset --hard'` bypass it; direct forms (S01–S26) all correct |
| 3 Deny pkill/killall/pattern-kill | **no**, same root cause | `zsh <<< 'pkill node'` bypasses it; direct forms (K01–K15) all correct |
| 4 Deny `git add -A`/`commit -a` | **no**, same root cause | `sh <<< 'git add -A'` bypasses it; direct forms (A01–A13) all correct |
| 5 Ask for `pnpm install` etc. | partially | direct and prefixed forms (I01–I08) correct; `npx pnpm install` / `corepack pnpm install` are allowed outright (see optional note — lower severity, "ask" not "deny", and not required verbatim by the card's wording) |
| 6 Ask for `db:reset` unless main/qa-engineer | yes | D01–D06 all correct, no bypass found on this rule specifically |
| 7 ≥40-case adversarial table, `python3 -m unittest ...` passes | yes | 112 cases, table tallies exactly, suite green |

## Blocking findings
1. **`invai-docs/team/hooks/guard-bash.py:131-150` (`_lex`) and `:193-248` (`simple_commands`) — a shell here-string (`<<<`) is never unpacked as a command.** `shlex` (with `punctuation_chars=True`) tokenizes `bash <<< 'git push'` as `['bash', '<<<', 'git push']`: the quoted string becomes **one token with an embedded space** (`"git push"`), which is never re-split, so `os.path.basename(w[0])` is the literal string `"git push"`, never matching `git`. The guard has special-case code for `-c`/`-e` inline strings (python/node), `find -exec`, and "a pipe into a shell" (`echo … | sh`), but nothing for `<<<` or plain `<<` heredocs whose body is a real command for the invoked shell to run. **Failure scenario:** a `backend-engineer` agent runs `bash <<< 'git push origin main'` (or `sh <<< 'git stash'`, `zsh <<< 'pkill node'`, `sh <<< 'git add -A'`) through the Bash tool. The PreToolUse guard returns exit 0 (allow) instead of denying, so the push (or stash, or `add -A`) executes — defeating R1–R4 entirely, on a card whose own risk flag is "auth (the guard is a control)" specifically because it must not be bypassable this way. This is exactly the class of case the wave assigns to the security-reviewer co-review ("tries to bypass the guard"), and it is not present anywhere in the 112-row adversarial table (no `<<<` or bare `<<` case is tested).

## Checks
- [x] Only owned paths changed (`git -C invai-docs show 59f8d31 --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; none were weakened; the 112-case table is a genuine expansion, not a loosening, of prior coverage. But the table has a real coverage gap (finding 1) rather than a weakened assertion.
- [x] Fails closed on malformed input and internal errors (confirmed above) — the bypass is a rule-coverage gap, not a fail-open/fail-closed regression
- [ ] Guard can't be trivially defeated for the rules it claims to enforce — **not met**, see finding 1
- [x] Decisions recorded where needed — n/a (no cross-cutting decision required for a bash-word parser fix)

## Optional notes (not blocking)
- `npx pnpm install` and `corepack pnpm install` are allowed outright (not even "ask"): `_strip_prefix`'s `PREFIX_CMDS` doesn't include `npx`/`corepack`, so `head` stays `"npx"`/`"corepack"` and never reaches the `pnpm`/`npm` branch in `lesson_rules`. Lower severity than finding 1 (R5 is "ask", not "deny", and the card's wording names `pnpm install/i/add` and `npm install/i/ci` specifically), and not listed in the report's "Known gaps" section — worth adding there or fixing alongside the here-string fix.
- `watch -n1 git push` and `alias g=git; g push` are already disclosed in the report's "Known gaps" section ("watch, make or package scripts that run git"; "shell functions and aliases defined in an earlier call") — acceptable as documented, out-of-reach-of-a-denylist limitations, consistent with the report's stated design philosophy.
- Same stale `sync.sh` note as T-16-1's review: the "Blocked by other owners" complaint was already fixed at `1c14f5d`, before this card's commit.

## Suggested fix (for the author, not prescriptive)
Treat `<<<` and `<<` the way `-c`/`-e` inline code and `find -exec` are already treated: when a redirect operator is `<<<` or `<<` and its target is a single quoted-looking token (or, for `<<`, the heredoc body collected up to the delimiter), recursively run it through `simple_commands` the same way `_substitutions`/eval bodies are. Add here-string and heredoc rows to the adversarial table for R1–R4 so a regression is caught automatically.
