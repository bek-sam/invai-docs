# Review of T-20-2 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: web-engineer on Sonnet 5
- Commits reviewed: `invai-web` `d092a4b` (author's round-2 fix) and `6e7db2f` (QA's acceptance-file re-point)
- Verdict: **approve**

## Context
Round 1 (`T-20-2-reviewer-r1.md`) had one blocking finding and one open question:
1. **Blocking:** `recommendation-copy.ts`'s R1 peak-under-way branch rendered an empty `{{niche}}`
   slot ("The  season is on now…") when a design has no niche mapping (R1 firing from its own sales
   seasonality), unlike the backend's `render.ts`, which falls back to the peak month name.
2. **Question for the tech lead/PM:** AC4's literal example ("10.000") predated the PM's T-20-1
   decision that the whole digest uses one `es-US` number convention; the reviewer recommended
   option A (widen AC4 to `es-US`) and the tech lead amended the card same day, citing that review.

Round 2 fixes both. QA's own acceptance-file commit (`6e7db2f`) independently re-points its AC4 test
from `settings/billing.tsx` (out of this card's owned paths) to the digest page's "Plan usage" block,
matching the tech lead's amendment.

This is a fresh round-2 review (the previous reviewer run was lost to a usage-limit stop before
writing anything); I read the card (with the amended AC2/AC4), the r1 review, and the diffs cold, per
`independent-review`.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web log --oneline -6` | `d092a4b` (T-20-2 r2) on `6e7db2f` (QA re-point) on `f59438f` (T-20-2 r1) on `f5af662` (QA acceptance) — clean, no interleaving with another card |
| `git -C invai-web status --short` | clean; nothing uncommitted |
| `git -C invai-web show --stat d092a4b` | `digest-copy.ts`, `digest-copy.test.ts`, `recommendation-copy.ts` (the grant), `recommendation-copy.test.ts` — all inside the card's owned globs (components/digest, the recommendation-copy grant, their co-located tests) |
| `git -C invai-web show --stat 6e7db2f` | `e2e/digest-dates.spec.ts` only — QA's own file, not the author's to touch |
| `pnpm typecheck` (invai-web) | `tsc --noEmit`, exit 0, no output |
| `pnpm lint` (biome) | `Checked 167 files in 111ms. No fixes applied.` |
| `pnpm test` (vitest) | `Test Files 17 passed (17)`, `Tests 104 passed (104)` (103 from r1 + 1 new no-niche fallback test) |
| `VITE_API_URL=http://localhost:3000 pnpm build` | `✓ built in 1.41s`, only the pre-existing >500 kB chunk-size warning; `dist/` removed immediately after (disk near-full, per instructions) |
| `pnpm vitest run src/components/market/recommendation-copy.test.ts src/components/digest/digest-copy.test.ts --reporter=verbose` | 22/22 passed, including the two round-2 tests by name |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web 6e7db2f~1` | Deleted-assertion hits are the old (now wrong) AC4 assertions in `e2e/digest-dates.spec.ts` pointed at `settings/billing.tsx` and the old bare-`es` `localeNumber` expectation — both replaced 1:1 by the corrected, equally strict assertions. No skips, no mocks of the unit under test, no snapshot rewrites |
| Red-for-the-right-reason: copied `recommendation-copy.test.ts` and `digest-copy.test.ts` from `d092a4b` onto the pre-fix tree (`d092a4b~1`) and ran them | Both new tests fail on the old code for exactly the reviewed bug: `expected 'The  season is on now...' to be 'The September season is on now...'` (empty niche slot, the r1 finding) and `expected '10.000' to be '10,000'` (bare-`es` grouping) |
| Read `recommendation-copy.ts:8-11` (`monthName`) | Uses bare `es` locale for month names — a pre-existing, non-blocking mismatch with the digest's stated `es-US` rule that the PM's r2 review already flagged as having no visible effect ("septiembre" renders identically either way); not reproduced by this round's fix and not blocking |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Spanish heading | Yes (unchanged from r1, re-confirmed) | Not touched by round 2; `pnpm test` still green for `weekOfLabel` |
| 2 Points/unchanged, no arrow | Yes (unchanged from r1, re-confirmed) | Not touched by round 2 |
| 3 Refused page | Yes (unchanged from r1, re-confirmed) | Not touched by round 2 |
| 4 Numbers, es-US throughout the digest (amended) | **Yes, now** | `digest-copy.ts:73` `localeNumber` uses `es-US`/`en-US`; unit test `localeNumber(10000, "es")` → `"10,000"`, `localeNumber(1950, "es")` → `"1,950"`; QA's `6e7db2f` re-points its e2e AC4 to the digest page's "Plan usage" block and asserts `"10,000"` present, `"10.000"` absent, in both languages |
| 5 Peak under way, no-niche fallback (r1 finding) | **Yes, now** | `recommendation-copy.ts:48` falls back to `monthName(p.peakMonth, lang)` when `params.niche` is absent, matching the backend's `render.ts` `marketPart()`; new test asserts the exact en string and no empty/double-space slot in es. Confirmed to fail on the pre-fix code (see red-for-the-right-reason above) |
| 6 390/1440, en/es, no raw keys, targets ≥44px | Yes (unchanged from r1, re-confirmed) | Not touched by round 2; no new UI surface added |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show --stat d092a4b`: `components/digest/{digest-copy,digest-copy.test}.ts`, `components/market/recommendation-copy{,.test}.ts` — all inside `src/components/digest/**` and the `recommendation-copy.ts` grant; QA's `6e7db2f` touches only its own `e2e/**` file)
- [x] Nothing outside scope (no route, i18n catalog, `errors.ts`, or `settings/billing.tsx` change; the report explicitly and correctly leaves `billing.tsx` alone as backlog B-184, matching the tech lead's amendment)
- [x] Tests exercise the behavior, none weakened (scan clean apart from the expected AC4 re-point and value correction, both proven red-for-the-right-reason above)
- [x] Tenancy / idempotency / money-in-cents — not applicable, UI copy and formatting only
- [x] en/es text — both fixed strings render correctly in both languages per the new tests; the one pre-existing `monthName` bare-`es` gap has no visible rendering effect (month names are identical under `es` and `es-US`) and was already surfaced non-blocking by the PM's r2 review
- [x] Decisions recorded where needed — the `es-US` widening follows the tech lead's same-day amendment of AC4 (cited in both commits' messages and the card itself), which in turn follows the PM's recorded decision in `specs/weekly-digest.md`; no new decision needed here

## Optional notes (not blocking)
- `recommendation-copy.ts`'s `monthName()` still uses bare `es` instead of `es-US` for month names (line 9). No rendered difference today, but for strict consistency with the digest's now-stated "one `es-US` locale throughout" rule, a future pass could align it — the PM's r2 review already flagged this as not worth a round 3.

## Disposition
Round 1's blocking finding (empty niche slot for a no-niche R1 peak-under-way item) and the AC4
question (resolved by the tech lead's amendment, following the PM's T-20-1 decision) are both closed
by `d092a4b`, with QA's `6e7db2f` correctly re-pointing its own acceptance test to match. All checks
(`typecheck`, `lint`, `test`, `build`) pass on a clean re-run; both new/changed tests are proven to
fail on the pre-fix code. No new findings. **Approve.**
