# 0014: Market signals and the weekly digest are in scope, inside fixed fences

- Status: accepted (2026-09-27)
- Type: owner

## Context
- SCR-001 (market signals for the assistant) and SCR-002 (a scheduled weekly business review) were sent to the owner as OI-6 and OI-7 with a "defer" recommendation: 0 shops had asked, and both add cost and risk (marketplace terms, unattended sends).
- The owner approved both on 2026-09-27 (answers in `owner-inbox.md`, OI-6 and OI-7), with guardrails: ToS-compliant sources only, no scraping, a mock for every provider, no paid source bought without the owner; the digest gets its own spec, opt-in/opt-out, an eval gate before any unattended send, and a spending cap per tenant.
- Research: `research/14-market-signals.md` (marketplace terms: Amazon AUP §4.4–4.6, Shopify API Terms §6.2.5/§6.2.8/§2.3.24, Walmart and TikTok partner terms, Etsy's analytics clause) and `research/15-weekly-digest.md` (hybrid digest, CAN-SPAM, RFC 8058, cost per shop).
- Links: `product/scope-changes/SCR-001-…`, `SCR-002-…`; specs `specs/market-signals.md`, `specs/weekly-digest.md`; scope items 16 and 17. Decided by the owner; recorded by product-manager.

## Decision
1. `product/scope.md` items 16 (market signals) and 17 (weekly digest) are in the MVP.
2. Fences (hard; changing one needs a new owner decision):
   - No scraping of any marketplace, search engine or competitor site, and no scraper or unofficial API, ever.
   - Marketplace-origin data (API or the shop's CSV export) is used only for the shop it came from. No cross-seller aggregation, benchmark or model training on it.
   - Cross-shop benchmarks over InvAI-native data are deferred until 10+ live shops per cell and a counsel-reviewed ToS/DPA clause.
   - No automatic price, listing, ad or PO changes; outputs are suggestions.
   - No Etsy competitor data until Etsy agrees in writing.
   - No real paid data source, alpha programme or outside account without an answered owner-inbox entry; the mock is the default.
   - Every number shown by either feature is computed by code. The model may choose, order and phrase; it never produces a number. Mock data is labelled "sample data".
   - The digest email is opt-in per person, carries no promotions, and the AI-written summary stays in shadow mode until the real-model eval (OI-8) passes.
3. Build order: market signals (wave 18) before the digest (wave 19), because the digest's Market watch block reads market-signal output.

## Consequences
- Easier: the assistant can answer "is this trending?", "am I priced right?" and "when should I prep for the season?" with cited numbers; shops get a weekly review without asking.
- Harder: two new modules, new tables (one global cache table needs an architect ADR under CLAUDE.md rule 7), a new outbound email stream, and more eval surface.
- Enforcement: tests that the global market cache has no `company_id` and holds only taxonomy queries; a validator that rejects any model-written digit in the digest; the answer validator that rejects market numbers not in a tool output; `sendMail` skip rules for sample workspaces and non-opted-in users. Owners: backend-engineer (market, digest), ai-engineer (validators, evals), security-reviewer (co-review).
- Owner follow-ups: OI-9 (Google Trends alpha), OI-10 (Etsy permission), OI-11 (Jungle Scout licence), OI-12 (postal address), OI-13 (email provider and sending subdomain), OI-14 (counsel on CAN-SPAM classification). Nothing in waves 18–19 waits on them.
