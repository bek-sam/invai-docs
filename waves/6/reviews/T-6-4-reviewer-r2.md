# Review of T-6-4 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: ai-engineer on Opus
- Verdict: **approve**

Round 1's only blocker (`T-6-4-reviewer-r1.md`): the Shopify CSV branch never set a real
`Option1 Value`, so Shopify's own importer couldn't distinguish variants. Fix: backend `937ef89`.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git log 0e2822e..937ef89 -- src/ai src/modules/ai` | one commit, `937ef89`, touches only `src/modules/ai/service.ts` + `service.test.ts` — everything else on `main` between the two is other cards' work (T-7-1/T-7-2), not this fix |
| `invai-backend-r-t64-r2` (worktree @ `937ef89`) `tsc --noEmit` | clean |
| `invai-backend-r-t64-r2` `biome check .` | clean (265 files) |
| `invai-backend-r-t64-r2` `tsup` (build) | success |
| `invai-backend-r-t64-r2` `vitest run src/ai src/modules/ai` | 20/20 passing |
| `scan-test-weakening.sh invai-backend-r-t64-r2 2d4668f` (937ef89's own parent, so the scan is scoped to just this fix commit) | no hits |
| Updated Shopify test run against `git archive 0e2822e` (the r1 code the last review blocked) | **fails**: `expected 'Size' to be 'Color'` — proves the new assertions actually catch the bug r1 found, not just re-testing what already passed |

## The fix
`ExportRow` now carries `color`/`size` (display names, e.g. "Black"/"Small" — not the internal
`colorCode`/`sizeCode`) alongside `content`/`sku`. `variantRowsForDraft` (`service.ts:804-838`)
selects and passes them through instead of discarding them. The Shopify branch of `exportCsv`
(`service.ts:706-761`) now sets `Option1 Name: "Color"` / `Option1 Value: color` and `Option2
Name: "Size"` / `Option2 Value: size` on **every** row (not just the handle's first row) — matching
how Shopify's own CSV exports repeat the option-name columns on every variant row while only the
shared listing fields (Title, Body (HTML), Tags, ...) stay on the first row of a Handle. A
defensive dedupe (`seen` set of `color\0size` per handle) skips a second row that would collide on
the same option combination within one Handle, with a comment explaining why it shouldn't happen
(the `blank_variants` unique index) but choosing to skip rather than export a colliding row if it
somehow did.

Etsy/Amazon/generic branches correctly ignore the new `color`/`size` fields (destructured out,
unused) — no behavior change there, confirmed by diff.

## Acceptance criteria (delta from round 1)
| # | Met? | Evidence |
|---|---|---|
| 2. `exportCsv` — Shopify branch | **Yes now** | New test asserts, per row, `Option1 Name === "Color"`, `Option2 Name === "Size"`, and the *correct* `color`/`size` for that row's own SKU (via a `bySku` map), plus that every `Handle\|Option1 Value\|Option2 Value` combination is unique across the export. All pass at `937ef89`, fail at `0e2822e` (confirmed above). |

Every other AC was already met per round 1 and is untouched by this commit (confirmed by the diff
being confined to the Shopify branch and its data plumbing).

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — `937ef89` touches only `src/modules/ai/service.ts` and
  `service.test.ts`.
- [x] Nothing outside scope — no contract/db change, no unrelated refactor.
- [x] Tests exercise the behavior, and none were weakened — scan clean for this commit; new
  assertions proven to fail on the pre-fix code.
- [x] Tenancy/idempotency/money in cents/en+es — unaffected by this commit (no new tables, no new
  UI strings, no money fields touched).
- [x] Decisions recorded where needed — none needed.

## Optional notes (not blocking)
- Round 1's other notes (mid-turn disconnect token accounting, `ask()`'s empty-message cleanup not
  covering the disconnect path, missing screenshots) stand as filed; none were in scope for this
  round's fix and none block this card.
- The Etsy `production_partner` text issue (M-23) is unchanged — see
  `T-6-4-compliance-officer-r2.md` for this round's compliance read.
