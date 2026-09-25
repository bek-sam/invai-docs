# Review of T-6-5 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: backend-foundation + integrations-engineer on Opus
- Verdict: **approve**

## What changed since round 1
Round 1's only finding was that the supplier guard (`integrations/suppliers/index.ts`,
`modules/inventory/service.ts`) touched files outside T-6-5's owned paths and both documented
grants, with no `scope-change-request` on file, contradicting AC2's explicit instruction to raise
one rather than build it in silently.

The tech lead resolved this by grant, recorded on the card itself: `T-6-5-demo-cant-spend.md`
lines 28-29, "## Tech-lead decision (2026-09-25, given in the build prompt, recorded here) —
Supplier ordering is **in scope** for this card... `integrations/suppliers/index.ts` and the
supplier call sites in `modules/inventory/service.ts` were granted to T-6-5. No scope-change
request is needed." This is the owner-decides-scope path the round-1 escalation asked for, and
it's in the right place (the card, not just a chat message).

No code changed. All round-1 evidence (tsc/biome/vitest/build across all three repos at the same
SHAs, the adapter-call-site grep, `demo-guards.test.ts`'s spy/behavioral proof, the test-weakening
scan, the new-test-fails-on-old-code check) still stands — see `T-6-5-reviewer-r1.md` for the full
table; I re-read the card's new section and the diffs it covers, and re-confirm nothing else needs
re-running.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| AC1 | Yes | unchanged from r1 |
| AC2 | Yes | unchanged from r1; the supplier path is now in-scope by grant, closing the round-1 process gap |
| AC3 | Yes | unchanged from r1 |
| AC4 | Yes | unchanged from r1 |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — yes, with the supplier files now covered by the recorded grant
- [x] Nothing outside scope — yes, per the tech-lead decision
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy/idempotency/money/en+es — n/a / satisfied, per r1
- [x] Decisions recorded where needed — yes, on the card itself

## Optional notes (not blocking)
None beyond r1's.
