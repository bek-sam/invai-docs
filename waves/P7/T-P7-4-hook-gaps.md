# T-P7-4: Guard reads scripts it runs, blocks `sst secret` and repo-setting API calls; Stop check counts shell edits (B-115, B-189)

| Field | Value |
|---|---|
| Wave | P7 |
| Scope ref | `always-in-scope: security` (team controls: B-115 gaps accepted in wave 16; B-189 guard gap found in the T-21-2 review) |
| Spec | backlog B-115, B-189; `waves/16/reports/T-16-1.md` (Known gaps), `waves/16/reports/T-16-2.md` (lines 63-96), `operating-system.md` "What enforces this" |
| Owner | platform-sre |
| Reviewer | reviewer (sonnet) |
| Co-reviewers | security-reviewer (fable) |
| Risk flags | auth (team controls) |
| Model | opus |
| Depends on | nothing |

## Owned paths (edit)
- `.claude/hooks/**` (live hooks; `.claude/settings.json` only if a new hook must be wired, say why)
- `invai-docs/team/hooks/**` (grant from the tech lead: the backed-up copy and the hook tests; after your change both copies of every `*.py` hook must be identical)

## Read-only paths
- Every code repo, `invai-docs/**` except the grant, `.claude/agents/**`, `.claude/skills/**`.

## Safety (read first)
The guard runs on every Bash call of every agent, including yours, and it fails closed: a syntax error denies every command for the whole team. Build and test in a temp copy (`/tmp/p7-4-hooks/`), run the full hook test suite and the sample-JSON smoke checks there, and only then copy into `.claude/hooks/`. Right after installing, run one harmless command (`git -C /Users/bekbolsun/invai/invai-docs status --short`) to prove the guard still allows normal work. Note: the live `guard-bash.py` is newer than the backup in `invai-docs/team/hooks/` (it has the T-23-6 push-stamp check and `.claude/hooks/tests/test_push_stamp.py`); start from the live one and bring the backup in line.

## Acceptance criteria
1. **Scripts the guard is asked to run.** When a Bash command runs a script file (`bash|sh|zsh <file>`, `source|. <file>`, `./<file>` or an absolute path to a `*.sh`), the guard reads that file (text, ≤ 256 KB, any path) and applies the same rules to its lines; a blocked command inside the script denies the call with the same message. A missing or unreadable file is allowed (the shell will fail anyway); binary files are skipped.
2. **Encoded commands.** `base64 -d|--decode` (or `openssl base64 -d`, `xxd -r`) piped into a shell, `eval` or `source`, and `eval "$(… base64 …)"`, are denied. Normal `base64` use (encoding, decoding to a file) stays allowed.
3. **B-189.** Denied: `sst secret set|remove|load` (any stage), `gh api` calls that write repo settings (`-X|--method PATCH|PUT|POST|DELETE` on `repos/<o>/<r>` itself, `…/branches/*/protection`, `…/rulesets`, `…/collaborators`, `…/hooks`, `…/environments`), `gh repo edit|delete|rename|archive`, `gh ruleset` writes. Read-only `gh api` GETs and `gh run list` stay allowed.
4. **Shell edits count as edits.** After a Bash command that writes inside a code repo (`sed -i`, `perl -i`, `>`/`>>` redirection or `tee` to a repo path, `git apply`, `patch`, `biome … --write`, `prettier --write`, `mv`/`cp` into a repo's `src/`), `track-verify.py` records the repo as edited by that agent, so `verify-gate.py` asks for checks at Stop exactly as for an Edit. Choose text-based detection or a `git status` fingerprint; say why, and how you avoid blaming one agent for another's edits in the shared tree.
5. **No regressions.** Every existing hook test passes, plus new tests for each case above (allowed and denied). The team's real commands still pass: the commands in this card, `pnpm gate …`, `git -C <repo> push origin main` (with its stamp rule), heredoc commit messages that merely mention a blocked verb (as today), `kill <pid>`.
6. **Docs.** The `guard-bash.py` docstring and `operating-system.md`'s "What enforces this" list match (you can't edit `operating-system.md`: give the tech lead the exact replacement lines in the report). The remaining known limits (runtime-built `bash -c "$(printf …)"`, aliases, node/python subprocesses) are listed in the docstring.

## Verification
- `cd /tmp/p7-4-hooks && python3 -B -m unittest discover -s tests 2>&1 | tail -n 15` (or the backup's tests dir; say which), before and after installing.
- Smoke: feed sample PreToolUse JSON for each AC1-AC3 case to the installed guard (`echo '<json>' | .claude/hooks/guard-bash.py; echo rc=$?`) and show rc 2 for denied, 0 for allowed. Put the deny samples in a file and pipe the file, so this session's own guard doesn't block the command text.
- `diff -q` each live hook against its backup copy: no differences.

## Out of scope
- Making the guard a sandbox (it stays a denylist for mistakes), the owned-paths hook, settings permissions, the AI spend breaker (T-P7-5).

## Rules
- Role file `.claude/agents/platform-sre.md`; run `threat-model-change` first (short result at the top of the report). Memory: `/Users/bekbolsun/invai/.claude/agent-memory/platform-sre/`.
- Other agents at the same time: qa-engineer, product-designer, ai-engineer, all running Bash through the guard you're changing. Install once, after tests pass; never leave the live guard half-edited.
- `.claude/` is not a git repo: commit only the backup copy in `invai-docs` (`git -C /Users/bekbolsun/invai/invai-docs add team/hooks/…`), attribution line at the end. **Don't push; only the tech lead pushes after the gate.**
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P7/reports/T-P7-4.md`, one line per milestone as you go. List any PID you start (stopped).

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
