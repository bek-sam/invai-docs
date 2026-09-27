---
name: two-memory-systems
description: InvAI has two separate, unrelated "agent memory" concepts — don't conflate them
metadata:
  type: project
---

InvAI wave 16 (T-16-3, 2026-09-26) added its own in-repo memory system: `invai-docs/team/agent-memory/<role>/MEMORY.md` seeds, installed into the live (non-git) `invai/.claude/agent-memory/<role>/MEMORY.md` via `bash invai-docs/team/sync.sh restore`, seeded with one-line lessons pulled from `invai-docs/team/lessons.md`. This is separate from my own Claude Agent SDK persistent memory store at `invai-docs/.claude/agent-memory/<role>/` (this file's location).

**Why:** the two live at similar-looking paths (`invai/.claude/agent-memory/` vs `invai-docs/.claude/agent-memory/`) and both call themselves "agent memory," but they're unrelated systems with different owners, formats and installation mechanisms.

**How to apply:** when reviewing any card touching "agent memory" (e.g. T-16-3), check the in-repo one against `team/lessons.md` for sourcing accuracy — that's a project artifact under review, not my own memory. Keep my own SDK memory entries here separate and don't seed lessons.md content into this store.
