# Review of T-2-6 (round 1) — invai-web `4425d5e`

- Reviewer: reviewer + backend-engineer (shipping, feature owner co-review) on Claude Sonnet 5
- Author: qa-engineer on Fable
- Verdict: **changes-required**

No formal task card file exists for T-2-6 (only `invai-docs/waves/2/reports/T-2-6-qa-report.md`); I
reviewed against that report's stated intent — the golden-path suites must correctly reflect T-2-5's
CSV-channel shipping semantics (unit ships on the carrier's first scan, not at push time) without
weakening what the golden path proves.

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web log --oneline -3 4425d5e` | commit present on top of `23f0552`/`e37e716` |
| `git -C invai-web show --stat 4425d5e` | `e2e/api-golden-path.spec.ts \| 15 +++++++++++++--`, `e2e/golden-path.spec.ts \| 16 +++++++++++++---` — owned paths only (`invai-web/e2e/**`) |
| `git -C invai-web show 4425d5e` (full diff, read) | as summarized below |
| `pnpm biome check e2e/api-golden-path.spec.ts e2e/golden-path.spec.ts` (invai-web) | **1 error** — `e2e/golden-path.spec.ts:349` needs reformatting (line too long, not wrapped) |
| `pnpm lint` (invai-web, `biome check .`) | **fails**: same error, 117 files checked, 1 error — this is a repo-wide gate in Definition of Done #1 |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | 1 removed assertion line overall repo-wide (unrelated T-2-2/T-2-4 test files also on this branch ahead of `origin/main` account for the rest); the only hit inside this commit's files is `getByText("Due today")` → replaced by `getByRole("link", { name: "Due today" })`, same check, more precise selector — not a weakening |
| `grep -n "export async function poll" invai-web/e2e/helpers/api.ts` then read it | default `timeoutMs = 60_000`, `everyMs = 750`, unchanged by this commit |
| Read `invai-web/src/routes/_app/index.tsx` (StatGrid) | the "Due today" stat card is wrapped in `<AnyLink>` (an anchor), so `getByRole("link", { name: "Due today" })` is a real, unique element; the "over capacity" banner text is not a link, so it no longer collides |
| Read full bodies of step 9 in both spec files | see below |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| Suite still proves each unit reaches `shipped` | Yes (api suite); N/A by design (browser suite) | `api-golden-path.spec.ts:352-362`: `poll(... i.state === "shipped")` on `orderItems.get`, then `expect(item.state).toBe("shipped")`. `golden-path.spec.ts` never asserted item-level `shipped` at step 9 before this diff either (only `order.status`) — unchanged division of labor, not a regression introduced here. |
| Suite still proves the order reaches `shipped` | Yes | Both files: `poll(... o.status === "shipped")` then `expect(order.status).toBe("shipped")` (`api-golden-path.spec.ts:363-368`, `golden-path.spec.ts:359-366`). |
| Poll replaces a racy single read, no sleeps | Yes | Both new polls use the existing `poll()` helper (`e2e/helpers/api.ts:123`), bounded, no `setTimeout`/sleep added by hand. |
| Relaxed shipment-status poll condition is still correct | Yes, with reasoning verified | `s.status !== "pending" && s.status !== "rated"` accepts `labeled`, `in_transit`, `delivered`, `voided` — but the golden path never voids, so in practice it accepts exactly the states that mean "a label exists and the shipment has moved past rating," which is what the next lines (`shipment?.labelKey` truthy, PDF fetch) require. It does not accept an unbought/unlabeled shipment. Reasonable given a ~3.6s scan delay can race the observer past `labeled` into `in_transit`. |
| Step 1 selector fix is a real, non-masking fix | Yes | `getByRole("link", …)` targets the actual stat-card anchor; the pre-existing failure was a genuine strict-mode collision with the capacity banner's copy, unrelated to T-2-5. Confirmed the "Due today" card renders as a link and the banner does not. |
| `pnpm lint` passes on the changed files | **No** | See blocking finding below. |

## Blocking findings
1. `invai-web/e2e/golden-path.spec.ts:349` — the new shipment-status poll condition line is too long
   for Biome's formatter and was committed unformatted. `pnpm biome check .` (= `pnpm lint`) fails
   with exit 1 on this exact line ("Formatter would have printed the following content"), which
   fails Definition of Done #1 (`pnpm typecheck && pnpm lint && pnpm test` must pass in every repo
   touched) and would fail CI/the wave gate. Concrete failure: anyone running `pnpm lint` in
   `invai-web` after this commit gets a non-zero exit purely from this line, blocking the wave gate
   until reformatted (e.g. wrap the predicate across two lines, matching Biome's suggested diff).
   Trivial to fix, but it is a real, reproducible failure as committed.

## Checks
- [x] Only owned paths changed (`git diff --stat`: `invai-web/e2e/**` only)
- [x] Nothing outside scope (no product code touched; step-1 fix is test-code-only and explained as incidental, blocking test)
- [x] Tests exercise the behavior, and none were weakened (poll conditions are equal-or-stronger than the single reads they replace; selector fix is a precision improvement, not a loosening)
- [x] Tenancy / idempotency / money / i18n — N/A (test-only diff, no product code)
- [ ] `pnpm lint` passes — **fails**, see blocking finding

## Optional notes (not blocking)
- The relaxed shipment-status condition (`!== "pending" && !== "rated"`) is correct but slightly
  coarser than strictly necessary; a comment already explains why (mid-flight `labeled` → `in_transit`
  race at ~3.6s). No change requested — noting only that if `MOCK_CARRIER_TRANSIT_HOURS` were later
  raised well above the poll's `everyMs` (750ms), the original `=== "labeled"` condition would again
  be reliably observable and this broadening could be tightened back up, but there's no reason to do
  that now.
- Consider running `pnpm biome check --write` (or equivalent) on just this line rather than a broad
  reformat, to keep the diff minimal when this is fixed.

## Verdict rationale
The substance of the change — what the golden path proves — is sound and, if anything, more correct
than before (it now matches T-2-5's real shipping semantics instead of racing them). The only blocker
is mechanical: the commit as pushed fails `pnpm lint`. Fix the one line and re-request review; round 2
should be a fast approve once lint is clean.
