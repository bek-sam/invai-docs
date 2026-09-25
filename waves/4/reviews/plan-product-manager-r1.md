# Wave 4 plan review — product-manager, round 1

**Verdict: approve with clarifications applied** (directly to the cards and `wave.md`; listed below).

## Scope traceability
| Card | Scope ref | Traced to |
|---|---|---|
| T-4-1 | `scope.md#mvp-in` item 5 (production floor: pack, scan match); decision 0002 | Correct. Pack-complete and idempotent QC/bin calls are exactly "scan-checked floor" and "never press/ship the wrong thing." |
| T-4-2 | `scope.md#mvp-in` item 5 (offline queue) | Correct — offline queue is named explicitly in the MVP-in line, this closes real gaps (B-95). |
| T-4-3 | `scope.md#mvp-in` items 5, 6 and 9 (floor app; blank inventory/receiving; vendor portal) | Correct. Receiving has been promised in scope since the baseline but never built for the floor tablet — this fills a real MVP gap, not a new scope item. |
| T-4-4 | `scope.md#mvp-in` item 5 | Correct — floor polish and English leaks in the Spanish UI are bugs in a shipped, in-scope feature ("always in scope: bugs in shipped features"). |

All four backlog IDs (B-94, B-95, B-96, B-27, B-33, B-105) trace to `build/audit-2026-09-24.md` §A-FE findings I verified by file:line. Nothing here touches anything cut by decision 0006 or reopens an accepted decision as filed. One correction below changes that read for T-4-1.

## "Pack anyway" / `packed_partial` — does it fit shops? (decision 0002)
This is the one real gap in the plan. Decision 0002 defines "packed" and "shipped" but says nothing about shipping an order with units missing — I checked `research/01-shop-workflow.md` and `scope.md` too, and found no mention of partial shipment, backorder, or "pack anyway" anywhere. This card is not extending decision 0002, it's making a new product call that decision 0002 never addressed: **should InvAI ever let a shop ship a customer an order that's short a unit?**

That's a real, evidenced pain in DTF shops (a lost transfer, a QC failure with no time to reprint before the ship-by) — I'd guess this is why the tech lead specified it — but "I'd guess" isn't evidence per my own MUST rule (every feature needs a pain: who, how often, what it costs). Nothing in the card or the backlog cites a pilot or ticket for it. Given the guardrails already in the design (permission-gated to `production.override`/owner/admin, audited with reason, `missing[]` never silently dropped — see the architect's exact stub), I'm not blocking on it: the blast radius is small (an explicit, logged human decision, not an automatic behavior), and refusing to build any safety-valve at all would leave shops stuck holding an order forever when one unit is lost. But this needs to be **recorded**, not just built:
- Added an instruction to T-4-1's card: the backend-engineer's final report must state explicitly that a `packed_partial`-equivalent path shipped, and the tech lead should file a short decision addendum (`decisions/0002-pack-semantics.md` gets a "consequences" update, or a new `0010-partial-pack-override.md`) once it's built, citing this review as the reason it's in scope.
- Confirmed with the architect (see their review) that override-packed orders still enter the normal shipping/label queue rather than being silently held — that's the only reading of "pack anyway" that matches the button's name and the packer's intent, and I want it on record that's the deliberate choice, not an accident of the state-machine design.
- Not escalating to the owner: this doesn't touch pricing, plan limits, or anything sent outside the team, and the permission gate means it's the shop's own admin/owner choosing to ship short, not InvAI deciding for them.

## Testable acceptance criteria
Mostly good — each card's criteria are concrete enough for QA to write a test against without guessing a number or a threshold (data-driven backlog fixes, not vague feature asks). Two gaps, now fixed on the cards:
1. **T-4-1 AC2 (override)** originally said the order is marked "`packed_partial` or similar per the architect" — not testable as written, since "or similar" has no fixed shape. The architect's exact stub (`wave.md` §4) replaces this with a concrete, checkable rule: `orders.packOverride` populated with reason/by/byName/at/missingItemIds, `status` forced to the existing `ready_to_ship` value. QA can now assert the exact field and value instead of guessing what "or similar" means.
2. **T-4-1 AC3 / T-4-4 AC5 (`wrong_style`)** were written as new work ("returns mismatch `wrong_style`" / "has its own mismatch message") but the architect's review found this already fully shipped — contract enum, backend matcher, floor i18n en/es, and a passing unit test. Rewrote both as regression checks. This matters for scope discipline: if QA had written a fresh acceptance test assuming this didn't exist yet, it would have "passed" trivially and the backlog item (B-33) would have stayed marked "open" indefinitely, wasting a future wave's planning time re-discovering it's done. Recommend the tech lead close B-33 in the backlog.

## Receiver scope
`receiver` gaining `production.receive` (scoped to marking sheets received) rather than the full `production.build` matches the segment table exactly: mid-shop receivers check in blanks and transfers, they don't build gang sheets or send to vendors. No scope creep — `RECEIVER`'s permission set stays narrow (`inventory.read/adjust/count`, `purchasing.read/receive`, `production.read/scan`, plus now `production.receive`), nothing added that a receiving-desk worker shouldn't have. Confirmed the architect's design also restores `office`'s access to `sheets.markReceived` (which changes which permission it needs) so no existing role silently loses something it has today — that would have been a real regression to catch.

## Other notes
- T-4-4 correctly sequences after T-4-1 since it consumes `packOrder` — right call, no scope issue.
- Nothing here implicates pricing, plan limits or segment targeting; nothing to escalate to the owner beyond the decision-record follow-up above.
