---
name: course-status-2026-10-02
description: Current state of invai-docs/learn/** and its Notion mirror as of 2026-10-02 (all 12 modules done)
metadata:
  type: project
---

All 12 course modules (`invai-docs/learn/01-big-picture` through `12-product-and-business`)
are written, each with 2-3 lessons in the full 9-part format, cited to real `file:line`.
Modules 09-12 were added in the 2026-10-02 run (security; the AI team, using the real
shared-Redis flakes/reprint profit bug/OrbStack+Mac-sleep incidents and decisions
0018/0019; deploy and ops, using `ops/cost-estimate-aws.md`; product and business, using
`product/scope.md` and `research/16-growth-opportunities.md`).

`glossary.md` now covers modules 01-12 (header line says so); the Notion Glossary mirror
previously lagged (only had modules 01-02 and 06-08 sections, with 03-05 explicitly noted
as pending) — that gap is now closed too, same run. Every module's lessons are mirrored to
Notion as child pages under the "InvAI Course" parent (URL in `learn/README.md`'s Notion
mirror table), in the same order as the parent's own child-page list.

**Why:** the owner's "push to 100%" instruction (see `push-to-100-percent.md` if it
exists) asked to finish all waves and course modules.

**How to apply:** the next natural piece of work is `diary/` — one short lesson per wave
(what was built, why, what went wrong, what to look at), starting from the waves that
module 10.3's three incidents came from. Before starting new course content, re-check
`invai-docs/waves/status-*.md` for the latest wave number, since this file will go stale
fast as waves continue. Don't re-verify modules 01-12 are current without checking
`git log` on `invai-docs/learn/**` first — this memory is a snapshot, not a live status.
