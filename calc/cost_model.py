"""InvAI monthly cost and margin model.

Run: python3 calc/cost_model.py
Inputs come from docs/research/05-09 (prices checked 2026-09-23). Values marked
U in those reports are unverified; change them here and re-run.
"""

SCENARIOS = {
    #          shops, orders/day per shop
    "Pilot":  dict(shops=3,   orders_per_shop_day=300),
    "Growth": dict(shops=20,  orders_per_shop_day=400),
    "Scale":  dict(shops=100, orders_per_shop_day=400),
}
DAYS = 30

# Subscription tiers: (max orders per month, price per month)
TIERS = [(3_000, 149), (10_000, 349), (30_000, 699), (float("inf"), 1_499)]

# Shipping labels (EasyPost Forge; per-label fee is unverified)
LABEL_FREE = 3_000
LABEL_COST = 0.08      # what EasyPost charges us per label (U)
LABEL_PRICE = 0.10     # what we charge the shop per label (PLAN_CATALOG.labelFeeCents; see OI-1)

# Monthly vendor costs per scenario (Pilot, Growth, Scale), from the research
FIXED = {
    # Hosting (05-tools-hosting): AWS Fargate + RDS + Valkey + S3 + CloudFront, on demand
    "Hosting (AWS)":               (265, 810, 2_140),
    # AI + imaging (08-tools-ai-imaging), volume based
    "AI: design generation":       (63, 630, 3_360),
    "AI: upscale + bg removal":    (3.7, 29.6, 148),
    "AI: mockups (own compositor)": (5, 15, 50),
    "AI: OCR":                     (1.25, 10.5, 50),
    "AI: observability (Langfuse)": (29, 41.96, 124.10),
    "Trademark (USPTO + Signa)":   (119, 139, 479),
    "Keyword data (DataForSEO)":   (50, 75, 250),
    "Forecasting compute":         (1, 5, 20),
    # Services (07-tools-services)
    "Printing (PrintNode)":        (60, 288, 1_450),
    "Email (SES)":                 (3.2, 24, 128),
    "Errors/analytics/logs":       (0, 95, 621),
    "Support chat (Crisp)":        (0, 45, 95),
    "Uptime/on-call (Better Stack)": (0, 29, 54),
    # Dev tools (09-tools-frontend)
    "AI code review (CodeRabbit)": (24, 24, 24),
    # Security: pen test ~$6.5k/yr from the Amazon review onward (U)
    "Pen test (amortized)":        (0, 540, 540),
}

# Claude text work: two model options (08-tools-ai-imaging)
CLAUDE = {
    "sonnet-5": {"listing copy": (15.6, 156, 780), "assistant chat": (26.2, 262, 1_310)},
    "opus-5":   {"listing copy": (39, 390, 1_950), "assistant chat": (65.5, 655, 3_275)},
}


def tier_price(orders_month):
    for cap, price in TIERS:
        if orders_month <= cap:
            return price


def stripe_fees(invoice_amounts, postage_topups):
    """ACH 0.8% capped $5, Billing 0.7%, Tax Basic $0.50 per invoice.
    Postage wallet top-ups are plain ACH payments (no Billing fee)."""
    fee = 0.0
    for amt in invoice_amounts:
        fee += min(amt * 0.008, 5) + amt * 0.007 + 0.50
    fee += postage_topups * 5
    return fee


def run(model):
    rows = []
    for i, (name, s) in enumerate(SCENARIOS.items()):
        shops = s["shops"]
        orders_shop_m = s["orders_per_shop_day"] * DAYS
        labels = orders_shop_m * shops

        sub_rev = tier_price(orders_shop_m) * shops
        label_rev = labels * LABEL_PRICE
        label_cost = max(0, labels - LABEL_FREE) * LABEL_COST

        invoice = tier_price(orders_shop_m) + orders_shop_m * LABEL_PRICE
        stripe = stripe_fees([invoice] * shops, postage_topups=shops * 4.33)

        fixed = sum(v[i] for v in FIXED.values())
        claude = sum(v[i] for v in CLAUDE[model].values())
        costs = fixed + claude + label_cost + stripe
        revenue = sub_rev + label_rev
        rows.append(dict(
            scenario=name, shops=shops, orders_month=labels,
            sub_rev=sub_rev, label_rev=label_rev, revenue=revenue,
            platform=fixed + claude, label_cost=label_cost, stripe=stripe,
            costs=costs, profit=revenue - costs,
            margin=(revenue - costs) / revenue,
            cost_per_shop=costs / shops,
            cost_per_order=costs / labels,
            margin_no_labels=(sub_rev - (fixed + claude + stripe)) / sub_rev,
        ))
    return rows


def fmt(rows, model):
    out = [f"\n### Claude text model: {model}\n",
           "| | " + " | ".join(r["scenario"] for r in rows) + " |",
           "| --- |" + " --- |" * len(rows)]
    lines = [
        ("Shops", "shops", "{:,.0f}"),
        ("Orders (labels) per month", "orders_month", "{:,.0f}"),
        ("Subscription revenue", "sub_rev", "${:,.0f}"),
        (f"Label fee revenue (${LABEL_PRICE:.2f})", "label_rev", "${:,.0f}"),
        ("**Total revenue**", "revenue", "**${:,.0f}**"),
        ("Platform costs (hosting, AI, services)", "platform", "${:,.0f}"),
        ("EasyPost label fees ($0.08)", "label_cost", "${:,.0f}"),
        ("Stripe fees (ACH)", "stripe", "${:,.0f}"),
        ("**Total costs**", "costs", "**${:,.0f}**"),
        ("**Gross profit**", "profit", "**${:,.0f}**"),
        ("Gross margin", "margin", "{:.0%}"),
        ("Margin on subscriptions alone", "margin_no_labels", "{:.0%}"),
        ("Cost per shop", "cost_per_shop", "${:,.0f}"),
        ("Cost per order", "cost_per_order", "${:,.3f}"),
    ]
    for label, key, f in lines:
        out.append(f"| {label} | " + " | ".join(f.format(r[key]) for r in rows) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    for m in CLAUDE:
        print(fmt(run(m), m))
    print("\n### Breakeven: label fee needed to cover EasyPost at list price")
    print(f"EasyPost ${LABEL_COST}/label -> any price above ${LABEL_COST} is margin; "
          "at $0.08 charged, labels are pure pass-through.")


def sensitivity():
    """Scale scenario, Sonnet 5: gross profit and what one 400/day shop pays per month,
    across our label price and EasyPost's (negotiable) per-label fee."""
    global LABEL_PRICE, LABEL_COST
    keep = (LABEL_PRICE, LABEL_COST)
    prices = [0.05, 0.08, 0.10, 0.15]
    costs = [0.08, 0.05, 0.03]
    out = ["\n### Sensitivity (Scale, 100 shops): gross profit per month",
           "| Our label price → / EasyPost fee ↓ | " + " | ".join(f"${p:.2f}" for p in prices) + " |",
           "| --- |" + " --- |" * len(prices)]
    for c in costs:
        cells = []
        for p in prices:
            LABEL_PRICE, LABEL_COST = p, c
            r = run("sonnet-5")[2]
            cells.append(f"${r['profit']:,.0f} ({r['margin']:.0%})")
        out.append(f"| ${c:.2f} | " + " | ".join(cells) + " |")
    shop_orders = SCENARIOS["Scale"]["orders_per_shop_day"] * DAYS
    out.append("\nWhat one 400-orders/day shop pays per month (plan + label fees): " +
               ", ".join(f"${tier_price(shop_orders) + shop_orders * p:,.0f} at ${p:.2f}" for p in prices))
    LABEL_PRICE, LABEL_COST = keep
    print("\n".join(out))


sensitivity()
