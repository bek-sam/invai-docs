# Review of T-19-3 (round 1)

- Reviewer: reviewer on sonnet
- Author: backend-engineer (digest) on opus
- Verdict: approve

## Evidence I re-ran
All in a fresh worktree (`git worktree add invai-backend-rev-t19-3 bef6158`, `node_modules` symlinked, `node_modules/.bin/*` invoked directly to avoid pnpm's workspace-hoist reinstall on a symlinked tree), own test DB `invai_t19_rev_3`, Redis DB 10, own API port 3175 against a migrated copy of the dev DB (`createdb -T invai invai_t19_rev_3_dev`).

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` | clean |
| `./node_modules/.bin/biome check .` | `Checked 380 files … No fixes applied.` |
| `./node_modules/.bin/drizzle-kit generate --name drift_check` | `No schema changes, nothing to migrate` (0029_digest matches the schema exactly; no drift) |
| `git show bef6158 --stat` / `git show cadc338 --stat` | 23 files (all `src/modules/digest/**`, `src/db/schema/digest.ts`, `drizzle/0029_digest.sql` + meta, one line in `src/db/schema/index.ts`) + 5 files (day-1 stub, all in the card's grant list) |
| `vitest run src/modules/digest/{pure,digest,market,scale}.test.ts src/db/rls-coverage.test.ts` | `47 passed, 2 skipped` |
| `vitest run src/modules/digest/digest.acceptance.test.ts src/modules/digest/digest-market.acceptance.test.ts src/modules/digest/digest-prod-mode.acceptance.test.ts src/modules/digest/digest-consent.acceptance.test.ts` (QA-owned) | consent file green; digest/market/prod-mode files red — every red traced to a QA-owned fixture bug, see below (not a T-19-3 defect) |
| `vitest run src/api/authz.test.ts` | 1 red at line 129, confirmed real and correctly out-of-scope for T-19-3 (see below) |
| `DIGEST_SCALE=1 vitest run src/modules/digest/scale.test.ts` | large-shop build 487 ms (< 60 s budget); sweep of 1,005 shops in 69.1 s, 0 failed (well inside the 30-min budget; slower than the author's reported 33 s, consistent with shared-machine load, not a regression) |
| My own scratch concurrency test (3× parallel `buildDigest` calls, same company+week, deleted after the run, not committed) | exactly one `digests` row, no duplicate `digest_insights` fingerprints |
| Own API on :3175 (Desert Bloom copy): forced `buildDigest` for `2026-W39` twice | `ready` then `exists`, same `digestId` |
| `GET /api/v1/digest/week?weekKey=2026-W39` as owner / office / presser | owner: full digest incl. `planUsage` (`billing.read`), no `narrative` key; office: no `planUsage`; presser: `403 FORBIDDEN` (`finance.read`) |
| `POST /rpc/digest/settings/set` as office | `403 FORBIDDEN` (`org.manage`) |
| `POST /rpc/digest/get {weekKey:"2099-W01"}` as owner | `404 NOT_FOUND` |
| `me.notifications.set {digest,on}` then `deliverDigest` twice (script, `at`=Monday 07:05 Phoenix) | `{sent:1}` then `{sent:0}`; exactly one Desert Bloom message in Mailpit with `List-Unsubscribe` (https+mailto), `List-Unsubscribe-Post: One-Click`, Message-ID `digest.<digestId>.<userId>@…` |
| `POST /l/:token {k:unsubscribe}` twice | `200`/`200`, preference `off` once, `source: unsubscribe_link`; `GET` on the same token → `302` (confirm page, no state change) |
| Click link `GET /l/:token` twice | `302` to the in-app href both times; 1 row in `digest_clicks` |
| `digest.sendPreview` × 3 in one minute | `sent`, then `429 RATE_LIMITED` × 2 with `retryAfterSec` |
| Hand parity check: `getProfit` for the built week vs. the digest's glance net | both `0` cents (also asserted automatically in `digest.test.ts`: `d.net?.value === expected.totals.net`, a different function than the digest's own snapshot query) |
| Root-caused every QA acceptance red (see below) by patching only the fixture's freeze offset in a throwaway copy, re-running, reverting | confirms each red is a QA fixture defect, not a digest defect |

**QA acceptance reds, judged individually** (all in QA-owned `*.acceptance.test.ts`, not this card's paths):
- The bulk of the reds (`digest.acceptance.test.ts`, `digest-market.acceptance.test.ts`, `digest-prod-mode.acceptance.test.ts`) come from one shared bug: `mondayPhoenix(dateIso)` returns local **midnight** (`T07:00:00Z` = 00:00 Phoenix, correct per its own comment), but the tests then `freeze(monday + 5 min)`, landing at 00:05 Phoenix — before the shop's 07:00 default slot — so the sweep correctly finds nothing due and every `digest.get` afterwards is `NOT_FOUND`. I patched only the freeze offset to `+7h05m` (the author's suggested fix, sales/other dates left untouched) in a scratch copy: 11 of 17 tests in `digest.acceptance.test.ts` turned green immediately (was 0), and confirmed the same pattern independently accounts for all 4 reds in `digest-market.acceptance.test.ts` and the 1 in `digest-prod-mode.acceptance.test.ts`. Reverted the copy (`git diff` on the file is empty).
- The remaining 5 reds after that fix are each a separate, independently-verified QA fixture/assertion bug, exactly matching the author's own diagnosis in the report: AC10 reads `digest.glance.netCents`, but the contract field is `net.value` (confirmed live: the real response shape is `{net: {value, formatted, …}}`, no `glance.netCents`). AC27/AC28 assume another shop's digest for the same week key is `NOT_FOUND`, but the same sweep call also builds that other shop's own (quiet) digest for that week, so its owner legitimately gets `OK` on their own row. AC30 never builds a digest for its "Preview Tees" shop before calling `sendPreview`, so the contract correctly answers `NO_DIGEST` for all three calls (`sendPreview` only bypasses the opt-in, not the "does a ready digest exist" check — confirmed in `deliver.ts`). AC18 uses `mondayPhoenix("2026-12-07")` and expects week key `2026-W50`, but Dec 7 2026 (a real Monday, ISO week 50) is the **start** of W50, so the "last complete week" built when the sweep fires at Dec 7 07:05 is W49, not W50 — a fixture week-key mismatch.
- AC3 (`it.fails`) is the same `mondayPhoenix` bug wearing an expected-fail marker: it "passes" (fails as expected) for the wrong reason. The author's own `digest.test.ts` "New York across both DST changes: 07:00 local, not an hour off" (3 tests) passes cleanly and is a real DST proof.
- `src/api/authz.test.ts:129`: real, reproduced, and out of this card's paths. `me.notifications.*` is on `org.read` (T-19-1/T-19-4, landed before T-19-3), which now makes `me` reachable to a vendor session; digest itself stays unreachable to vendors (`finance.read`/`org.manage`). Belongs to security-reviewer per the task brief; not counted against T-19-3.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Tables, RLS, isolation | yes | migration read: all 7 tables `ENABLE ROW LEVEL SECURITY` + `tenant` policy, `company_id`-leading indexes, composite `(company_id,id)` FKs on children; `rls-coverage.test.ts` green; own scratch test found no cross-tenant leakage |
| 2 Schedule, DST, skips, catch-up, quiet hours, idempotent | yes | code read (`jobs.ts` `dueShops` SQL, `build.ts` `emailWindow`/`slotReached`) + `digest.test.ts` DST/hour tests green + own concurrency test (build called 3× in parallel → 1 row) + live double-build (`ready`→`exists`) |
| 3 Snapshot, parity, cancelled/reprint | yes | `digest.test.ts` asserts `d.net?.value === getProfit(...).totals.net` (different function); own hand check on the live copy (`getProfit` 0 vs digest glance 0); cancelled/reprint logic lives in T-19-2's shared `analyst-queries.ts` (by construction, out of this card's paths) |
| 4 D1–D8 | yes | `pure.test.ts` unit cases + DB tests (D6 hand-SQL count, D1 pinned/partial, D7 linked blank) green; config thresholds match the spec table exactly |
| 5 Ranking, suppression, skip, paused | yes | `pure.test.ts`/`digest.test.ts` green; `rank.ts` read for D1-pin/severity/vote-down/tired logic |
| 6 Market watch | yes | `market.test.ts` (4/4) green; `market-watch.ts` read: mock filter `opts.mockAllowed || !r.mock`, `isPromotable` for R1/R3 only |
| 7 Templates en/es | yes | `pure.test.ts` P1 (every rendered line = a fixed template key + allow-listed values) and AC13 (Spanish differs from English, USD stays USD, no raw keys) green; live email body read (English) |
| 8 AI summary shadow | yes | `digests.narrative` never selected in `service.ts` (grep confirms only `build.ts` writes it); `digest.test.ts` explicitly asserts `Object.keys(d)).not.toContain("narrative")`; live `digest.get` response has no `narrative` key while DB row has stored text |
| 9 Delivery | yes | live: opt-in → 1 send → 1 Mailpit message with correct headers; 2nd `deliverDigest` call → 0 sent (durable `email_sends` dedupe + per-recipient `digest_deliveries` row) |
| 10 Router/permissions | yes | live: presser `FORBIDDEN`, office no `planUsage`, office `settings.set` `FORBIDDEN`, unknown week key `NOT_FOUND`; `service.ts` `visibleByWeek` filters by `ctx.companyId` in addition to RLS |
| 11 Clicks | yes | live: `GET /l/:token` → `302` to the stored in-app href twice, 1 `digest_clicks` row |
| 12 Scale | yes | re-ran with `DIGEST_SCALE=1`: 487 ms / 69.1 s, both inside budget |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show bef6158/cadc338 --stat`; matches the card's owned globs and the three named grant lines exactly)
- [x] Nothing outside scope (web, T-19-2's prompt/validator, T-19-4's token crypto and public routes untouched by these two commits)
- [x] Tests exercise the behavior, and none were weakened — ran `scan-test-weakening.sh`; hits were a spy-wrapped `vi.mock("../market/service")` that still calls the real `listDigestMarketItems` (used to force one throw for AC16, not to fake the unit under test), a `vi.mock("../../env")` that copies `importOriginal` and only flips `isProd`/`allowMocks` for the prod-mode test, and `if (!env.isTest)` guarding the scheduler auto-registration at module load (a pre-existing pattern, not a correctness shortcut). None weaken an assertion.
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — `withSystem` appears only in `dueShops` (cross-tenant sweep, ids only) and `digest.purge` (retention by age), both commented; every write in `service.ts`/`build.ts`/`deliver.ts` runs inside `withTenant`; money fields are `*Cents` integers throughout
- [x] Decisions recorded where needed — none needed beyond what's already in the wave file (grants, migration order)

## Optional notes (not blocking)
1. Live on the dev copy, a mock R1 Market watch item rendered as "List Arizona Est. 1912 on  and stock Gildan G64000 … before September." (empty `{{channels}}`). `market-watch.ts`'s `isPromotable`/candidate builder allows an R1 item to qualify purely via `blankBelowReorderPoint` with no `params.channels`, but `render.ts`'s `R1 action` template always says "List {{design}} on {{channels}}", producing a grammatically broken line when there's no cross-listing gap. Per `specs/market-signals.md` R1 should always have a gap (so `channels` should never legitimately be empty), so this may be a wave-18 data artifact from my own worker recomputing signals with imaging down rather than a T-19-3 bug — worth a quick cross-check with the market module owner, but not blocking this card.
2. If the shadow narration step (`narrate()` in `build.ts`) throws after the digest is already committed `ready` (e.g., a process crash mid-call), there's no retry path: a later `buildDigest` call for the same week short-circuits to `{status:"exists"}` before ever reaching `narrate()` again. Low risk since it's shadow-only and never user-facing, but worth a backlog note given T-19-2's `priorRun` reuse logic implies a retry path was anticipated.
