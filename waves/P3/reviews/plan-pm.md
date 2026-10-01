# PM review: wave P3 plan

**Verdict: approve** (T-P3-1, T-P3-2)

## T-P3-1 / T-P3-2 scope check
- Both cite `always-in-scope: bug` (`product/scope.md#always-in-scope`, "Bugs in shipped features") and both
  trace to a confirmed root cause (`waves/P2/reports/gate-rootcause.md`), not a new feature: B-236
  misclassifies read traffic as writes in the rate limiter; B-237 maps the resulting 429 to the wrong floor
  UI state. Real regressions on the golden path (floor scanning), not scope creep.
- No rate limit is raised or lowered (card and wave.md fence agree) — the fix is classification, not
  loosening a control. Good: a weakened limit would need an owner escalation, not just a card.
- Fences respected: no deploys/AWS/outbound in either card; OI-17/OI-18 (unapproved scope) and waves 24/25
  (decision 0019, paused) aren't touched; `invai-infra` stays read-only.
- Risk flags fit: T-P3-1 (auth, floor-correctness) correctly pulls security-reviewer per decision 0019
  (auth-adjacent: it changes how the auth/rate-limit middleware classifies a procedure). T-P3-2
  (floor-correctness, ui copy) stays with the primary reviewer only, correctly — no tenancy/PII/payments
  surface.
- B-240 (contract `rateBucket`) is correctly left for later, architect first — not pulled into T-P3-1.

## Slots 3–5: ranking (full detail in `product/backlog-ranking.md`, 2026-10-01 wave-P3 section)
1. **es 4-digit money group separator** (invai-ui, product-designer) — carried over from the P2 ranking's
   "worth its own card" flag; every Spanish-reading shop's money display, single owner, no dependency.
2. **B-230**, Profit v2 "losing orders" Units 0 / Revenue $0 (backend-engineer finance) — verify first; ties
   to the "unknown profit" wedge pain; single owner.
3. **B-221**, market test suite leaks into global cache, 3/3 failed runs plus a deadlock (backend-engineer
   market) — tagged Medium "can fail the gate"; the only pick that protects wave velocity itself, not just
   one screen.

**Wait:** B-238+B-224 and B-231 both need the architect to go first (contract `reasonCode` / enum shaping)
before a single owner can close them this wave — same hold-rule used for B-231/B-132 in the P2 ranking.
B-132 waits for the same reason and is lowest-priority besides (cosmetic console noise, already mitigated).
B-235, B-239, B-232, B-234 are real but lower pain/evidence or test-only; good filler if a 4th/5th slot
opens, not ahead of the top 3.

No spec needed for any of the three picks — each is a small, evidence-backed bug fix on an existing screen
or test suite, the same class as B-223/B-224 in P2 (`write-spec` not required for a one-line always-in-scope
bug).
