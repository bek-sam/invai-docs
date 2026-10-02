---
name: guard-hook-review-pattern
description: Reviewing changes to team/hooks/guard-bash.py or guard-paths.py (T-20-4): differential harness old-vs-new, prove new tests fail on the previous commit, scan for old-deny→new-allow, probe inputs kept in files
metadata:
  type: feedback
---

For a guard-hook change, run a differential harness (every case through the pre-change guard and the new one, via stdin JSON `{"tool_name":"Bash","tool_input":{"command":…},"agent_type":…}`), and treat every old-deny→new-allow as a finding unless the card names it as an intended allow.

**Why:** T-20-4 r1: the segment split intentionally allowed lesson shapes but also let a lister feed a kill through a file (`pgrep > /tmp/p; kill $(cat /tmp/p)`), which only the old-vs-new diff surfaced; the author's suite was green. In r2 the same harness plus 20 variants of the fixed rule (quoted `$(cat)`, `$(<file)`, `xargs -a`, `tee`, `eval`, subshell, lister after kill, `/bin/kill`, env prefix) confirmed the fix with zero regressions.

**How to apply:** keep `harness.py` and `guard-bash-old.py` in the scratchpad; extract the previous commit's guard with `git show <sha>:team/hooks/guard-bash.py` to a scratch tree and run the author's pytest there so the new subtests fail. Put commands containing blocked text (`git push -f`, `pkill`) inside script files, never inline in Bash (the live guard scans Bash text). `uv run --no-project --with pytest python3 -B -m pytest … -p no:cacheprovider` is the working pytest form on this machine (system python3 has no pytest). Pre-existing gaps worth re-noting each round: `lsof -c <name>` counts as trusted lsof; a relay split across two Bash calls is invisible to a per-command hook.
