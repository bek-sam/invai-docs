# T-7-3: Label fee from the plan (B-69, B-40)
## Owned paths
- backend: `modules/billing/**` (the catalog), `modules/shipping/service.ts` (the fee lookup only)
- `invai-docs/calc/cost_model.py` (update the assumptions to match the code)
- tests

## Acceptance criteria
1. **Fee source:** `LABEL_FEE_CENTS = 4` is gone. The fee comes from the company's plan, `PLAN_CATALOG.labelFeeCents`.
2. **Default price:** use the concept's $0.10 per label as the default in the catalog, per OI-1's default, and mark it clearly as awaiting the owner's decision (OI-1). Changing it later is a one-line catalog edit. Confirmed OK to build now: OI-1's own "default if no answer" and its recommendation (option C, with A as the code default) both name $0.10 — this doesn't preempt the owner, it's what OI-1 already asked for while it stays open. Put `// see OI-1` on `PLAN_CATALOG.labelFeeCents`, not just the number.
3. **Consistency:** billing usage, the shipping label record and profit all use the same fee. The cost model matches the code.
4. **Tests:** cover per-plan fees.

## Verify
Run tsc, lint and test. Buy a label on the starter and pro plans (on a DB copy) and check the fee.

## Clarifications from the plan review
- **Out of scope, note as still open:** `cost_model.py`'s other three gaps from OI-1 (AI design generation still counted, Scale priced at $1,499 vs. `custom`/uncapped in code, revenue booked for free pilots) aren't part of this card's AC and shouldn't get fixed as drive-by changes. Say so in the report so they aren't mistaken for closed.
- **Written against current `main`:** wave 6's T-6-5 (`5339a57`) already changed `modules/billing/service.ts` (43 lines) and `modules/shipping/service.ts` call sites (the `carrierAdapter` factory now takes the company/scope). Base your "fee lookup only" hunk on the current file, not the pre-wave-6 shape.
- `modules/shipping/service.ts` is also touched by T-7-1 (export procedure) this wave — commit only your own hunk (`git add -p`), and if T-7-1 lands first, rebase onto it rather than the reverse.
