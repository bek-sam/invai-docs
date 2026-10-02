---
name: concurrent-writer-shared-paths
description: another process wrote sibling files into my owned scripts/gate/** mid-task on T-23-6; verify + re-verify before committing
metadata:
  type: feedback
---

While building `invai-infra/scripts/gate.sh` + `scripts/gate/lib.sh` for T-23-6, another process
(not me, source unidentified — no card mentioned a second concurrent platform-sre on this card)
repeatedly rewrote `scripts/gate/lib.sh` and added sibling files (`refuse.sh`, `repo-check.sh`,
`stamp.sh`, `golden-path.sh`) into the same directory, at least 4 times over ~10 minutes, with an
incompatible design (my `gate.sh` calls functions that design didn't define, so sourcing its
`lib.sh` would have broken my script).

**Why:** a system reminder confirmed this is expected to happen sometimes ("that's usually
deliberate... don't revert it yourself") — multiple agents can land writes in the same shared,
non-worktree filesystem. Silently trusting the file I last wrote is not safe; it can be
clobbered again after I "finish".

**How to apply:** when a directory I own is shared risk (another agent may reuse it, e.g. the
card said "T-23-7 may reuse your scripts/gate/**"), re-`Read`/checksum my own files immediately
before the final `git add`+commit, not just after writing them. Stage and commit only the exact
files I authored and verified (`git add <explicit paths>`, never the whole directory), leave any
foreign untracked files untouched, and flag the collision explicitly in the report so the tech
lead reconciles the two designs before anyone builds further on the shared path.
