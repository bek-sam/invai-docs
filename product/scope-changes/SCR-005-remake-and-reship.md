# SCR-005: Remake and reship after shipment, with cost in profit
Filed by: product-manager  Date: 2026-09-28  Type: add
Scope section affected: scope.md#mvp-in items 5 (floor), 7 (shipping), 8 (profit); new state path

## Request
From a shipped order, "Remake" creates new units linked to the original. They reuse the original print file, land on the next gang sheet tagged REMAKE, and pass the floor scan like any unit. A reship label follows. Reason codes: `lost_in_transit`, `damaged`, `print_defect`, `wrong_item`, `buyer_size`. Remake cost (blank, film, labor, label) posts to profit against the original order, design and channel. An optional carrier-claim status (filed, paid, denied) is included. Today's reprint flow covers only defects found before shipping.

## Why (evidence)
- TikTok moved 100% of buyer-remorse return shipping to sellers in June 2026, and customer service can issue partial refunds ([vendor] and [O] TikTok Seller University, `research/16` §1.2).
- USPS Ground Advantage claims are reported as routinely denied, so the shop pays refund plus remake (§1.1).
- Walmart enforces a Negative Feedback Rate from April 2026 [O].
- Veeqo shipped Reship on 2026-07-17 (research 16 §2).
- `research/03` pain #12 (returns and exchanges). Shops confirmed: 0 pilots.

## Who it helps
All segments; office, owner and floor roles.

## Cost and risk
- Effort: M, about 3 cards. It needs a contract change for the state path from shipped to linked remake units (architect), plus backend work in orders, production, shipping and finance, web, and a REMAKE tag on the floor.
- No new service. Label spend is the shop's.
- Risk: a state-machine change on the golden path, so it needs `run-golden-path` and an architect co-review.

## If we don't
Remakes happen outside InvAI (manual orders or spreadsheets). Profit per design and channel understates the real cost of returns, and remakes skip the scan check.

## Decision
Sent to owner (OI-17). The PM recommends **accept**.
Reason: closes a gap in the wedge (every unit scan-checked) and in true profit.  Decided by: —  Date: —
