# Plan review (scope): wave P7. Product-manager

Reviewer: product-manager. Scope: scope refs, fences, and whether other agent-doable P1/P2 (non-Low)
backlog items remain beyond B-134, B-115 (B-189 folded in).

**Verdict: approve.**

## Scope refs
T-P7-1 (B-255, flaky gate) and T-P7-3's added half (B-262, English spend-cap text shown to es users) are
correctly `always-in-scope: bug`. T-P7-2/T-P7-3 (B-134) correctly cite `scope.md#market-signals` (the
shipped screen the debt is on). T-P7-4 (B-115 hooks + B-189) and T-P7-5 (B-115 spend-per-round, LLM10) are
correctly `always-in-scope: security`. All four backlog ids this wave claims as its base (B-255, B-134,
B-115, B-189) match my P6 hand-off ranking; nothing here needed a scope-change-request.

## Scope creep check (items the architect's plan review surfaced)
The architect's R1-R3 rulings (`reviews/plan-architect.md`) added two things beyond the original cards:
B-262 was folded into T-P7-3 as its own `always-in-scope: bug` line (a real defect in a shipped screen, not
scope growth) and B-261 (a backend poll-skip follow-up) was correctly left as a Low backlog row, not forced
into a card. Both calls are sound; no fence crossed.

## Fences
No card touches `invai-infra` (T-P7-1 reads `gate.sh` only), Track D, OI-17/18 topics, or a wave-24/25 item
(B-261's Low follow-up is deferred, not built). No deploy, AWS or outbound send in any card. Decision 0020
isn't reopened. T-P7-4 and T-P7-5 strengthen controls (guard coverage, spend caps); neither weakens one.
Fences hold.

## Other open agent-doable P1/P2 (non-Low) items after P7
Beyond this wave's four, re-checking ranges my P5/P6 reviews didn't cover (backlog.md 183-315) turns up a
real gap: **B-185, B-186, B-187, B-188** (Amazon DPP: account lockout, password history, 18-month non-PII
retention sweep, mandatory owner/admin MFA; filed wave 21 T-21-3, `security/v1-review.md`) are still open,
agent-doable now (no SCR, no outside approval blocks the hardening work itself), and `always-in-scope:
compliance` (Amazon's data-protection rules) by `scope.md`'s own bullet — no wave has picked them up since
wave 21.

One more is technically open but not newly found: **B-132** (assistant stream `net::ERR_ABORTED`, P2) —
already mitigated by QA's allow-list, cosmetic, and repeatedly deprioritized across P1/P2/P3 rankings
because it needs the architect as a second owner first. Still open; not a clean single-card item yet.

**After P7: yes, something remains.** Recommend the tech lead fold B-185..B-188 into a P8 wave (compliance
debt, four small single-owner cards or one combined card) rather than a status-only file; B-132 stays
parked until the architect takes the dependency-patch decision.
