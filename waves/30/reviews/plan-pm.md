# Wave 30 plan review: product-manager (2026-10-09)

Verdict: APPROVE with two text edits (wording only, no card is cut).

Checks
- Cards: 4 (cap 5). OK.
- Scope refs: all four use "always in scope" classes that exist in scope.md (compliance, security, reliability and observability needed to run pilots, team tooling). T-30-1: compliance + S-59, evidence is the Amazon DPP row and decision 0027 gaps. T-30-2/3: deploy prep under the owner order of 2026-10-09; decision 0019 pause is on AWS work, and these cards use no AWS, keys or deploys. T-30-4: guard reliability. Nothing outside scope.md; no scope-change-request needed. B-23 correctly left to wave 31.
- Decision 0019 / 0027: no conflict. 0027 "Known gaps" are exactly B-300/B-301/B-304; T-30-1 narrows them via 0031 and does not edit 0027.
- Wedge: T-30-1 touches sheets, but only after a sheet leaves production (AC2/AC3/AC7), so no pressing or reprint flow is affected.

Product decisions made
- Deleting a sheet's print files after a purged unit is acceptable (reprints are per unit and rebuild a new sheet; a purged unit needs its text re-entered anyway). Recorded as decision 0032.
- Disabled download buttons with no explanation are not acceptable as a final state. T-30-1 stays without a web change, but a follow-up card (web-engineer, wave 31) adds the explaining line on both sheet screens. Tech lead: add the backlog row (text in 0032).

Edits required
1. wave.md Goal, first clause: replace "(closes the gaps that keep Amazon's "PII deleted 30 days after delivery" row Partial)" with "(narrows the gaps behind Amazon's "PII deleted 30 days after delivery" row; it stays Partial until B-302 audit_log flags and B-303 manual uploads are closed)". Reason: the card's own Out of scope lists those two, so the outcome claim was overstated.
2. T-30-1 AC8 / "Out of scope": add the line "Shop-visible side effect: sheet download buttons stay disabled with no explanation until the wave-31 web card (decision 0032); say so under Known gaps in the report." Also add "0032" to the Spec field next to 0027.

Notes (no change needed)
- T-30-1 reserves 0031; I used 0032 and added its index row. 0031 must be added by T-30-1.
- Honest user outcome for T-30-2/3: owner gets a verified build path, not a deployed system; keep the wording "no unknown build step", which is accurate.
- No pilot has asked to keep old sheet files (customers/ has no such issue); revisit if two shops do.
