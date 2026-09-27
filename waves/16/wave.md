# Wave 16: the team harness catches mistakes as they happen

- Goal:
  - Lint and type errors surface right after the edit that caused them, not at the end of a card.
  - An agent can't finish a card with unverified code edits without being told, once.
  - The mistakes that keep recurring in `team/lessons.md` (git stash, pushing, pkill, `git add -A`, `pnpm install`) are blocked by the guard hook, not only written in prompts.
  - Builders keep memory across cards, so a lesson learned in one card reaches the next.
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push; only the tech lead pushes after the gate."**
- Runs alongside wave 17. This wave touches only team files.

## Analysis (tech lead, 2026-09-26)
- **Late errors:** agents learn about type and lint errors only when they run the full `pnpm typecheck && pnpm lint && pnpm test`, often after many edits. Fix: a PostToolUse hook on Edit/Write/MultiEdit that lints the edited file (Biome or Ruff), plus a fast typecheck if the repo's typecheck runs in under about 8 seconds (measured), and hands the errors back to the model.
- **Unverified "done":** decision 0011 cut reviewer re-runs, so a builder that skips its checks is caught only at review or the gate. Fix: a tracker (PostToolUse on Edit/Write/Bash) records which code repos each agent edited and which verification commands succeeded afterwards. A Stop/SubagentStop hook blocks the first stop while an edited repo has no successful `typecheck`, `lint` and `test` run after its last edit, and names the commands. `stop_hook_active` lets the second stop through, so it can't loop, and the agent must report the gap honestly.
- **Repeat mistakes:** 8 of the 23 lessons are mechanically checkable, and at least 3 repeated after being written down (git stash in waves 4 and 8; pushing in waves 2 and 8). Hook input carries `agent_type` for subagents, so the guard can deny `git push` for every agent except `tech-lead` and the main session.
- **Memory never written:** every role has `memory: project`, but `.claude/agent-memory/` holds only two empty folders. Nothing in the brief or the playbooks asks an agent to save a memory, and the 8-line reply budget pushes them to finish fast. Fix: a "save what you learned" step in `verify-and-report` and `independent-review`; each role's `MEMORY.md` seeded with the lessons that apply to it (Claude Code auto-loads the first 200 lines); and `sync.sh` backs up agent memory.

## Cards
| Card | Owner | Flags | Model |
|---|---|---|---|
| T-16-1 Fast check hook and verification gate (PostToolUse + Stop/SubagentStop) | platform-sre | — | opus |
| T-16-2 Guard hook: block the recurring lessons, with adversarial tests | platform-sre | auth (guard) | opus |
| T-16-3 Agent memory: playbook steps, seeds per role, backup | tech-lead | — | (tech lead) |

## Ownership
| Card | Owns (exclusive) |
|---|---|
| T-16-1 | new `invai-docs/team/hooks/post-edit-check.py`, `track-verify.py`, `verify-gate.py`, `invai-docs/team/hooks/tests/**`, `invai-docs/team/settings.json` |
| T-16-2 | `invai-docs/team/hooks/guard-bash.py`, `invai-docs/team/hooks/tests/test_guard.py` |
| T-16-3 | `invai-docs/team/skills/verify-and-report/**`, `invai-docs/team/skills/independent-review/**`, `invai-docs/team/agent-brief.md`, `invai-docs/team/sync.sh`, `.claude/agent-memory/**` (seeds) |

- Same agent runs T-16-1 then T-16-2.
- **Nobody installs into the live `.claude/` except the tech lead, at the gate** (`bash invai-docs/team/sync.sh restore`). A broken Stop hook would block every running agent.

## Reviews
- T-16-1, T-16-2: `reviewer` primary (sonnet), `security-reviewer` co-review (tries to bypass the guard and to make the gate loop or block wrongly).
- T-16-3: `reviewer`.

## Grants
(none yet)
- 2026-09-26: T-16-1 also owns the new shared `invai-docs/team/hooks/invai_hooklib.py`. `sync.sh` copies `hooks/*.py` since `1c14f5d`, so it is installed with the hooks.
- 2026-09-26: T-16-2 round 2 also owns a new `invai-docs/team/hooks/guard-memory-path.py` (PreToolUse on Write|Edit|MultiEdit: deny writes into any `.claude/agent-memory/` outside `$CLAUDE_PROJECT_DIR/.claude/agent-memory/`), its tests, and its entry in `invai-docs/team/settings.json`. Source: lesson row 2026-09-26 "agent memory landed in subfolder .claude dirs".
