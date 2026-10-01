# Plan review (scope): wave P4. Product-manager

Reviewer: product-manager. Scope: scope refs on all 5 cards, fence check, card count, user outcome, slot-4
ranking (B-243).

**Verdict: approve.**

## Scope refs
All five cards correctly claim `always-in-scope: bug` (`scope.md` "Always in scope" → "Bugs in shipped
features"; T-P4-5 also fits "Reliability … needed to run pilots safely" for the B-221 cache-leak half).
T-P4-1/4: B-242, a real bug in a shipped feature (finance/analytics on a shipped item flag) — ruling
`decisions/0020` is sound and holds the money/floor-correctness line (`openReprint` unchanged, no
double-ship). T-P4-2: B-241, en/es is MVP item 5. T-P4-3: en/es leaks + B-184, same. T-P4-5: test-fixture
correctness is not itself a shop bug, but B-221's cache leak is a reliability class, not a new feature — the
ref holds. Nothing here builds past `scope.md`; no scope-change-request needed.

## Fences
Checked against `wave.md`'s stated fences: no card touches Track D, OI-17/OI-18 items, `invai-infra`, or
waves 24/25 work (confirmed: `invai-infra` not in any owned-paths list; no card role is platform-sre). No
card changes a rate limit or security control. No deploy, no AWS, no outbound send in any card's steps or
verification. Fences hold.

## Card count and outcome
Five cards, at the cap. The wave goal line states the user outcome plainly: profit keeps a reprinted sale's
revenue; Spanish floor/web screens read cleanly. No change needed.

## B-243 (seed reprint realism, backend-foundation, Medium)
**Wait for P5.** Two independent reasons, not just the 5-card cap: (1) the card itself says "do it with or
after B-242" — T-P4-1 is what makes B-242's model correct, so B-243's realistic seed mix should be built
against the landed fix, not in parallel with it; (2) P4 is already at 5 cards. Taking it as a 6th card would
also violate the wave cap (`operating-system.md`, owner's rule 5). Confirmed as the top P5 candidate below.

## P5 candidates (ranked, from `waves/backlog.md`, agent-doable, open, excluding waves 24/25, Track D,
OI-17/18, and approval-blocked)
Note: `backlog.md` has stale "open" rows for several items already closed in waves 22/23/A1/A2/P1-P3 (e.g.
B-25, B-30, B-139, B-164, B-223, B-236, B-237 are done despite their row text) — checked against the owning
wave files, not taken at face value.
1. **B-243** — seed reprint realism (44 orders 100%-reprinted is not credible for a pilot demo); single
   owner, ready right after T-P4-1 lands.
2. **B-224 + B-238** — typed `reasonCode` for Today alert bodies and the timeline reason, translated in web;
   held for an architect slot across P2 and P3 rankings with no slot yet opened; real, twice-confirmed
   Spanish-correctness pain (Today, order drawer) on a daily-use screen.
3. **B-233 (rest)** — design-preview cleanup on replace, the late-preview orders subscriber, and the seed's
   direct `imaging.preview` call; the DB-transaction part of B-233 is done (T-P2-2), this is the named
   remainder; single owner (backend-engineer, catalog/orders).
