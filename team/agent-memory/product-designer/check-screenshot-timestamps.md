---
name: check-screenshot-timestamps
description: when a report's "after" screenshot looks wrong, compare file mtimes against the commit time and against sibling screenshots of the same screen before assuming the code is broken — it may just be a stale frame left in the evidence set.
metadata:
  type: feedback
---

2026-10-01, T-P4-3: `es-design-detail-1440.png` (and the 390 and en variants) still showed the raw
enum "sleeve_left" as the broken-image alt text, which looked like the reported placement-alt-text
fix hadn't landed. But `ls -la` (or `stat`) showed those three files were written at 01:49:2x–30,
while the sibling "-bottom" screenshots of the *same* scrolled page were written at 01:51:52 — 2.5
minutes later, after the commit's actual build — and those did show the fix working ("Manga
izquierda"). The commit itself (85c4ed0, 01:55:12) came after both. Conclusion: the fix was real; the
web-engineer just left pre-fix frames in the evidence folder under names that read as "after".

**Why it matters going forward:** before writing up a screenshot-evidence mismatch as a blocking code
defect, check mtimes of the suspect screenshot against (a) the commit timestamp and (b) any other
screenshot of the same screen taken later in the session. A later, correct screenshot of the same
page is strong proof the fix works and the issue is stale evidence, not a code bug — downgrade to a
non-blocking "retake this screenshot" note instead of blocking the card.
