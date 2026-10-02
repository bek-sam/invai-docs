---
name: git-apply-cached-partial-staging
description: How to stage only my own hunk in a shared file (owner-inbox.md) another agent also edited in the working tree
metadata:
  type: feedback
---

When asked to commit only my own change to a shared doc (e.g. `owner-inbox.md`) that another agent has
also modified in the working tree (e.g. tech-lead appending a new OI-N entry), don't `git add` the whole
file — that stages the other agent's uncommitted work too, which `respect-ownership` forbids.

Instead: `git diff -- <file> > /tmp/full.diff`, extract just my hunk (by line range) into its own patch
file, then `git apply --cached /tmp/my-hunk.diff`. This stages only that hunk against the index while
leaving the working tree (with the other agent's edit) untouched. Verify with
`git diff --cached -- <file>` before committing.

**Why:** T-21-1 round 2 (2026-09-28) — product-manager review asked me to fix OI-19's deadline in
owner-inbox.md, but the tech lead had already appended OI-20 to the same file in the working tree by the
time I got to it. Using `git add owner-inbox.md` would have committed OI-20 under my authorship, violating
"MUST NOT stage or commit other agents' work in progress" ([[respect-ownership]]).

**How to apply:** Any time a task explicitly calls for `git apply --cached`-style partial staging of a
shared file, or whenever `git status` shows a file I need to touch already has unstaged changes I don't
own.
