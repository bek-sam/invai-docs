---
name: dest_zone_pii_review_pattern
description: T-A4 dest_zone (carrier zone from ZIP3) — how to verify a "derive-then-discard" PII pattern fast
metadata:
  type: project
---

T-A4 added `shipments.dest_zone` (smallint 1-9) computed from ZIP3s already held in memory at label-buy time, never persisting the ZIP. Verified in minutes by: (1) `git show <migration commit>` — the SQL must be exactly one `ADD COLUMN`, nothing else; (2) grep the schema diff for the new column only; (3) confirm the service diff passes the *derived* value (zone number), not the raw input, into the write path; (4) check the exact-column-list test uses equality (`cols.sort()).toEqual(fixed list)`), not just a regex filter, per [[s34-taxonomy-equality-test]].

**Why:** this is the fast, reliable way to prove a "compute in memory, store only the derived non-PII value" claim without reading the whole diff line by line.
**How to apply:** any future card that claims "we only store X, never the underlying PII" (zones, hashed emails, redacted logs) — check the migration SQL first, then trace the value backward from the write call to its source.
