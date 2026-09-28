#!/usr/bin/env python3
"""PreToolUse on Write|Edit|MultiEdit|NotebookEdit: keep the tech lead and the reviewer to their own paths (B-47).

The owner's rules say the tech lead plans and doesn't write code, and reviewers are read-only on code
(team/operating-system.md, lessons 2026-09-24). This hook enforces that for the file tools:

- tech-lead: invai-docs/{waves (not waves/*/reviews), team, research, decisions}/**, invai-docs/owner-inbox.md,
  CLAUDE.md, .claude/{agents,skills}/**, .claude/agent-memory/tech-lead/**, invai-docs/.claude/agent-memory/tech-lead/**
- reviewer: invai-docs/waves/*/reviews/**, .claude/agent-memory/reviewer/**
- every other agent type: unaffected (a later card adds builder roles).

The agent is known from `agent_type`, which Claude Code sends on PreToolUse input for subagent calls and omits
for the main session (verified headless on 2.1.283, T-16-1). With no agent_type the write is allowed and one
line (time, caller, path; never content) goes to invai-docs/team/state/guard-paths.log, so a Claude Code change
that stops sending it shows up there.

Paths are resolved (relative to the hook's cwd, `..` and symlinks followed, case folded for macOS) before the
check. For a restricted agent, anything unreadable fails closed (exit 2). Only the file tools are covered: a
shell redirect is Bash, which guard-bash.py handles.
"""
import json
import os
import sys
import time
from pathlib import Path

RESTRICTED = ("tech-lead", "reviewer")
TECH_LEAD_TREES = ("invai-docs/waves", "invai-docs/team", "invai-docs/research", "invai-docs/decisions",
                   ".claude/agents", ".claude/skills", ".claude/agent-memory/tech-lead",
                   "invai-docs/.claude/agent-memory/tech-lead")
TECH_LEAD_FILES = ("invai-docs/owner-inbox.md", "CLAUDE.md")
REVIEWER_TREES = (".claude/agent-memory/reviewer",)
ALLOWED_TEXT = {
    "tech-lead": ("invai-docs/waves/** (not waves/*/reviews/**), invai-docs/team/**, invai-docs/research/**, "
                  "invai-docs/decisions/**, invai-docs/owner-inbox.md, CLAUDE.md, .claude/agents/**, "
                  ".claude/skills/**, .claude/agent-memory/tech-lead/**, invai-docs/.claude/agent-memory/tech-lead/**"),
    "reviewer": "invai-docs/waves/<n>/reviews/**, .claude/agent-memory/reviewer/**",
}
LOG_MAX_BYTES = 512 * 1024
_unrestricted = False  # set once the caller is known not to be a restricted agent


def deny(msg):
    print(f"Blocked by InvAI team rules: {msg}", file=sys.stderr)
    sys.exit(2)


def workspace_root():
    """The invai/ folder: CLAUDE_PROJECT_DIR or its nearest parent holding invai-docs/, else from this file's place."""
    starts = []
    if os.environ.get("CLAUDE_PROJECT_DIR"):
        starts.append(Path(os.path.realpath(os.environ["CLAUDE_PROJECT_DIR"])))
    here = Path(os.path.realpath(__file__)).parent
    if here.name == "hooks" and here.parent.name == ".claude":
        starts.append(here.parent.parent)
    for s in starts:
        for d in (s, *s.parents):
            if (d / "invai-docs").is_dir():
                return d
    return None


def role_of(agent_type):
    """'tech-lead' / 'reviewer' for those agents (also a plugin-prefixed 'x:tech-lead'), else None."""
    name = agent_type.strip().casefold().rsplit(":", 1)[-1]
    return name if name in RESTRICTED else None


def target_path(tool_input):
    p = tool_input.get("notebook_path") if "notebook_path" in tool_input else tool_input.get("file_path")
    return p if isinstance(p, str) and p.strip() else None


def resolve(path, cwd):
    if path.startswith("~"):
        return None  # the tool may or may not expand it; don't guess
    base = cwd if isinstance(cwd, str) and os.path.isabs(cwd) else os.getcwd()
    return os.path.realpath(path if os.path.isabs(path) else os.path.join(base, path))


def rel_parts(full, root):
    """Path parts of `full` below `root` (case folded), or None when it's outside the workspace."""
    f, r = full.casefold(), str(root).casefold()
    if not f.startswith(r.rstrip("/") + "/"):
        return None
    return [p for p in f[len(r.rstrip("/")) + 1:].split("/") if p]


def under(parts, tree):
    t = tree.casefold().split("/")
    return len(parts) > len(t) and parts[:len(t)] == t


def allowed(role, parts):
    if parts is None:
        return False
    if role == "reviewer":
        if len(parts) > 4 and parts[:2] == ["invai-docs", "waves"] and parts[3] == "reviews":
            return True
        return any(under(parts, t) for t in REVIEWER_TREES)
    # tech-lead
    if under(parts, "invai-docs/waves") and "reviews" in parts[2:-1]:
        return False
    if "/".join(parts) in {f.casefold() for f in TECH_LEAD_FILES}:
        return True
    return any(under(parts, t) for t in TECH_LEAD_TREES)


def log_unknown(root, data, path):
    try:
        log = Path(os.environ.get("INVAI_GUARD_PATHS_LOG") or (root / "invai-docs/team/state/guard-paths.log"))
        log.parent.mkdir(parents=True, exist_ok=True)
        gi = log.parent / ".gitignore"
        if not gi.exists():
            gi.write_text("*\n")
        if log.exists() and log.stat().st_size > LOG_MAX_BYTES:
            os.replace(log, str(log) + ".1")
        agent_id = data.get("agent_id")
        caller = f"no-agent-type agent_id={agent_id}" if agent_id else "main"
        clean = str(path).replace("\n", " ").replace("\r", " ")[:300]
        with open(log, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S%z')}\t{caller}\t{data.get('tool_name')}\t{clean}\n")
    except Exception:
        pass  # the log is a signal, never a reason to block


def main():
    global _unrestricted
    try:
        data = json.load(sys.stdin)
        if not isinstance(data, dict):
            raise ValueError
        tool_input = data.get("tool_input") or {}
        agent_type = data.get("agent_type")
        if not isinstance(tool_input, dict) or not isinstance(agent_type, (str, type(None))):
            raise ValueError
    except Exception:
        deny("the path guard couldn't read its input")

    if agent_type is None or not agent_type.strip():
        _unrestricted = True
        root = workspace_root()
        if root is not None:
            log_unknown(root, data, tool_input.get("file_path") or tool_input.get("notebook_path"))
        return
    role = role_of(agent_type)
    if role is None:
        _unrestricted = True
        return  # other roles: out of this card's scope

    howto = (f"The {role} writes only to: {ALLOWED_TEXT[role]}. "
             f"For anything else, write a card for the owner of that path (tech lead: waves/<n>/T-*.md).")
    path = target_path(tool_input)
    if path is None:
        deny(f"the path guard couldn't find the file path. {howto}")
    root = workspace_root()
    if root is None:
        deny(f"the path guard couldn't find the invai/ workspace. {howto}")
    full = resolve(path, data.get("cwd"))
    if full is None:
        deny(f"write {path!r} as an absolute path. {howto}")
    try:
        if os.path.isfile(full) and os.stat(full).st_nlink > 1:
            deny(f"{full} is a hard link, so the guard can't tell where it really points. {howto}")
    except OSError:
        pass
    if not allowed(role, rel_parts(full, root)):
        deny(f"{full} is outside the {role}'s paths. {howto}")


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:
        if not _unrestricted:
            deny("the path guard hit an error; the tech lead and reviewer fail closed")
    sys.exit(0)
