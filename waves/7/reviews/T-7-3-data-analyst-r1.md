# Review of T-7-3 (round 1) — data-analyst co-review

- Reviewer: data-analyst on Sonnet 5
- Author: backend-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| Read `invai-docs/owner-inbox.md` OI-1 in full | Confirms $0.10/label is both OI-1's own "default if no answer" and named as the code default under its recommended option C — the card's AC2 is not preempting the owner, it's implementing what OI-1 already asks for while open |
| `git -C invai-docs diff 07ecddf~1 07ecddf -- calc/cost_model.py` | `LABEL_PRICE 0.15 → 0.10`; label revenue line now `f"Label fee revenue (${LABEL_PRICE:.2f})"` instead of a hardcoded `"($0.15)"` string |
| `git -C invai-backend diff b04849e~1 b04849e -- src/modules/billing/service.ts` | `PLAN_CATALOG.labelFeeCents`: starter 5→10, growth 4→10, pro 3→10, scale 2→10; trial stays 0 |
| `grep -n "LABEL_PRICE\|TIERS\|LABEL_FREE\|LABEL_COST" invai-docs/calc/cost_model.py` | `LABEL_COST` (EasyPost's cost to us, $0.08) and `TIERS`/`LABEL_FREE` untouched — only the revenue-side constant moved, which is exactly this card's scope |
| Cross-check the unit-economics number OI-1 cites | At $0.15 model margin ≈ 47% gross on labels (0.15-0.08)/0.15; at the new $0.10 it's (0.10-0.08)/0.10 = 20% gross on the label line alone — consistent with OI-1's text that the code's 2-5¢ fees gave ~3-6% overall margin and $0.10 gives ~60% overall margin (overall margin blends subscription + label revenue, so the two numbers aren't the same base, but both move in the direction OI-1 describes) |

## Money-math / model-fidelity checks
- **Unit consistency:** `PLAN_CATALOG.labelFeeCents = 10` (integer cents, per the repo's money convention) and `cost_model.py`'s `LABEL_PRICE = 0.10` (dollars) are the same number expressed in two units — `10¢ = $0.10`. No off-by-100 error.
- **No silent scope creep into the other OI-1 gaps:** confirmed the diff does not touch `TIERS` (Scale's $1,499 model price vs. the code's `custom`/uncapped is still there, correctly listed as open in the report), does not add or remove any AI-design cost/revenue lines, and does not change how free pilots are booked. This card's AC explicitly excludes these, and the diff honors that — nothing to flag as incomplete-but-hidden.
- **Reduces future drift risk:** the printed revenue-line label used to be a hardcoded string (`"Label fee revenue ($0.15)"`) that would have silently gone stale the next time `LABEL_PRICE` changes. It's now an f-string reading the live constant, so the two can't diverge again the way they just did (model said $0.15, code said 2-5¢, and neither table caught it before OI-1). Small but real hygiene improvement, in scope ("the cost model matches the code").
- **Trial plan and the model:** the model computes label revenue as a flat `labels * LABEL_PRICE` without splitting by plan tier, so it implicitly assumes every label is billed at the paid rate. That's a pre-existing simplification (not introduced or worsened by this diff) and is separate from OI-1's free-pilot gap already logged as open — not this card's AC, not blocking, but worth a one-line note for whoever next touches the model: if trial/pilot shops generate a meaningful share of `labels_month`, the model currently overstates label revenue slightly by billing them at the paid rate too. Flagging for the backlog, not this review.

## Acceptance criteria (data lens)
| # | Met? | Evidence |
|---|---|---|
| Cost model matches the code | Yes | `LABEL_PRICE` (0.10) = `PLAN_CATALOG.labelFeeCents` (10¢) exactly; comment cross-references OI-1 and the catalog by name |
| OI-1's other three gaps stay open, not closed as a drive-by | Yes | No diff to `TIERS`, AI-design lines, or free-pilot revenue booking; report explicitly lists all three as still open |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`calc/cost_model.py`)
- [x] Nothing outside scope
- [x] No tests in this repo to weaken (docs-only diff here; backend test-weakening scan covered in the reviewer's file, clean)
- [x] Money/units consistent between the model (dollars) and the code (integer cents)
- [x] Decisions recorded where needed: OI-1 left open and correctly cited as the source of the $0.10 default, not answered by this card

## Optional notes (not blocking)
- Once OI-1 is answered, both `PLAN_CATALOG.labelFeeCents` and `cost_model.py`'s `LABEL_PRICE` need the same one-line edit — the `// see OI-1` comment and the model's comment both point at each other, which makes that future edit easy to find in either direction. Worth keeping that cross-reference alive if the number moves again.
- The model's flat-rate label revenue (no split by plan or trial/paid status) is a separate, pre-existing simplification unrelated to this card; noting it here only so it doesn't get rediscovered as a "new" bug later.
