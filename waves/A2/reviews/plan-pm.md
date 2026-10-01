# Wave A2 plan review — product-manager, 2026-09-30

## Verdict: approve

## Findings

1. **T-A6** scope ref `#mvp-in` item 8 correct (B-173, profit). AC list (A1,A2,A3,A6,A7,E6) matches spec. B-226 (Costos clipping, es number formats) folded in with its own AC line — fine, matches my scope-check's fold instruction.

2. **T-A7** scope ref items 5, 6, 14 correct (B-174 ops/inventory/design lifecycle, B-177 web half of Today). AC list (B1-B3, B/C-screen1, C1, C2, C4, C5, E2 web half, E6) matches spec. AC-C3 (reorder PO edit-before-submit) correctly marked out of scope as "served by the backend split in A1" — consistent with my scope-check note that B-172's size-split suggestion already passes the no-automatic-changes fence. B-225 (Today date locale, repeat of B-207) folded in with a ban-check AC — good, this is the second occurrence my memory flags; a lint/test enforcement is the right promotion.

3. **T-A8** scope ref item 13 correct (B-175, assistant tools v6, read-only). AC list (A5, E3, E4, G1 assistant leg) matches. No write tool, no model/effort change — correctly out of scope per decision 0007. No market-signals tools (item 16) leak in.

4. **T-A9** scope ref items 14, 17 correct (B-176 digest D9-D13 + D2 mover, B-177 backend half of Today). AC list (E1, E1b-E1f, E2 backend half, E4, E5, G1 digest leg) matches spec exactly, including the A1 tiebreak note and `shipmentsWithoutZone` grant, both already flagged in the A1 handoff rather than new scope. No buyer data in detector params, stated explicitly.

5. **T-A10** scope ref items 14, 17 correct (contract for B-176/B-177). Additive-only contract change (0.10.0), stub grant is narrowly scoped and handed back to T-A9. No Track D leakage.

6. **No fence violations found:** Track D (B-178..B-181) does not appear on any card; "Not in this wave" and each card's "Out of scope" section name it explicitly. OI-17 and OI-18 are correctly treated as unapproved (both still `status: open` in `owner-inbox.md`) and nothing gated behind them is built. No buyer PII, no cross-seller aggregation, no automatic price/listing/PO writes, no forecasting model anywhere in the five cards.

7. **AC coverage for B-173..B-177 is complete** across the five cards (cross-checked against every AC-A/B/C/E/G id in `specs/business-analytics-v2.md` for these rows): every AC lands on at least one card, or is correctly marked already-satisfied in A1 (AC-C3, AC-A4) or covered by QA's separate scale run (AC-G2, per my note in `wave-plan-review-pattern` memory — a scale AC doesn't need its own card).

No changes required. The order of B-173..B-177 in the backlog rows is the tech lead's call, not reviewed here.
