---
name: scrub-pii-fixture
description: Turn real or realistic marketplace data (Etsy, Amazon, Shopify, TikTok, Walmart exports, webhook payloads, label responses, screenshots) into a safe InvAI test fixture — reserved fake names, emails, phones and addresses, same structure, SKUs, variations and personalization shapes. Use before committing any fixture, seed row, screenshot or example that started from real data.
---

# Scrub a PII fixture

A fixture behaves exactly like the real file in the parser, and contains nothing that identifies a real buyer,
shop or staff member.

## When to use
- A shop sent an order export, webhook sample or label response to reproduce a bug (`import-dry-run`,
  `triage-support-ticket`).
- You are adding a CSV or JSON fixture under `invai-backend/src/integrations/**/fixtures/` or test data in
  `src/test/`.
- A screenshot, log excerpt or example for a spec, help article, review or incident note.

## Steps
1. **Keep the raw file out of every repo.** Work on it under `/tmp/invai-scrub/` (never inside `invai-*`).
   Don't paste it into chat, prompts, tickets or reports. It's deleted at step 8.
2. **List the PII columns and fields.** For marketplace exports these are at least:
   - buyer name, username/handle, email, phone
   - ship-to name, street 1 and 2, city, state, zip, country (and billing equivalents)
   - buyer note / gift message / personalization text that names a person
   - order ids and transaction ids that can be looked up in the real marketplace
   - tracking codes, label URLs, IPs, payment details
   Example column names: Etsy `Buyer`, `Ship Name`, `Ship Address1`, `Ship Address2`, `Ship City`,
   `Ship State`, `Ship Zipcode` (see
   `invai-backend/src/integrations/channels/csv/fixtures/etsy-sold-order-items.csv`).
3. **Replace, keeping the shape.**
   | Field | Replace with |
   |---|---|
   | Person names | Obviously fake but realistic names; keep length and accents where the parser cares (Spanish names with accents are good test data) |
   | Emails | `<name>@example.com` or `<name>@<shop>.test` (reserved domains, RFC 2606) |
   | Phones | US fictional range `+1 555-0100` to `555-0199` |
   | Streets | A fake number + a generic street; keep apartment/suite lines where the original had them (they exercise `street2`) |
   | City/state/zip | Keep a plausible US combo (for example `Phoenix, AZ 85003`); zip must be valid-format so ship-by and rate code still runs |
   | Order/transaction ids | Same length and prefix pattern, new digits (`3310000001` style) |
   | Tracking codes | Carrier-shaped fakes (`9400100000000000000000` style) |
   | Personalization text | Keep length, line breaks, emoji, accents and overflow cases; replace real names with fake ones |
   | Buyer notes | Keep the meaning that matters to the test ("rush", "gift"), drop identifying details |
4. **Keep what the tests need:** column order and headers exactly, quoting, blank cells, multi-item orders
   (same order id across rows), quantity > 1, coupons and discounts, currency, `Variations`, SKUs (shop SKUs
   are product codes, not PII, but rename a shop's brand prefix if it identifies the shop), and dates (shift
   them, keep weekdays if ship-by logic depends on them).
5. **Scrub the shop too.** Real shop names, logos, staff names and emails become seed-style fakes
   (`Desert Bloom Tees`, `@desertbloom.test`).
6. **Check it.** Before saving the fixture:
   ```
   # emails not on a reserved domain (also catches Amazon relay addresses, which are real buyer contacts)
   grep -nEo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+' <fixture> | grep -vE '@(example\.(com|org|net)|[a-z0-9-]+\.test)$'
   # phone-shaped numbers outside 555-0100..0199 (long order ids match too: read each hit)
   grep -nE '\b[0-9]{3}[-. )]*[0-9]{3}[-. ]*[0-9]{4}\b' <fixture> | grep -vE '555[-. ]?01[0-9]{2}'
   ```
   Every remaining hit must be a value you confirmed is fake. Then read every row of the name and address
   columns yourself.
7. **Prove it still parses.** Add or run the parser test (for CSV:
   `invai-backend/src/integrations/channels/csv/parse.test.ts`, run with
   `pnpm test src/integrations/channels/csv`) and confirm the same counts, items and edge cases as the raw
   file produced.
8. **Delete the raw file.** `rm -rf /tmp/invai-scrub/`. Note in your report: source type, what was scrubbed,
   and that the raw file was deleted.

## Rules
- MUST NOT commit, screenshot, log or send to an AI provider any real buyer PII, even in a private repo or a
  test that is "only local".
- MUST NOT put real shop data in any non-local environment without the owner (`escalate-to-owner`).
- MUST NOT keep a mapping from fake to real values anywhere.
- MUST keep fixtures synthetic enough that no row can be traced back, and realistic enough that parsers and
  ship-by logic behave the same (the seed-realism lesson in `team/lessons.md`).
- If you find real PII already committed, stop and treat it as a possible incident: tell the
  `security-reviewer` and follow `incident-response`. Don't rewrite pushed history
  (`.claude/hooks/guard-bash.py` blocks it); the owner decides.

## Done when
- The fixture lives in the owner's fixtures folder, passes the step 6 greps, and a human-eyes read of name and
  address columns.
- The parser test passes with the fixture, covering the same edge cases as the source.
- The raw file is deleted and the report says so.

## References
- `invai-docs/research/12-security-quality-playbook.md` §2.2 (test and production data kept apart), §2.7
  (retention)
- `invai-docs/security/v1-review.md` (PII handling: S-09, S-16, S-17, S-29)
- Existing fixtures: `invai-backend/src/integrations/channels/csv/fixtures/`
- Related: `import-dry-run`, `triage-support-ticket`, `incident-response`
