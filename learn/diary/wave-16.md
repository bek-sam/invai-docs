# Wave 16 — the team harness catches mistakes as they happen

**Dates:** 2026-09-26 to 27. Notably, this wave is about the *team itself*, not the
product — it builds the hooks and memory system module 10 describes.

## What was built
- **T-16-1** Fast check hook and verification gate (platform-sre): `PostToolUse` and
  `Stop`/`SubagentStop` hooks that run quick checks right after an edit, and a gate before
  an agent is allowed to report done.
- **T-16-2** Guard hook: block the recurring lessons, with adversarial tests (platform-sre):
  the `guard-bash.py` hook that blocks force-pushes, tag pushes, deploys, `aws` commands
  and secret changes — built specifically to stop the mistakes `team/lessons.md` had
  already recorded, and tested by trying to break it.
- **T-16-3** Agent memory: playbook steps, seeds per role, backup (tech lead): the
  `.claude/agent-memory/<role>/` system this very course's memory file lives in.

## Why
By wave 15 the lessons log already had over a dozen entries — real mistakes, written
down, with a rule attached. But a rule written in a markdown file only works if every
agent reads and remembers it every time. Wave 16 is the team deciding to stop relying on
that, and instead build mechanical enforcement: hooks that physically block a dangerous
command, and a memory system that survives between agent runs instead of resetting with
every new context window.

## What went wrong
- The brand-new guard hook denied the tech lead's own memory-seeding script, because the
  command's heredoc text happened to *quote* a lesson about workflow runs — the guard
  matches patterns anywhere in the command text, heredoc bodies included, and it fails
  safe by design. The fix was to put the quoted text in a file and run the file, not to
  weaken the guard.
- Agents wrote 21 memory files into the wrong place — `invai-docs/.claude/`,
  `waves/16/.claude/` and `waves/17/.claude/` — because project agent memory resolves
  from whatever folder the agent's shell happened to start in, and the tech lead had
  started agents from inside `invai-docs` subfolders instead of the `invai/` root. The
  live `.claude/agent-memory/` stayed empty the whole time, making memory look unused
  when it was actually just being written somewhere nobody would ever read it again.
- After the guard was installed, a plain push to `main` got denied because the *same
  command line* also ran `tr -d` later in a loop — the push rule scanned the whole joined
  command, and `tr`'s `-d` flag read as a ref-deletion flag.

## What the team learned
- A security guard that fails closed on ambiguous input is working as designed, even when
  it's inconvenient — the fix for a false positive is to change *how you run the command*
  (isolate it, put text in a file), never to weaken the guard itself.
- "Start every agent from the `invai/` root" became a hard rule the moment memory got
  scattered into three wrong locations — a `PreToolUse` hook now denies memory writes
  outside the real project memory path as a backstop, because a written instruction alone
  had already failed twice (wave 16, then again wave 18).
- Scanning a whole joined shell command for a dangerous pattern is safer than scanning
  only the first word, but it also means unrelated flags in later parts of the same
  command line can trigger it — this becomes B-116 (a segment-aware guard), fixed properly
  only much later, in wave P7.

## Files to look at
- `invai-docs/team/hooks/post-edit-check.py`, `track-verify.py`, `verify-gate.py` — T-16-1.
- `invai-docs/team/hooks/guard-bash.py`, `invai-docs/team/hooks/tests/test_guard.py` — the
  guard and its adversarial tests (T-16-2).
- `.claude/agent-memory/` — where memory is actually supposed to live (T-16-3).
- `invai-docs/team/lessons.md` (2026-09-26/27, "Wave 16" and "Wave 16 install" rows).
