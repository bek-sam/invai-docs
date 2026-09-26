# T-7-3: Label fee from the plan (B-69, B-40)

## What changed

- **`modules/billing/service.ts`** (invai-backend `b04849e`): `PLAN_CATALOG.labelFeeCents` for
  every paid plan (starter, growth, pro, scale) is now `10` (the concept's $0.10/label), each with
  an inline `// see OI-1` comment, plus a doc comment on the catalog pointing at OI-1. Trial stays
  `0` (free trial, unchanged). OI-1 is still **open** — its own "default if no answer" and
  recommendation (option C, with A as the code default) both name $0.10, so this doesn't preempt
  the owner; changing the number later is a one-line catalog edit.
- **`modules/shipping/service.ts`**: `LABEL_FEE_CENTS = 4` is gone. `recordLabel` (the tx that
  writes the `labels` row and flips the shipment to `labeled`) now reads
  `(await getPlan(tx, ctx.companyId)).labelFee` once and writes that same value onto both the
  `labels.labelFeeCents` and `shipments.labelFeeCents` columns. Only this hunk was touched — the
  fee lookup — per the card and `wave.md`'s note that T-7-1 owns the export-procedure hunk in the
  same file. Diff is 2 import/const lines plus a 3-line addition in `recordLabel`; no other line
  in the file changed.
- **`invai-docs/calc/cost_model.py`**: `LABEL_PRICE` changed from `0.15` to `0.10` (with a comment
  pointing at `PLAN_CATALOG.labelFeeCents` and OI-1) so the model's assumption matches the code's
  new default. The revenue-line label in the printed table now shows the live `LABEL_PRICE` value
  instead of a hardcoded `$0.15`. Nothing else in the model was touched.

## AC check

1. **Fee source** — done. `LABEL_FEE_CENTS` no longer exists anywhere in `src/` (grepped clean).
2. **Default price** — done. All paid plans default to 10¢ with `// see OI-1` on each.
3. **Consistency** — done, and mostly "already true structurally" as the plan-review note
   predicted: billing usage (`currentUsage` in `billing/service.ts`) sums `labels.labelFeeCents`,
   and finance's profit calc reads `shipments.labelFeeCents` — both now get the plan's fee because
   `recordLabel` writes the same computed value to both columns. No changes needed outside
   `recordLabel` for AC3.
4. **Tests** — done. New `modules/shipping/label-fee.test.ts`: buys a label (fake carrier, real
   Postgres) on starter/growth/pro/scale and asserts the plan's own `labelFeeCents` lands on both
   the `labels` and `shipments` rows and on the API's `shipment.labelFee`; a second test asserts
   billing usage (`currentUsage(...).labelFees`) increases by exactly the fee charged. 5/5 pass.

## Verify

- `pnpm typecheck` — clean.
- `pnpm lint` (biome) — clean, no fixes needed.
- `pnpm vitest run src/modules/shipping/label-fee.test.ts` — 5/5 pass.
- `pnpm vitest run src/modules/billing/` — 31/31 pass (no regressions in plan listing/limits).
- `pnpm vitest run src/modules/shipping/` — 91/92 pass. The one failure
  (`export-tracking.test.ts` > "re-export with since=null ... re-includes it") is **T-7-1's own
  test, not mine**: I stashed my two changed files and reran it against a clean `main` checkout —
  it fails identically with none of this card's diff applied, so it's a pre-existing timing/cutoff
  issue in the export code, unrelated to the fee lookup. Not touched, since it's outside this
  card's owned path (`modules/shipping/service.ts`, "the fee lookup only").
- Ran against `invai_test_t73` (real Postgres via `docker exec local-postgres-1`), `NODE_ENV=test`,
  `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` pointed at that DB, migrations already
  up to date. This is effectively "buy a label on starter and pro (and growth/scale) and check the
  fee" from the card's verify step, done at the service-function level against a real database
  rather than through the HTTP API. Docker/psql commands to also stand up the `invai_t73_copy`
  DB-copy and drive it through curl on port 3173 hung repeatedly (no output, moved to background,
  never returned) partway through this task — looked like the sandbox blocking or silently
  queuing the interactive docker exec calls, not a code issue. Given the unit-test coverage above
  already exercises the real DB path end to end, I didn't keep retrying; flagging it in case it's
  a real infra gap for other agents on this box.

## Out of scope, still open

Per `wave.md`'s clarification, these OI-1 gaps in `cost_model.py` are **not** fixed by this card
and remain open:
- AI design generation is still counted as a cost with no matching revenue line.
- Scale is priced at $1,499 in the model vs. `custom`/uncapped in the code.
- Revenue is booked for free pilots.

## Commits

- `invai-backend` `b04849e` — Label fee from the plan, not a flat constant (T-7-3, B-69, B-40).
- `invai-docs` — cost model's `LABEL_PRICE` synced to $0.10 (see SHA in reply).

Not pushed (wave in progress, per `CLAUDE.md`'s "owners commit their own paths, tech lead pushes
after the integration gate").
