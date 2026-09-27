#!/usr/bin/env python3
"""PostToolUse tracker for the InvAI verification gate (verify-gate.py).

Per session_id + agent_id ("main" for the main session) it records:
- Edit/Write/MultiEdit/NotebookEdit: which code repo or worktree was edited, and when (docs and images
  are ignored);
- Bash: which full-repo checks succeeded afterwards (pnpm typecheck/lint/test/build, their
  node_modules/.bin forms, tsc, biome check ., vitest run, vite build; imaging uv run ruff check . and
  uv run pytest), including `cd <repo> &&`, `-C`/`--dir` and `&&` chains. A failed command fires
  PostToolUseFailure, not PostToolUse, so it is never counted. A check counts only if it started after
  the edit (start = now - duration_ms).

State: .claude/state/verify__<session>__<agent>.json, written atomically under a lock; files older
than 2 days are pruned. Fails open: this hook only keeps notes, so any error exits 0.
"""
import json
import os
import sys
import time


def main():
    data = json.load(sys.stdin)
    if data.get("hook_event_name") not in (None, "PostToolUse"):
        return
    sys.dont_write_bytecode = True  # no __pycache__ next to the hooks (sync.sh copies hooks/* flat)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import invai_hooklib as h

    tool = data.get("tool_name", "")
    ti = data.get("tool_input") or {}
    cwd = data.get("cwd") or os.getcwd()
    sf = h.state_file(data.get("session_id"), data.get("agent_id"))
    now = time.time()

    if tool in ("Edit", "Write", "MultiEdit", "NotebookEdit"):
        path = ti.get("file_path") or ti.get("notebook_path") or ""
        if not path or os.path.splitext(path)[1].lower() in h.DOC_EXT:
            return
        repo = h.find_repo(path if os.path.isabs(path) else os.path.join(cwd, path))
        if not repo:
            return
        root, kind = repo

        def mark_edit(state):
            r = state["repos"].setdefault(root, {"kind": kind, "ok": {}})
            r["kind"] = kind
            r["edited_at"] = now
            r.setdefault("files", [])
            if path not in r["files"]:
                r["files"] = (r["files"] + [path])[-20:]

        h.update_state(sf, mark_edit)
        return

    if tool == "Bash":
        resp = data.get("tool_response") or {}
        if ti.get("run_in_background") or (isinstance(resp, dict) and (resp.get("backgroundTaskId") or resp.get("interrupted"))):
            return
        if not sf.exists():
            return  # nothing edited yet: nothing to verify
        output = ""
        if isinstance(resp, dict):
            output = f"{resp.get('stdout', '')}\n{resp.get('stderr', '')}"
        found = h.parse_verifications(ti.get("command", ""), cwd, output)
        if not found:
            return
        started = now - float(data.get("duration_ms") or 0) / 1000.0

        def mark_ok(state):
            for root, _kind, check in found:
                r = state["repos"].get(root)
                if r is not None:
                    r["ok"][check] = max(r["ok"].get(check, 0), started)

        h.update_state(sf, mark_ok)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
