---
name: wave-p2-ranking
description: How P1 hand-off backlog candidates were scored and picked for wave P2 slots 4-5
metadata:
  type: project
---

2026-10-01: Ranked the P1 hand-off candidates (`waves/P1/wave.md` hand-off item 4) for P2's open slots
T-P2-4/5. Picked B-223+B-224 (Spanish-correctness, order drawer + Today alerts) and an un-numbered bug
("Today actions jobId re-queue after 3 failures", first noted `waves/24/wave.md` L53 / A2 T-A9 review) —
both small, single-owner, no contract change. Passed over B-231 and B-132 because each needs the architect
as a second owner (contract enum shaping / vendor-library decision) before it fits a 2-3h single-owner card —
**How to apply:** when a candidate needs the architect or another role to go first, it's not a clean fit for
a small-slot wave; rank it below items a single owner can close, even if its raw pain score is higher.
Also flagged the es 4-digit money group-separator bug (inside "invai-ui follow-ups") as worth its own future
card since it affects every Spanish-reading shop's money display, not just a cosmetic clip — see
`invai-docs/product/backlog-ranking.md` 2026-10-01 section for full scoring.
