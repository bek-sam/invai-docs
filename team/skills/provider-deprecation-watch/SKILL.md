---
name: provider-deprecation-watch
description: Track dated provider deadlines and changes (marketplace API versions, token and secret rotation, carrier rules, supplier moves, fee changes) and turn each into a card before it breaks InvAI. Use monthly, when a provider changelog or email announces a change, or when asked "what's expiring", "API version", "deprecation", "sunset", "deadline".
---

# Provider deprecation watch

Every dated change from Etsy, Amazon, Shopify, TikTok Shop, Walmart, EasyPost, USPS/UPS, S&S and SanMar has an
owner and a card at least one wave before its deadline, and nothing ships against a removed API.

## When to use
- Monthly (first wave of the month), and whenever a provider changelog, developer email or policy page
  announces a change.
- Before bumping a pinned API version (`SHOPIFY_API_VERSION` in `src/integrations/channels/shopify/common.ts`,
  now `"2026-07"`).
- Owner: integrations-engineer. compliance-officer owns policy (non-API) changes through
  `policy-change-watch`.

## Steps
1. **Open the deadline table** `deadlines.md` (this folder). Sort by date; anything within 60 days is urgent.
2. **Check each provider's source of truth** (doc changelogs, not blogs): Shopify API release notes and
   changelog; Etsy Open API GitHub discussions and developer portal; Amazon SP-API changelog
   (`developer-docs.amazon`); TikTok Partner Center; Walmart developer release notes; EasyPost releases and
   blog. Record the URL and the date you checked.
3. **Mark each fact's confidence** the way research 10 does: untagged (official), [3P] (third party), [U]
   (unverified). A [3P] or [U] deadline gets a verification task before any code change.
4. **Grep the code for impact** and write the file list:
   ```
   cd ~/Desktop/projects/invai/invai-backend
   grep -rn "SHOPIFY_API_VERSION\|ignoreCompareQuantity\|getOrders\|getOrderItems\|x-api-key\|confirmShipment" src
   ```
   Also check `invai-contracts/src/channels.ts` (`CHANNEL_RULES` fees and ship-by rules) for fee and policy
   changes.
5. **Decide per row:** no impact (note why), a code card (backlog id), a contract change
   (`contract-deprecation` via the architect), or an owner action (app re-registration, secret rotation in a
   real account, approval) through `escalate-to-owner` with the deadline and the default if silent.
6. **Add or update backlog rows** by asking the tech lead (they own `invai-docs/waves/backlog.md`). Give
   severity: P0 if it breaks orders, tracking or listing before the next wave ends.
7. **Update `deadlines.md`**: new rows, status, the check date. Remove a row only after the change shipped and
   was verified in a sandbox.
8. **Recurring credentials** (Amazon 180-day LWA secret, 365-day re-auth, Walmart 1-year, Etsy/Shopify 90-day
   refresh): make sure the credential calendar job (backlog B-05, to be created) covers them; until it exists,
   list the connection-level dates you know in the report.
9. **Report** to the tech lead: what changed since last month, what's urgent, cards requested, owner actions
   requested.

## Rules (MUST / MUST NOT)
- MUST NOT bump a pinned API version without reading every breaking change between the old and new version and
  running the adapter's fixture tests and a sandbox run.
- MUST NOT act on a [3P] or [U] date without verifying it; say so in the report when you can't.
- MUST keep reads and writes that live on different API versions separate when a provider splits them (Amazon:
  reads on v2026, `confirmShipment` on v0).
- MUST escalate anything that needs a real account action (secret rotation, app re-registration, new
  approval).

## Done when
- Every row in `deadlines.md` has a status, an owner and a check date within the last 31 days.
- Every row inside 60 days has a card or an owner-inbox entry.
- The report lists sources checked with URLs.

## References
- `deadlines.md` (this folder)
- `invai-docs/research/10-marketplace-engineering-rules.md` (all dated facts; §9 for code impact)
- `invai-docs/waves/backlog.md` (B-04, B-05, B-06, B-07, B-13, B-25, B-36)
- Related: `add-marketplace-integration`, `add-carrier-or-supplier-adapter`, `contract-deprecation`,
  `policy-change-watch`, `escalate-to-owner`
