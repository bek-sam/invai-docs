# Wave P5 — Spanish alert and timeline text, realistic reprints in the demo, design preview loose ends

**Dates:** 2026-10-01.

## What was built
- **T-P5-1** Seed reprints partial and ~3% of pressed items (B-243); seed previews
  through the catalog path (B-233 seed part) (backend-foundation/seed) — makes the demo
  shop's reprints look like a *real* shop's, not 44 orders reprinted end to end.
- **T-P5-2** Replaced design's old previews removed when unreferenced; late preview
  backfills order items (B-233 rest) (backend-engineer/catalog, orders).
- **T-P5-3** Contract: alert `params`, timeline `reasonCode` + `reasonParams`, additive
  (B-224, B-238) (architect) — structured data so alert and timeline text can be
  translated properly instead of built as raw English sentences.
- **T-P5-4** Backend fills alert params and timeline reason codes (B-224, B-238)
  (backend-engineer across today, orders, shipping, inventory, channels, vendors).
- **T-P5-5** Web shows alert lines and timeline reasons from codes, en and es (B-224,
  B-238) (web-engineer).

## Why
Today's alert lines and the order timeline's reasons had been showing raw English
sentences (or nothing at all) under Spanish — because the data behind them was built as
English prose at the source, not as a translatable code plus parameters. T-P5-3 through
T-P5-5 fix that at the contract level, the same pattern as every other en/es feature in
the project (a code the UI maps to a translated string, never raw text from the server).

## What went wrong
- A scratch-DB `db:reset` without a pinned `REDIS_URL` wiped the shared dev Redis DB 0
  queues **again** — the same mistake as T-23-9, still happening because the default
  behavior hadn't changed yet (B-219 was proposed but not yet landed). A scratch seed
  without `SEED_OUTPUT_FILE` also overwrote the shared `seed-output.json` the same way.
- Two builders handed back while their own full test suite was still running in the
  background, one of them with its work still uncommitted — because the Bash tool itself
  moves any call longer than its 2-minute default timeout to the background, which ends
  the agent's turn before the suite is actually done.

## What the team learned
- Before any scratch reset, migrate or seed, pin *both* `REDIS_URL` and
  `SEED_OUTPUT_FILE` explicitly — the mechanical fix (B-219, refusing an unpinned reset)
  still hadn't landed by this wave, so the written rule had to carry the weight alone
  again.
- Full suites and E2E runs use an explicit 600000ms timeout in the foreground, specifically
  so the Bash tool's own default timeout doesn't silently background a run an agent
  thinks it's still waiting on.

## Files to look at
- `invai-backend/src/db/seed/data.ts` — the realistic reprint rate (T-P5-1).
- `invai-backend/src/modules/catalog/service.ts` — preview cleanup and backfill (T-P5-2).
- `invai-contracts/src/schemas/today.ts` (alert `params`), `src/schemas/orders.ts`
  (timeline `reasonCode`/`reasonParams`) — T-P5-3.
- `invai-backend/src/modules/{today,orders,shipping,inventory,channels,vendors}/service.ts`
  — T-P5-4.
- `invai-web/src/i18n/en.ts` + `es.ts`, `src/components/orders/timeline.tsx` — T-P5-5.
- `invai-docs/team/lessons.md` (2026-10-01, "wave P5" rows, two of them).
