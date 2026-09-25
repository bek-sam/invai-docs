# Review of T-3-1 (round 1)

- Reviewer: compliance-officer on Opus 5.5
- Author: integrations-engineer on Opus 5.5
- Verdict: **approve**

## Evidence I re-ran

Setup shared with the primary review: worktree `../invai-backend-r31` at `00c35e4`, API port 3191 + worker against DB copy `invai_r31_copy`, mock Shopify, `REDIS_URL=redis://localhost:6379/10`.

| Command | Result |
|---|---|
| `node_modules/.bin/tsc --noEmit && node_modules/.bin/biome check . && node_modules/.bin/vitest run && node_modules/.bin/tsup` | all clean |
| Live: signed `customers/redact` on a real imported order | `buyer_note`/`buyer_ref`/`raw_payload_key` null, `buyer_pii` rows gone, `privacy_requests` row `completed` with counts, all synchronous (before the 200) |
| Live: signed `shop/redact` on the seeded shop | all 100 orders on that connection redacted (98/98 had PII), including orders imported before this test — confirms scope is "every order from that store," not just ones named in the payload |
| Read `shopify.app.toml` | declares the three compliance topics app-scoped, correct API version, matches `common.ts`'s scope list |

## Shopify App Store / privacy-law-compliance checklist (`research/10-marketplace-engineering-rules.md` §5, `shopify.dev/docs/apps/build/compliance/privacy-law-compliance`)

| Requirement | Status | Evidence |
|---|---|---|
| `customers/data_request`, `customers/redact`, `shop/redact` declared in `shopify.app.toml` | Met | `shopify.app.toml` `[[webhooks.subscriptions]] compliance_topics = [...]` |
| HMAC-verified, dedupe on delivery id | Met | `api/webhooks.ts`; verified via `security-reviewer`'s review too |
| Completed within 30 days | Met, with one caveat below | `PRIVACY_REQUEST_DUE_MS` (30 days) on `data_request`; redact is synchronous (done before the 200, so effectively instant) |
| `shop/redact` handled even after uninstall (arrives 48h later) | Met | `handlePrivacyRequest`'s connection lookup uses `ne(status, "pending")`, which includes `disconnected` — confirmed live: a store's `shop/redact` after real Shopify usage would still resolve its connection whether or not it's currently connected |
| The shop identified from the signed body, not a spoofable header | Met | see security-reviewer's review; confirmed live |
| `data_request` produces something the owner can act on within 30 days | Met | `privacy_requests` row `status: open`, `dueAt`; `audit()` log entry; daily `warnOverduePrivacyRequests` logs anything still open after 20 days, giving a 10-day buffer before the deadline |
| GraphQL-only, Billing API for charges | N/A to this card | out of scope (no billing changes here) |

## Redaction completeness — what's covered and what isn't

Covered by the synchronous handler: `buyer_pii` rows (name, email, phone, address), `orders.buyer_note`, `orders.buyer_ref`, the encrypted raw webhook payload in S3, and every order-item personalization answer/uploaded file reference. Order facts kept for accounting (ids, SKUs, amounts, dates) match the card and the processor obligation ("keep non-PII order facts needed for the shop's accounting").

**Not covered synchronously, and worth tracking as a follow-up rather than a blocker:** rendered artwork files and label PDFs that have the buyer's address printed on them. These are deleted by the existing `purgePiiObjects` sweep (`orders/jobs.ts`, not part of this card), which runs on a 30-day-from-object-creation cutoff independent of when a redact request arrives. In practice (labels are bought within days of the order, not weeks) this still lands inside Shopify's 30-day compliance window, but it is not driven by the redact event itself. The author's report discloses this explicitly under "known gaps," which is the right way to hand it off — I'm recording it here as a follow-up card, not a blocker: **have redact/shop-redact enqueue an immediate purge of that order's/that shop's PII objects (`label`, and any rendered-artwork prefix), instead of relying solely on the daily sweep's own clock.** This closes the gap between "the data subject asked" and "the object is actually gone" without touching the general retention sweep's design.

No search index, cache, or secondary store outside Postgres/S3 was found holding buyer PII for Shopify orders (checked: no Elasticsearch/OpenSearch or similar in `invai-backend`'s dependencies; `rg -i "buyer" invai-backend/src --type ts -l` turns up only the DB/S3 paths already covered).

## Blocking findings

None.

## Checks
- [x] Only owned paths changed (`invai-docs/compliance/**` untouched by this card; reviewing `invai-backend`'s diff per the primary review's `--stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior (7 tests named in the author's report for `modules/privacy/service.test.ts`: 401, redact-before-200 incl. S3 object gone, duplicate, cross-shop isolation, header spoof, `data_request` due-30-days, `shop/redact` after uninstall, unknown shop)
- [x] "Draft for counsel" marking: n/a, this card writes no legal text
- [x] Every compliance claim in this review is tied to a file, test, or a live run I did myself — no claim taken on the author's word alone

## Optional notes (not blocking)
1. File the label-PDF/rendered-artwork immediate-purge-on-redact gap as a backlog item, owned by whoever owns `orders/jobs.ts` (not this card's owner), so it doesn't only live in review files.
2. Once the app is actually registered (OI-2) and `shopify.app.toml`'s placeholders are replaced, re-confirm the webhook URL and API version still match what's declared to Shopify — routine, not specific to this diff.
