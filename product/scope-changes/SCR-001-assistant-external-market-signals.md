# SCR-001: External market signals for the assistant (marketplace search trends, competitor prices)
Filed by: product-manager  Date: 2026-09-26  Type: add
Scope section affected: scope.md#mvp-in item 13 ("AI business assistant (read-only tools)")

## Request
Let the assistant answer with outside market context, not just the shop's own data: Etsy/Amazon search-trend or demand signals ("is this design still trending?"), and competitor pricing on similar listings ("am I priced right?"). This was raised in `specs/assistant-business-analyst.md` ("Out of scope") during wave 17's analyst-tools work (T-17-2/T-17-3), not from a pilot yet — there are no live pilots as of 2026-09-26.

## Why (evidence)
- `research/03-pain-points.md` ranks "unknown profit" and "listing time" among top pains, but no ranked pain is specifically "I can't see market trends or competitor prices" — this is an inference from the assistant spec's gap analysis, not a shop ask. One source, not a confirmed pain.
- `00-platform-concept.md` names AI listings with a trademark check as the wedge-adjacent AI surface; market-trend intelligence is not part of the stated wedge (orders → labeled gang sheets → scan-checked floor).
- No shop, pilot or ticket has asked for this (no entries in `customers/issues.md` yet, since no pilot is live). Evidence is thin: 0 shops confirmed.

## Who it helps
All segments in theory (small shops picking their next design, mid/large shops tuning ad spend), but unproven — this is a hypothesis, not a measured pain.

## Cost and risk
- **New paid service:** no in-house source for marketplace search-trend or competitor-price data exists. This needs either a paid third-party market-data API (recurring cost, unbudgeted) or scraping Etsy/Amazon/TikTok/Walmart search or listing pages.
- **Marketplace policy risk:** scraping breaks Etsy's and Amazon's terms of service — the same terms this team is trying to get commercial API approval under (`marketplace-app-application`). A ToS violation could jeopardize the pending Etsy Commercial Access and Amazon SP-API applications (decision `0006-v1-cuts.md` already treats direct Amazon SP-API as blocked pending security review; adding a scraping risk here compounds that).
- **AI/compute cost:** any ingested market data adds tokens to the assistant prompt per call, on top of the wave 17 analyst-mode cost increase (more tools called per turn, `max_iterations` raised to 10).
- **Effort:** at least a full wave (a new integration adapter or paid API contract, ingestion/caching, a new read-only tool, evals for staleness and hallucination risk) — sizeable, not a quick add.
- **Data quality risk:** stale or wrong external data presented as fact could mislead a shop's pricing or design decisions — a specific new "never promise/never fabricate" guard would be needed beyond what wave 17 already builds for internal data.

## If we don't
Shops keep making design and pricing calls on gut feel plus whatever they already see on the marketplace itself; the assistant stays honest by only ever citing the shop's own numbers (which is also the current, tested trust model — spec item "never cite outside market facts").

## Decision
Sent to owner (OI-6). Reason: unbudgeted recurring spend, a marketplace-ToS/scraping risk that could affect pending approvals, and evidence is a single inference rather than a pilot or ticket ask — this is squarely a cost-and-risk call reserved for the owner, not the PM.
Decided by: — (pending)  Date: —

My recommendation to the owner: defer. Don't build until (a) a paid, ToS-compliant market-data source is identified and priced, and (b) at least one live pilot explicitly asks for it. Revisit at the first `weekly-metrics-review`/`churn-risk-review` cycle after pilots go live.
