# Review: business-analytics-v2 spec (flow only) — product-designer

Reviewer: product-designer. Scope: Tracks A, B, C, E only (Track D out of scope this round).

## Verdict: changes-required

## What I checked
| Area | Verdict |
|---|---|
| Observable flow per new screen/surface (AC-A1–A7, B1–B3, C1–C4, E1–E6) | Mostly yes; gaps below |
| Empty/zero-data states (fixed costs, labeled shipments, history) | Insufficient — see findings 1–3 |
| Screen-buildability (no vague or contradictory descriptions) | OK; CSV export pattern (AC-E6) matches the Profit page precedent |
| en/es and plain-language flags (rule 10) | Present at the rules level; not tested per-surface (optional note) |
| Association-not-causation wording (rule 4) in AC-B3 | Correct — "were more often," never "caused" |

## Blocking findings
1. **Section 6 Track A / AC-A3 (lines 130, 163)** — Shipping profit tab has no Given/When/Then for a shop with **zero labeled shipments** in the period. AC-A6/AC-A7/AC-B2/AC-C1 cover "no fixed costs," "orders without profit lines," "not enough scans," and a stock-share filter respectively, but none of them stands in for this case. A shop mid-onboarding or one that hand-writes labels will hit an empty tab with undefined behavior. Add an AC: given no labeled shipments in the period, show a clear "no labeled shipments yet" state, not a blank table or a $0 margin that reads as good news.

2. **Track B/C screens overall (lines 136–144; AC-B2, AC-C1)** — Existing ACs handle per-metric thresholds (press-time sample size, a per-style/color filter) but there's no screen-level first-run state for **Operations, Inventory health, or Design lifecycle** when a shop has too little history overall (e.g., live 2 weeks). AC-A7's "105 orders aren't in these numbers yet" banner is the right pattern (rule 2's "not enough data yet"); it isn't extended to these three screens. Add an equivalent whole-screen empty state, distinct from the individual widget-level "not enough scans yet" / "not enough data" notes already specified.

3. **Section 6 Track E (line 148)** — Digest detectors D10 (losing orders), D11 (dead stock/size gap), D12 (blank price up) and D13 (break-even pace) have no acceptance criteria; only D9 gets one (AC-E1, line 175). A designer/QA can't verify their trigger flow, copy pattern or minimum-sample rule the way D9's is verified. Add one AC per detector (or a shared AC covering all four with per-detector thresholds), matching AC-E1's shape.

4. **AC-E2 (line 176)** — Today actions panel flow is specified only for the case where actions exist. No stated behavior when zero detectors fire (a healthy week) — does the panel hide, or show a plain "nothing needs attention" state? This is a normal, frequent state, not an edge case; needs an explicit AC.

## Optional notes (non-blocking)
- Rule 10 (en/es) is stated as a blanket rule but no AC exercises Spanish copy for the new web screens (T-A6/T-A7) or digest D9–D13 templates the way AC-E3 does for the assistant. Given `build-dashboard-screen`'s DoD already enforces en/es, this is low risk, but one AC per new surface would remove ambiguity at card time.
- T-A6 bundles six new sub-views (contribution, losing orders, leakage waterfall, shipping profit, bridge, break-even) into one card with no stated navigation model (tabs vs. sections vs. sub-routes). The AC names are concrete enough to design from, but the UX spec written at card time should settle the IA before web-engineer builds.
