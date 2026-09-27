# Review of T-16-2 (round 1)

- Reviewer: security-reviewer on Opus 5.5
- Author: platform-sre on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `python3 -B -m unittest discover -s invai-docs/team/hooks/tests` | `Ran 35 tests in 6.442s OK` |
| Adversarial probes: JSON fed directly to `team/hooks/guard-bash.py` on stdin, `tool_name: Bash`, varying `tool_input.command` and top-level `agent_type` (scripts kept in scratchpad, not committed) | see findings below; full case list in my probe output |
| `grep -c npx invai-docs/team/hooks/tests/test_guard.py` | `0` — `npx` is absent from all 112 adversarial cases |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 `git push` deny unless main/tech-lead | **Not fully** | Holds for a bare `git push`, but bypassed via `npx git push origin main` (finding 1) |
| 2 deny stash/reset --hard/checkout --/restore/clean | **Not fully** | Holds for bare forms; `npx git stash`, presumably `npx git reset --hard` etc. bypass the same way (finding 1) |
| 3 deny pkill/killall/pattern-kill | **Not fully** | `npx pkill -f node` → ALLOW (finding 1) |
| 4 deny `git add -A`/`-a` | **Not fully** | `npx git add -A` → ALLOW (finding 1) |
| 5 ask for pnpm/npm install | **Not fully** | `npx pnpm install`, `npx npm install`, `corepack pnpm install` → ALLOW, no ask (finding 1) |
| 6 ask for db:reset | met | not retested beyond the report's cases; same root cause would apply to `npx pnpm db:reset` but out of scope of this finding's reproduction |
| 7 ≥40 adversarial cases, incl. env prefixes, `-C`, `cd &&`, quoting, uppercase, malformed input | **Not fully** | Table is thorough (112 cases) but has zero coverage of `npx`/`corepack`/other npm-ecosystem wrapper prefixes, which is exactly the class this criterion asks for |
| Fail-closed on malformed input | met | `echo 'not json {{{' \| guard-bash.py` → exit 2, deny message |
| Existing rules unchanged (force-push, `aws`, `sst deploy`, secrets) | **Not fully** | The pre-existing `aws` deny rule has the same class of gap (finding 1) |

## Blocking findings

1. **`invai-docs/team/hooks/guard-bash.py:87-90, 163-190` — `npx` (and any other unrecognized wrapper command) is not stripped as a prefix, so every lesson rule and the pre-existing `aws` deny rule can be bypassed by simply prefixing the real command with `npx`.**

   `PREFIX_CMDS` (line 87) and `_strip_prefix()` (line 163) only know about `sudo, env, command, builtin, exec, nohup, time, nice, caffeinate` plus shell keywords. `npx` isn't in that set and isn't handled by any of the special-cased heads (`SHELLS`, `eval`, `find`, the python/node/perl regex) in `simple_commands()`. When the guard sees `["npx", "git", "push", "origin", "main"]`, `_strip_prefix` returns the list unchanged, so `head = "npx"`, not `"git"` — `git_rules()` is never called, and `lesson_rules()` finds nothing.

   Reproduced by piping this JSON to `guard-bash.py` with `agent_type: "backend-engineer"` (a role that is not the main session and not tech-lead):
   ```
   {"tool_name":"Bash","tool_input":{"command":"npx git push origin main"},"agent_type":"backend-engineer"}
   ```
   Result: **exit 0, no stderr, no ask JSON — the push is silently allowed.** The same bare command (`git push origin main`, no `npx`) is correctly denied with `"only the tech lead pushes, after the wave gate ..."`.

   Same technique, same result (all ALLOW where the bare command DENYs or ASKs):
   - `npx git add -A` — bypasses R4 (bare `git add -A` denies with "stage only your own paths...")
   - `npx git stash` — bypasses R2 (bare `git stash` denies)
   - `npx pkill -f node` — bypasses R3 (bare `pkill -f node` denies)
   - `npx pnpm install`, `npx npm install`, `npx -y pnpm add lodash`, `corepack pnpm install` — bypass R5 (bare forms correctly return `ask`)
   - `npx aws s3 rm s3://bucket/key` — bypasses the **pre-existing** `aws` deny rule (`BASH_RULES` line 73). That rule is anchored with `^\s*(?:sudo\s+|env\s+|command\s+|exec\s+|\w+=\S+\s+)*(?:\S*/)?aws\s+`, so it only matches when the segment *starts* with one of those exact prefixes or with `aws` itself; `npx aws ...` doesn't start with any alternative in the group, so the anchored match fails at position 0 and `re.search` (which can't slide past `^`) never fires. Bare `aws s3 ls` is correctly denied with `"real AWS accounts are touched only by the owner"`.

   By contrast, `npx git push --force origin main` **is** still caught, because the force-push rule is a plain substring `re.search` on the raw segment text (no `^` anchor, matches `\bgit` anywhere) — so this specific class of bug is confined to the rules that walk parsed shell words (`lesson_rules`/`git_rules`/`kill_rules`) and to the one anchored `BASH_RULES` pattern (`aws`), not to the rest of `BASH_RULES`.

   **Why this matters:** R1 (only the tech lead pushes after the gate) is the direct fix for the wave-2 and wave-8 incidents this card exists to close, and it is defeated by a single, completely ordinary word — `npx` is a standard part of the Node/pnpm toolchain that any agent could type without any intent to evade anything, let alone one that does. The `aws` bypass is worse: CLAUDE.md lists "aws commands" as one of the handful of things the guard is described as blocking outright ("It also asks the owner before any MCP tool that sends or publishes... blocks force-pushes, tag pushes, deploys, `aws` commands and secret changes"), and this reproduction shows a real AWS account action going through with zero owner visibility.

   **This is not one of the disclosed "known limits."** The report's "Known gaps" section names shell functions/aliases defined earlier, `source`, base64+eval, and list-form subprocess calls built from variables — none of which is what's happening here. This is a plain, one-word, extremely common invocation that the guard's own sibling file already knows to handle: `invai-docs/team/hooks/invai_hooklib.py:220` (`track-verify.py`'s command parser, built by the same author for T-16-1) explicitly lists `"npx"` in its own `_strip_prefixes()`. The omission from `guard-bash.py` looks like a straightforward miss, not a scoped-out risk, and the 112-case adversarial table has zero `npx`/wrapper-prefix cases to have caught it (`grep -c npx test_guard.py` → `0`).

   **Suggested fix (for platform-sre, not mine to make):** add `npx`, `pnpm dlx`, `yarn dlx`, `bunx`, `corepack` (and ideally any single unknown word followed by a recognized subcommand name that matches a package binary pattern) to the words `_strip_prefix()` unwraps — mirroring what `invai_hooklib._strip_prefixes()` already does — and add `npx git push`, `npx pnpm install`, `npx aws ...`, `npx pkill ...` to the adversarial table so a regression is caught. Given the anchored `aws` rule has the identical root cause, consider whether `BASH_RULES`' anchored patterns should also run through the same word-level parser used for the lesson rules, rather than a separate anchored regex, so the two don't silently diverge again.

## Non-blocking observations

- **`agent_type` trust boundary verified, no bug found.** `agent_type` is set by the Claude Code harness from the actual subagent/session, not from anything inside `tool_input`, and T-16-1's report independently confirmed this empirically (a subagent's Bash calls carry `agent_id`+`agent_type`; the main session's carry neither). I probed the guard's own handling of edge values and all deny correctly: missing (`None`) → allow (main session, correct), `""` → deny, `"Tech-Lead"` (wrong case) → deny, `"tech-lead "` (trailing space) → deny. The one thing the guard cannot and should not try to police: if some other part of the harness lets an arbitrary agent spawn a nested agent with `subagent_type: "tech-lead"`, that nested agent's Bash calls will legitimately carry `agent_type: "tech-lead"` and push will be allowed, because it *is* the tech-lead role at that point, not a spoof. That's a process/permissions question for the tech lead and operating-system.md, not a defect in this guard.
- The `base64 | eval` and script-file bypasses I tried (e.g. `eval $(echo <b64> | base64 -d)`) do get through, as the report discloses; I didn't chase these further since they're explicitly named as accepted, non-denylistable limits.
- All of the explicitly-carved-out allow cases I re-checked behave correctly: `git stash list`, `git restore --staged <file>`, `kill 12345`, `kill $(lsof -ti :3101)`, `git add -p <file>`, `git checkout <branch>`, `git push origin main` from the main session (no `agent_type`), `db:reset` from `qa-engineer` and the main session.
- Malformed input (`not json {{{`, empty stdin, `tool_input` as a list, non-string `command`) all fail closed (exit 2, deny) — confirmed, including the specific bug the report says it fixed (non-string `command`/`tool_input` used to exit 1, a non-blocking hook error; now denies).

## Checks
- [x] Only owned paths changed (`git -C invai-docs diff --stat` for `59f8d31`: `guard-bash.py`, `tests/test_guard.py`, `waves/16/reports/T-16-2.md` — matches the card's owned paths)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scanned the diff, found no `.skip`/loosened assertions/mocks of the unit under test
- [ ] The control itself (this is an `auth` co-review): **not fully sound** — see finding 1. A denylist-based guard will always have edges, but this one is reachable with a single common word, not an exotic technique, and directly undermines the card's headline acceptance criteria (R1, R3, R4, R5) plus a pre-existing rule.
- [x] Decisions: none needed for this round; the fix belongs in guard-bash.py itself, not a new decision

## Recommendation
Send finding 1 back to platform-sre (owner of `guard-bash.py`) as a required fix before this card is pushed: strip `npx`/`pnpm dlx`/`yarn dlx`/`bunx`/`corepack` the same way `invai_hooklib.py` already does, re-run the adversarial suite with `npx`-prefixed cases added for R1, R3, R4, R5 and the `aws` rule, and I will re-verify with the same reproductions before approving.
