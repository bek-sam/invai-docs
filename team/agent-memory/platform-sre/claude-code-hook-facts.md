---
name: claude-code-hook-facts
description: Empirically verified Claude Code 2.1.283 hook behaviour (inputs, feedback channels, Stop blocking, fail-open exit codes) and how to test hooks headless
metadata:
  type: reference
---

Verified 2026-09-26 with headless `claude -p --model haiku` in a scratch folder with its own `.claude/settings.json` (T-16-1). Prompt via stdin, because `--allowedTools` is variadic and swallows a trailing prompt.

- Bash `PostToolUse` has no exit code. A non-zero exit fires `PostToolUseFailure` instead (with `error`). `duration_ms` is present.
- Subagent calls carry `agent_id` + `agent_type`; main-session calls carry neither. SubagentStop has `agent_id`, `stop_hook_active`, `agent_transcript_path`.
- Hook `cwd` follows the shell's `cd`.
- PostToolUse feedback reaches the model via exit 2 + stderr, via JSON `decision:block` + `reason`, or via `additionalContext`. Stop `decision:block` adds one turn ("Stop hook feedback: …"), and the next Stop has `stop_hook_active: true`.
- A hook that exits 1 (a crash) is a non-blocking error, so the call goes through. PreToolUse guards must catch every exception and exit 2. The old guard failed open on a non-string `command`.
- The live guard regex-matches raw text, so a Bash command that merely contains `git push --force` (even in a JSON probe) is blocked. Put probe payloads in files.
- `invai-docs/team/sync.sh` copies `hooks/*` flat. A `hooks/tests/` folder or a `__pycache__` breaks restore (`chmod` is skipped), and backup's `rm -rf hooks` deletes the tests. Run hook tests with `python3 -B`.

Related: [[wave16-hooks]]
