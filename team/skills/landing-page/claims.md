# Claims register and rules (all growth copy)

Every factual statement in public copy (pages, listings, emails, posts) is a row in
`invai-docs/growth/claims.md` (created on first use). Copy cites the claim id in a comment next to the
sentence (`<!-- C-012 -->`). Used by `landing-page`, `seo-comparison-page`, `lifecycle-email-sequence`,
`app-store-listing` and `launch-plan`.

## Register format
```
| Id | Claim as written | Type | Source / metric definition | Checked | Re-check by | Reviewed by |
|---|---|---|---|---|---|---|
| C-001 | "Turns today's Etsy and Shopify orders into order-labeled gang sheets" | capability | seen in app, /production/sheets, seed data, screenshot growth/shots/2026-10-01/… | 2026-10-01 | next release | compliance-officer |
| C-002 | "Pythias starts at $199/month for 2 channels" | competitor fact | https://pythiastechnologies.com/pricing | 2026-10-01 | 30 days | compliance-officer |
| C-003 | "Pilot shops cut gang-sheet layout time by X%" | measured | metrics/<metric>.md, n shops, dates | — | — | data-analyst + compliance |
```
Types: `capability` (verified in the running app), `competitor fact` (public source, dated), `measured`
(data-analyst metric with definition, sample size and period), `third-party fact` (marketplace fee, rule),
`opinion` (clearly phrased as ours: "we think").

## Rules and where they come from
| Rule | Source |
|---|---|
| Have a reasonable basis (evidence) for every objective claim **before** publishing | FTC Advertising Substantiation policy: https://www.ftc.gov/legal-library/browse/ftc-policy-statement-regarding-advertising-substantiation |
| Comparisons with named competitors are allowed if truthful, clear and supported; the same basis is needed for claims about them | FTC Comparative Advertising policy (16 CFR 14.15): https://www.ftc.gov/legal-library/browse/statement-policy-regarding-comparative-advertising |
| No fake, AI-written or insider reviews or testimonials; no buying reviews; no suppressing negative ones; no fake social proof | FTC Consumer Reviews and Testimonials Rule, 16 CFR 465, in force 2024-10-21: https://www.ftc.gov/legal-library/browse/federal-register-notices/16-cfr-part-465-trade-regulation-rule-use-consumer-reviews-testimonials-final-rule |
| A testimonial must reflect the person's real, typical-or-disclosed experience; disclose any material connection (free months, discounts, pilot status) clearly and conspicuously | FTC Endorsement Guides (16 CFR 255, revised 2023): https://www.ftc.gov/legal-library/browse/federal-register-notices/16-cfr-part-255-guides-concerning-use-endorsements-testimonials-advertising ; https://www.ftc.gov/business-guidance/advertising-marketing/endorsements-influencers-reviews |
| Pilot shops' names, logos and quotes only with the shop's written permission, obtained by the owner | growth-marketer role file |
| Prices and plan limits only as the owner approved them | growth-marketer role file; `product/scope.md` pricing hypothesis |
| Marketplace names as plain words only (no logos without brand permission); Etsy notice when Etsy is named in the product: "The term 'Etsy' is a trademark of Etsy, Inc. This Application uses Etsy's API, but is not endorsed or certified by Etsy." | research 10 §3; each marketplace's brand guidelines [verify before using any logo] |
| Don't say "integrates with Amazon/Etsy/TikTok/Walmart" while those adapters are CSV-only or awaiting approval; say "imports CSV exports from …" | `product/scope.md` MVP list; decision 0006 |

## Words to avoid unless a register row proves them
"#1", "best", "only", "first", "guaranteed", "never late", "zero waste", "saves X hours", "AI-powered" as the
whole pitch, "approved by Etsy/Amazon/Shopify", "partner of …".
