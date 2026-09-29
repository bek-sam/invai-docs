# Wave 21 plan review — product-manager

**Verdict: approve**

## Checked
- 5 cards, ≤5 limit met.
- Every source in scope: B-10 and B-29 are `always-in-scope: compliance`; B-98 is `scope.md#mvp-in` item 14 (onboarding: Help link, terms/privacy at sign-up); B-106 (runbook) is `always-in-scope: bug`. No item outside `scope.md`.
- Fence held: legal text stays draft-only. T-21-1 AC1 requires the "DRAFT for counsel review. Not in force." banner and `[[OWNER: …]]` placeholders instead of invented values; T-21-5 AC2 puts the same "Draft, pending legal review" banner on the live `/legal/*` pages; nothing is published or sent (T-21-1 "Out of scope": publishing, sending, signing). The integration gate requires an owner-inbox entry for counsel review rather than an actual send.
- No "secure/compliant/guaranteed" claims: stated as a rule on the wave and enforced by T-21-4/T-21-5's compliance-officer co-review.
- Priorities fit roadmap criterion 1 (no dead buttons): T-21-5 turns the sign-up terms/privacy text and the app-shell Help entry from dead links into real routes, and B-98's help-center content backs them — this is exactly the kind of end-to-end closure criterion 1 asks for.
- Evidence: every card cites a backlog id with a real source (B-10, B-29, B-98, B-106) already tracked in `waves/backlog.md`, plus T-20-5's report and the wave 19 gate finding for the runbook fixes — no unsourced work.

## Notes (non-blocking)
- T-21-4 AC1's 12+ help articles cover items 1–3, 4, 6, 7, 8, 9, 10, 11, 13, 14, 15, 17 reasonably; there's no dedicated article for item 16 (market signals), but that's assistant-surfaced and reasonably folded into "the assistant" article — no change needed unless a pilot asks for one.
