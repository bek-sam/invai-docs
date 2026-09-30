# Testability review: business-analytics-v2 (Tracks A, B, C, E only)

Reviewer: qa-engineer
Verdict: **changes-required**

## What I checked
| Check | Result |
|---|---|
| Every AC-A/B/C/E/G names role, starting state, observable result | Pass for user-facing ACs; several system-level ACs (A4, C2, C4, E1, G1, G2) skip a role, which is fine — they assert data/system invariants, not a role's view |
| Edge cases: cancel/no-profit-line-equivalent, tenancy, permission refusal, outage-equivalent, small-sample, scale | Present: A7 (orders not in numbers yet), E4 (tenancy), E5 (permission), A6 (no fixed-costs setting), B2 (insufficient scan history), B3/C1 (small-sample), G2 (scale) |
| AC-G1 parity testable as one assertion | **No — ambiguous**, see finding 4 |
| Every wave A1/A2 card has an AC for each piece of its scope (T-A1..T-A10 cross-check) | **Gaps found**, see findings 1–3 |
| T-A1 seed gives QA something concrete beyond "golden path unchanged" | **No**, see finding 1 |

## Blocking findings
1. **T-A1 (seed) has no acceptance criterion of its own** (spec line 200, and absent from the AC list entirely). The card promises "18 months of closed history with a Q4 peak, some late shipments, realistic scan intervals, POs with price changes and lead times, a few repeat Shopify buyers, several reprint reasons," but the only checkable line anywhere is "golden-path counts and Today queues unchanged." Several downstream ACs silently depend on these seed properties existing at a testable scale — AC-B2 needs "≥ 100 timed units" of scan data, AC-A5/profitBridge needs multiple distinct periods to diff, AC-C3 needs a real size-mix gap, and analytics.supplierTrends (finding 2) needs PO price changes and lead times. Add explicit, numeric ACs for T-A1 (e.g., "≥ 18 months of orders", "≥ 100 press scans with realistic press-time spread", "≥ 1 PO line with a ≥ 5% price change and a differing lead time", "≥ 2 Shopify buyers with ≥ 2 orders each", "≥ 3 distinct reprint reasons"), or QA has nothing to fail against for this card.

2. **`analytics.supplierTrends` has no acceptance criterion anywhere.** It's explicit scope on T-A5 (line 204: "supplier trends") and named in section 6 Track C (line 142) and the top-15 list (item 14), and T-A9's D12 depends on `supplier_trends.md` (line 192). AC-C1..C4 cover inventory health, dead stock, reorder PO, and design lifecycle — none test unit-cost-by-supplier×style×month, median lead days, or the "differs by > 3 days" lead-time-setting check. Add an AC-C5 for it before T-A5 starts.

3. **Digest detectors D10, D11, D12, D13 have no acceptance criterion.** T-A9's scope (line 212) is "Digest D9–D13 and D2 bridge mover," but only AC-E1 tests D9 (line 175). D10 (losing orders > 5%), D11 (dead stock/size gap), D12 (blank price up ≥ 5%), D13 (break-even pace), and the D2-bridge-mover change (line 148, "D2 names the bridge's biggest mover") are all described in section 6 but none are checkable from the AC list. Each needs its own Given/firing-threshold/Then, same shape as AC-E1, before T-A9 starts.

4. **AC-G1 parity is not one unambiguous assertion.** "Given the same period, when the Profit page, `analytics.unitEconomics`, the assistant's `get_unit_economics` and the digest snapshot compute net, then all four are equal" doesn't say: (a) which period boundary to use — the digest snapshot is a fixed calendar week (line 30, "last week, week before, trailing 4–8"), while the Profit page and `unitEconomics` take an arbitrary `{period}` (line 127) chosen in the UI; the test needs to state that the comparison period *is* the digest's own last-completed week, or the four surfaces aren't comparable. (b) whether the compared "net" is the whole-shop aggregate (no `channel`/`dimension` filter) or must also hold per-channel/per-design, since `unitEconomics` takes an optional `channel` and a required `dimension` (line 127) that the digest snapshot doesn't expose. Recommend rewriting AC-G1 as: "Given the digest's last-completed week as the period, with no channel filter and dimension=order (whole-shop totals), when all four surfaces compute net for that exact week, then they are equal to the cent" — or splitting into a whole-shop case and a named per-channel case.

## Optional notes (non-blocking)
- T-A8's three newer tools (`get_operations_health`, `get_inventory_health`, `get_shipping_insights`) are only exercised by the generic tenancy/permission ACs (E4/E5); no AC checks their actual content is correct. Thin, but not "no AC at all" — a nice-to-have addition, not a blocker for A1.
- AC-C1's "a style × color with < 30 units sold is not shown" reads as silent exclusion, which reads in tension with rule 5 #2 ("below the definition's minimum sample, show counts and 'not enough data yet'"). Likely intentional (it mirrors the ≥30-units gate on size-mix gaps in section 6), but worth a one-line clarification in the card so QA doesn't flag it as a rule-5 violation later.
- T-A2 (contract) carries no AC of its own; that's consistent with how contract-only cards are usually verified (via consumer type-checks), so not flagged as blocking.
