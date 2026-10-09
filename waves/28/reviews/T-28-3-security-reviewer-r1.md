# Review: T-28-3 Amazon 18-month retention sweep (security co-review, round 1)
Reviewer: security-reviewer on Opus 5.5. Author: backend-engineer (privacy) on Opus 5.5. Inputs: card, report, invai-backend `dd4907e`, invai-docs `4fc1bfe`.

## Verdict: changes-required (decision 0026 text only; the sweep code passes)

## Threat model
Entry: daily `privacy.retentionSweep` job only, no API (no new procedure, nothing for authz.test). Worst outcome: one tenant's rows changed under another's scope, or data deleted that a shop needs for its books. Neither found.

## Checks
- Cross-tenant pattern: OK. `withSystem` reads company ids only (reason comment, `service.ts` sweepStaleAmazonData); every select/update/delete runs in `withTenant(companyId)` with explicit `company_id = companyId` on top of RLS. Unscoped `exists` subqueries (`import_runs r.id = orders.import_run_id`, `channel_connections`) only widen the system id list; inside the tenant tx RLS hides foreign rows, so no write crosses tenants.
- Logs/audit: counts, cutoff and company id only; failure log is `errorData` (message, ids/cutoff params, no buyer values). Audit `data`/`summary` are counts. OK.
- Idempotency, batching (500, `for update`), dry run, open/young/other-channel fences: covered by `amazon-retention.test.ts` (6 tests) and re-run green. Keep columns and `updated_at` untouched. OK.
- Keep/drop vs DPP "non-PII at most 18 months unless legally required": money, dates, order numbers, `channel_line_id` (settlement key) are the tax-record exception; ASIN, ship level, push error, address check, raw listing JSON, import errors/file keys, Amazon price snapshots dropped. Titles and refund notes kept with an OI-19 reason. Acceptable.

## Blocking finding
1. **S-56 (Medium, PII retention, pre-existing) misclassified in 0026.** `decisions/0026-amazon-non-pii-retention.md` table row "`item_artwork` ... no Amazon content beyond ids" is false: `item_artwork.values` is a copy of the buyer's personalization answers (`personalization/service.ts:494`) and `file_key`/`preview_key` are art rendered with that text. No sweep clears them (30-day purge, `redactOrders` and this sweep all skip it), so a buyer's custom text is kept forever. Proof: `invai-backend/src/modules/privacy/security.test.ts` (`it.fails`; run without the marker it fails at :58 `expected '{"name":"Probe Buyername"}' not to contain ...`; the `order_items` copy is redacted). Required for this card: move `item_artwork` out of the keep row into a PII line ("`values`, `file_key`, `preview_key`: buyer personalization, to be cleared by the PII sweep, open gap S-56"), and add a `labels` row (tracking/label key kept; label PDF removed by the 30-day S3 rule). The code fix to `redactOrders` is a separate card (card's out-of-scope: PII sweep), owner backend-engineer (privacy), due 2026-11-08.

## Decision 0026 verdict
Accept after the edit above (status can then read `accepted (2026-10-09)` for security; compliance-officer still accepts the classification).

## DPP row (v1-review.md, "Non-PII data ... 18 months") text after approval
What InvAI does today: "Daily `sweepStaleAmazonData` (decision 0026, T-28-3) clears non-PII Amazon data on final-state orders older than 18 months (ASIN, ship level, push errors, address checks, listing raw JSON, Amazon import errors/file keys, Amazon price snapshots); money, dates, order numbers and line codes kept as US tax records." Gap: "Partial: item titles and refund notes wait on counsel (OI-19); personalization copy in `item_artwork` (S-56)."

## Evidence I re-ran (invai-backend)
- `pnpm typecheck` exit 0; `biome check src/modules/privacy/security.test.ts` clean.
- `pnpm exec vitest run src/modules/privacy --reporter=dot`: 4 files, 23 passed + 1 expected fail (S-56).
- `scan-test-weakening.sh invai-backend dd4907e~1`: only hit is my new `it.fails` marker (intended).
- Sweep not run on the shared dev DB; no processes started.

## Optional notes
- `redactStaleBuyerPii` has no per-company try/catch (author already noted); a throw there skips the Amazon sweep for the night.
