---
name: feedback-never-pkill
description: never use pkill/killall to stop your own dev processes, even filtered by a distinctive string — use kill <pid> from lsof
metadata:
  type: feedback
---

The agent brief's hard rules say "Never: ... pkill/killall". While swapping API ports mid-card (see [[feedback-dev-csp-needs-build-preview]]) I ran `pkill -f "PORT=3142"` to stop my own `tsx watch` process instead of finding its PID with `lsof -iTCP:3142 -sTCP:LISTEN` and `kill <pid>`. It happened to only match my own process, but it's still the forbidden command.

**Why:** in a shared machine with several agents' node/tsx processes running, `pkill`/`killall` can match more broadly than intended and kill another agent's process; the rule is absolute, not "unless your filter looks safe".

**How to apply:** always stop a process you started with `lsof -iTCP:<port> -sTCP:LISTEN` to get its PID, then `kill <pid>`. Never use `pkill`, `killall`, or any pattern-matching kill, even against a port number or env var string you believe is unique to your own process.
