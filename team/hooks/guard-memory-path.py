#!/usr/bin/env python3
"""PreToolUse on Write|Edit|MultiEdit: keep agent memory where Claude Code loads it.

Project agent memory is loaded only from $CLAUDE_PROJECT_DIR/.claude/agent-memory/<role>/. An agent started
from a subfolder writes its memory into that subfolder's .claude/ (21 files landed in invai-docs/.claude/ and
waves/1x/.claude/ in waves 16/17, lessons.md 2026-09-26), where no later run reads it. This hook denies such a
write and gives the right absolute path.

A nudge, not a security control: it fails OPEN (malformed input, no CLAUDE_PROJECT_DIR, any error -> allow),
unlike guard-bash.py, which fails closed.
"""
import json
import os
import sys

MARK = "/.claude/agent-memory/"


def main():
    data = json.load(sys.stdin)
    ti = data.get("tool_input") or {}
    path = ti.get("file_path")
    if not isinstance(path, str) or MARK not in path.replace(os.sep, "/"):
        return
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if not project:
        return
    cwd = data.get("cwd") or os.getcwd()
    full = os.path.realpath(path if os.path.isabs(path) else os.path.join(cwd, path))
    home = os.path.realpath(os.path.join(project, ".claude", "agent-memory"))
    if full == home or full.startswith(home + os.sep):
        return
    rest = full.split(MARK, 1)[1] if MARK in full else path.split(MARK, 1)[1]
    right = os.path.join(home, rest)
    print(f"Agent memory must live in {home}/, the only place Claude Code loads it from. "
          f"Write this file to {right} instead (lessons.md 2026-09-26: memory in subfolder .claude dirs is "
          f"never loaded).", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        pass
    sys.exit(0)
