# T-28-3: 18-month retention sweep for non-PII Amazon order data

| Field | Value |
|---|---|
| Wave | 28 |
| Scope ref | `always-in-scope: compliance` (Amazon DPP 2025-11-25: non-PII Amazon data "must not be stored for longer than 18 months, unless longer retention is legally required"; `security/v1-review.md` DPP table; backlog B-187) |
| Spec | this card plus the DPP table |
| Owner | backend-engineer (area: privacy) |
| Reviewer | `reviewer` (fable) |
| Co-reviewers | security-reviewer (opus; pii, tenancy: a cross-tenant system job that deletes data), compliance-officer (sonnet; the keep/drop classification and decision 0026) |
| Risk flags | pii, tenancy, data deletion |
| Model | opus |

## Owned paths (edit)
- `invai-backend/src/modules/privacy/**` (service, jobs, tests)
- `invai-docs/decisions/0026-amazon-non-pii-retention.md` plus its index row (type security, status proposed; compliance-officer and security-reviewer accept it in review)

## Read-only paths
- every other backend path, including `src/db/schema/**` (if a column or index is needed, stop and tell the tech lead: no migration is planned for this card), `src/worker/sweeps.ts`, `src/modules/orders/**`, `src/integrations/**`

## Depends on
- nothing. Runs in parallel with T-28-1, T-28-2 and T-28-5 (no shared files).

## Interfaces promised
- `sweepStaleAmazonData(now = new Date(), opts?: { dryRun?: boolean }) -> { orders: number; rowsCleared: Record<string, number> }` in `src/modules/privacy/service.ts`, called from the existing daily `privacy.retentionSweep` job after `redactStaleBuyerPii()`.

## Acceptance criteria
1. **Classify first, then build.** Before writing the sweep, list every table and column that holds data from an Amazon channel (orders and items from `channel = 'amazon'`, whatever the source: SP-API or the Amazon CSV import; raw payloads, marketplace-specific fields, sync and import logs, delivery/webhook rows, settlement or fee lines). Mark each **keep** (a financial record needed for tax and bookkeeping: money totals, fees, cost, dates, the order number on the shop's own books; the "legally required" exception, US tax records) or **drop** (everything else: raw payloads, buyer-facing text, marketplace metadata, logs). Put the table in decision 0026 and in your report. Compliance co-review approves the classification.
2. Given an Amazon order placed more than 18 months ago (the module's existing month cutoff, `buyerPiiCutoff`: `setUTCMonth(-18)` on `orders.placedAt`; no second day-count rule) and in a final state (shipped, delivered or cancelled, `invai-contracts/src/states.ts`; never an open order), when the daily sweep runs, then every **drop** value of that order and its children is deleted or set to null, and **keep** values stay unchanged. Profit for that order's month still adds up to the same total afterward.
3. Orders from other channels, Amazon orders younger than 18 months, and open orders of any age are untouched (tests prove each).
4. Idempotent and safe: the batch query selects only orders that **still hold drop data** (a predicate like `holdsPii`, `privacy/service.ts` ~749), so the loop ends and a second run selects and changes nothing; drop columns that are NOT NULL get a fixed placeholder named in decision 0026; work is batched (at most 500 orders per transaction, loop until done) so one run never holds a long lock; each company runs inside `withTenant` (or `withSystem` only to list the companies, as `redactStaleBuyerPii` does); a failure in one company is logged and the rest continue.
5. A dry run (`sweepStaleAmazonData(now, { dryRun: true })`) returns the same counts and changes nothing.
6. Each run logs counts only (companies, orders, rows per table), never order numbers or buyer data, and records an audit entry per company the same way the PII sweep does (if it does).
7. Existing tests of the PII sweep still pass unchanged.
8. Decision 0026 gets its index row in `decisions/README.md`; T-28-2 adds one too, so stage only your hunk (`git add -p`).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in invai-backend (privacy tests while building; the full suite once at the end with `set -o pipefail`, logged, FAIL/Error lines and tail printed).
- Exercise for real: a `tsx` script against `invai_test` or a scratch DB (never the shared dev DB: the sweep deletes data) that creates one Amazon order 19 months old (final state), one 17 months old, one 19 months old but open, one Shopify order 19 months old; runs a dry run, then the sweep twice; prints per-order before/after of the drop and keep columns. Expected: the dry run reports 1 order and changes nothing; the real run changes only the first order's drop values; the second run reports 0.
- Scratch DB: pin `REDIS_URL` to Valkey DB 13 and `SEED_OUTPUT_FILE` to `/tmp/t283-seed.json` before any reset, migrate or seed.

## Out of scope
- Non-Amazon retention policy changes; the existing buyer-PII sweep (B-23); log retention (B-75, infra); the 30-day PII purge (S-16). Deleting whole orders.

## Budget
- About 2 hours. Escalate to the tech lead if blocked for more than about 30 minutes of work, if a schema change looks necessary, or if a "keep" vs "drop" call needs a lawyer (then keep it, mark it in decision 0026 for OI-19 counsel review, and continue).
