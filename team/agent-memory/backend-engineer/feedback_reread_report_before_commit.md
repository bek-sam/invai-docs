---
name: feedback-reread-report-before-commit
description: a file wiped mid-task in a shared repo can mean the tech lead already decided and acted (git restore + a note in your own report file), not just an accident — re-read the report before redoing lost work.
metadata:
  type: feedback
---

On T-P3-4, my uncommitted test edit to `finance-service.test.ts` disappeared mid-session. I
assumed it was collateral damage from another agent's git operation in the shared (non-worktree)
repo, and re-added + committed it without first re-reading my own report file at
`invai-docs/waves/P3/reports/T-P3-4.md` — which a system note had just told me changed on disk.
The tech lead had actually `git restore`-ed that exact file and written the decision ("pinning
test dropped, tracked as backlog B-242 next wave") into my report file while I was mid-task. I
had to revert my re-commit with a second commit once I caught it.

**Why:** the harness surfaces "this file changed on disk since you last read it" as a neutral
note, not a warning — it doesn't say *who* changed it or *why*. In this team's shared-tree setup,
the tech lead can and does intervene on a card's owned files directly and leaves the decision in
the card's own report file, which is the first place to check before concluding "something
corrupted my edit."

**How to apply:** if a file you just edited (uncommitted) goes missing or reverts in a shared
repo, before redoing the work: (1) check `git log -1` / `git status` for anything already
committed on top, and (2) re-read your own report file in full — a tech lead decision recorded
there supersedes your in-progress plan. Only re-apply the edit if neither explains the change.
