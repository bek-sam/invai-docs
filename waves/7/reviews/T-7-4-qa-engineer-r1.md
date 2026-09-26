# Review of T-7-4 (round 1)

- Reviewer: qa-engineer on Claude Sonnet 5
- Author: backend-engineer (orders) on Claude Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git worktree add ../invai-backend-review-t74 0e16314` (+ a pinned `invai-contracts` worktree at `00bd3b3` to isolate from another agent's uncommitted `ai.ts` edits) | clean |
| `node_modules/.bin/tsc --noEmit` | 0 errors (the report's own "not mine" `shipping/service.ts:1841` failure doesn't reproduce once contracts is pinned — that error was a red herring from the shared, uncommitted `invai-contracts` tree, not from T-7-4's files) |
| `node_modules/.bin/biome check .` | clean |
| own test DB `invai_review_t74`, own Redis `/14`, `node_modules/.bin/vitest run` | **79 files, 567 tests passed** — matches the report |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend-review-t74 16ddc52` | no hits: 0 assertions removed, 74 added, no `.skip`/`.only`/mocks/loosened config |
| Grepped `invai-web/e2e/*.spec.ts` for `shipBy` | golden-path E2E never asserts an exact ship-by date/time — only `sort: "shipBy"`, `toBeTruthy()`, and `getTime() > X` comparisons |
| Read `invai-backend/src/db/seed/builder.ts:521-606` | seed's own ship-by generation (`placedAt + defaultDays * DAY`) does not call `computeShipBy`/`addBusinessDays` at all |
| Counted `it(` blocks in `import-edits.test.ts` | 11 (report says 10 for round 0; round 1 added more without updating that count) |

## Golden-path impact (the check I was specifically asked for)
No blocking impact. I checked both places ship-by numbers could break the wave gate:
- **E2E specs** (`golden-path.spec.ts`, `api-golden-path.spec.ts`, `screens.smoke.spec.ts`): every ship-by assertion is relative (`sort by shipBy`, `toBeTruthy`, `getTime() > ...`), not a hardcoded date. Orders these specs create go through the real API at test-run time, so they'll pick up the new holiday-aware `computeShipBy` automatically and won't regress from it — a run that happens to land near a 2026/2027 USPS holiday will get a slightly later ship-by than before, but nothing in these specs pins an exact value, so the gate won't fail on this.
- **Seed data** (`db/seed/builder.ts`): the demo seed computes `shipBy` with flat calendar-day arithmetic and never calls into `modules/orders/shipby.ts`. This means the seed's dashboards (e.g. the "due within 2 days" SLA count, `seed/index.ts:153`) don't reflect holiday/weekend skipping at all, before or after this card. That's a pre-existing seed-fidelity gap, not something T-7-4 introduced or regressed (`db/seed/**` isn't an owned or touched path for this card), and it doesn't threaten the golden-path gate since the gate doesn't assert specific ship-by values against that seed. Flagging it as a known gap for whoever next touches seed realism, not as a finding against this card.

## Acceptance criteria (test-coverage angle)
| # | Met? | Evidence |
|---|---|---|
| 1. Postal holidays | Yes | `shipby.test.ts` covers Thanksgiving, Christmas+weekend compounding, placed-on-a-holiday, and the 2027 Sunday→Monday-observed case, plus the Etsy-processing-days-across-Thanksgiving case. I independently re-derived every date in `USPS_HOLIDAYS` by hand (day-of-week formulas for the floating holidays, fixed dates for Juneteenth/Independence/Veterans/Christmas) — all correct against the cited ELM 518.1 and USPS newsroom sources. |
| 2. Re-import bug | Yes | Covered in the same test as the holiday case, plus exercised in the report's own webhook replay (delivery 4: same delivery replayed, no change). |
| 3. Staleness | Yes | `"ignores a payload older than the last one applied, even after a floor scan"` explicitly tests the scenario the design note (`wave.md:148`) called out as the reason to avoid `orders.updated_at`. |
| 4/5. Line cancel, edits, holds | Yes | `import-edits.test.ts` has dedicated cases for: cheapest-first cancel, pressed-units-never-touched-and-flagged-once, CSV-missing-line-cancels-nothing, routed-vs-unrouted SKU edit, quantity increase/new line, shop-self-cancel counted toward channel quantity, Walmart single-line cancel, buyer-cancel-request hold (once, stays released), TikTok ON_HOLD. This is thorough coverage of the stated matrix. |
| 6. Tests | Yes | See above; scan-test-weakening found nothing to flag. |

## Blocking findings
1. Deferring to the ownership/scope finding raised in `T-7-4-reviewer-r1.md` and `T-7-4-architect-r1.md`: `integrations/channels/csv/parse.ts` and `integrations/channels/types.ts` are touched without a `wave.md`-recorded grant to T-7-4 (that territory was explicitly assigned to T-7-1 in the plan clarifications). I re-checked this from the test-coverage side and have nothing to add functionally — the new parser tests (`"walmart: a cancelled line cancels only that line"`, `"tiktok On hold and amazon buyer-requested cancellation become holds"`) are correct and pass, and I confirmed by reading T-7-1's actual commit (`24b6790`) that it never touched `csv/parse.ts` for this purpose, so there's no live test conflict. This is procedural, not a test-quality problem, but per the review rule I can't wave it through on the strength of the report's own "Round 1 (grants from the tech lead)" label alone.

## Checks
- [x] Only owned paths changed — no (see finding 1, shared with the other two reviews)
- [x] Nothing outside scope otherwise
- [x] Tests exercise the behavior, none weakened
- [x] Tenancy / idempotency / money-in-cents / en-es — n/a beyond what's covered in reviewer-r1 and architect-r1; nothing new to add
- [x] Decisions recorded where needed — staleness design yes; CSV-parser grant no (finding 1)

## Optional notes (not blocking)
- `db/seed/builder.ts`'s ship-by generation bypassing `computeShipBy` is worth a backlog item so seed SLA numbers eventually reflect real holiday/weekend behavior, but it's not this card's problem.
- Report's "10 cases" for `import-edits.test.ts` is stale after round 1's additions (now 11); cosmetic only.
