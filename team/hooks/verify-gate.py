#!/usr/bin/env python3
"""Stop / SubagentStop gate: don't finish with unverified code edits.

If this agent (session_id + agent_id, "main" for the main session) edited a code repo after its last
successful typecheck, lint and test (plus build for web and floor; lint and test for imaging;
typecheck and lint for infra), the first stop is blocked once with the exact commands. The stop is
allowed when:
- stop_hook_active is true (we already blocked this stop sequence), or
- the gate already blocked for the same edit state (no new edits since), so a resumed agent that
  reported its failure honestly isn't blocked again, or
- nothing is pending (read-only agents and docs-only edits never have pending repos).

Fails open: a crash or unreadable input allows the stop. A broken gate must never trap every agent.
"""
import json
import os
import sys


def main():
    data = json.load(sys.stdin)
    if data.get("stop_hook_active"):
        return
    sys.dont_write_bytecode = True  # no __pycache__ next to the hooks (sync.sh copies hooks/* flat)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import invai_hooklib as h

    sf = h.state_file(data.get("session_id"), data.get("agent_id"))
    if not sf.exists():
        return
    state = h.read_state(sf)
    pending = h.pending_checks(state)
    if not pending:
        return
    edit_mark = max(state["repos"][root].get("edited_at", 0) for root, _k, _m in pending)
    if state.get("gate_blocked_for") == edit_mark:
        return

    def remember(s):
        s["gate_blocked_for"] = edit_mark

    h.update_state(sf, remember)
    lines = ["You edited code after its last successful checks. Before you finish, run:"]
    for root, kind, missing in pending:
        cmds = " && ".join(h.check_command(root, kind, c) for c in missing)
        lines.append(f"- {os.path.basename(root)}: cd {root} && {cmds}")
    lines.append("If you can't make them pass, stop and report the failure honestly.")
    print(json.dumps({"decision": "block", "reason": "\n".join(lines)}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
