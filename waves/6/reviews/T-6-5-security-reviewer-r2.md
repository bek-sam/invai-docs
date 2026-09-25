# Review of T-6-5 (round 2) — security-reviewer co-review

- Reviewer: security-reviewer on Sonnet 5
- Author: backend-foundation + integrations-engineer on Opus
- Verdict: **approve**

## What changed since round 1
Round 1 escalated one item: the supplier guard was built without the `scope-change-request` that
AC2 and both plan reviews called for, even though the guard itself was correct and well-tested.
The tech lead has since granted `integrations/suppliers/index.ts` and the supplier call sites in
`modules/inventory/service.ts` to T-6-5 directly, recorded on the card
(`T-6-5-demo-cant-spend.md`, "## Tech-lead decision", 2026-09-25): supplier ordering is
always-in-scope money safety, not new MVP scope, so no scope-change request is needed.

This resolves the escalation as intended — via an owner/tech-lead scope decision, not by reverting
a real control. Nothing else in round 1's threat model changes: no new entry points, no new PII,
no new webhook or injection surface. §5's worst-outcome framing is unchanged and, if anything,
now fully closed rather than partially closed: the supplier path (a sample workspace with its own
S&S credentials placing a real order) is guarded and in-scope, not a dangling out-of-process fix.
The one accepted gap (AI spend from a sample workspace, unguarded, platform-key exposure) remains
correctly flagged as a backlog item outside this card's AC, per the r1 finding for
`security/v1-review.md`.

## Decision
No blocking findings remain. **Approve.**
