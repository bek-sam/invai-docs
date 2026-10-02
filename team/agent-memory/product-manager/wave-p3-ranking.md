---
name: wave-p3-ranking
description: How P2 hand-off backlog candidates were scored and picked for wave P3 slots 3-5
metadata:
  type: project
---

2026-10-01: Ranked the P2 hand-off candidates (`waves/P2/wave.md` hand-off item 4) for P3's open slots 3–5
(P3 slots 1–2 are the always-in-scope B-236/B-237 gate-root-cause fixes). Picked, in order: the es 4-digit
money group-separator fix (invai-ui, product-designer — carried over from the 2026-10-01 P2 ranking's "worth
its own card" flag), B-230 (Profit v2 losing-orders Units 0/Revenue $0, verify first, backend-engineer
finance), and B-221 (market test suite leaks into the global cache, 3/3 failed runs plus a deadlock,
backend-engineer market — tagged Medium "can fail the gate").

Passed over B-238+B-224 and B-231 again because each still needs the architect as a second owner (contract
`reasonCode` / enum shaping) before it fits a single-owner card — same rule as [[wave-p2-ranking]]: when a
candidate needs the architect or another role to go first, it ranks below items a single owner can close,
even with a similar raw pain score (es-separator and B-238+B-224 scored about the same on pain×shops×conf
÷effort; the second-owner dependency broke the tie).

New this round: B-221, excluded from P2's scoring by that wave's catalog-path fence, scored above the other
test-flake items (B-234, B-239) once eligible, because it's the only one tied to an actual observed failure
("can fail the gate", not just a hardening gap) — **how to apply:** when ranking test-reliability items
against each other, prefer the one with a reproduced failure over one found only by code reading, even at
similar severity labels.
