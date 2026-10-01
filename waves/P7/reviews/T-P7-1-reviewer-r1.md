# Review of T-P7-1 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: qa-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show --stat c33421f` | 3 files, all owned: `e2e/api-golden-path.spec.ts`, `e2e/golden-path.spec.ts`, `e2e/helpers/api.ts` (+71 -4); worktree clean |
| `pnpm typecheck` (invai-web) | exit 0. `channels.update({settings:{autoImport}})`, `c.mode`, `ref.itemCount` all type-check |
| `pnpm lint` (invai-web) | 199 files, 0 errors, 1 warning that was already there, in a file outside this diff |
| `scan-test-weakening.sh invai-web c33421f~1` | no skip/only/sleep/retry/config/snapshot hits. 1 removed assertion (`getByText("Items").toBeVisible()`): it is still there, now as `expect(itemsLabel).toBeVisible()` |
| Read `sync.ts:647-668`, `service.ts:175,455`, `schema/channels.ts:44`, `sheets.ts:201-240`, `sheets.index.tsx:347,419-426` | the hold, the merge, the defaults, the explicit-ids build path and the DOM all match what the diff assumes (details below) |
| `lsof :3171/:8071`, `ls /tmp \| grep p7-1` | nothing left over from the author's scratch stack |
| E2E suites | not run, as instructed (the gate runs both on a fresh seed). The author's 13/13 scratch run is in the report |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes (with R1's residual) | API step 5 builds with `orderItemIds: preview.items.map(...)`. On the explicit path, `collectCandidates` (`sheets.ts:207-209`) loads exactly those ids, so a late import can't reach the build. The new `expect(ref.itemCount).toBe(preview.items.length)` makes this a hard check. Both suites log the pool size. The browser locator `..`→`p.nth(1)` matches `Metric` (`<div><p>label</p><p>value</p></div>`). |
| 2 | yes | The ids come only from connections with `mode==="api" && settings.autoImport` true (the list output is merged with `DEFAULT_CONNECTION_SETTINGS`, so "unset" reads as on, which is what the poll's `=== false` check expects). `afterAll` restores exactly those ids. Playwright runs `afterAll` after a failed test. If `beforeAll` fails before the hold, `ids=[]` and nothing is touched. The forced-failure run is the author's evidence; I did not re-run it. |
| 3 | yes | No assertion loosened. The ≥0.8 check on full sheets (`api-golden-path.spec.ts:232-234`) is unchanged. No sleep or retry added. One assertion added. |
| 4 | yes | Stated in the `holdAutoImport` doc comment and in the report: one queued sync per API connection, up to POLL_EVERY_MS plus jitter, 1-3 mock orders, and the API suite is immune because it builds from the preview's ids. The measured AC5 run (2 orders landed 3.5 min after the hold) matches. |
| 5 | yes (author's run) | Times and counts are in the report. While off, 9 min with no further import after the residual landed. Back on, the next tick imported #3003 8m42s later. |

`seedOutput()`: when `E2E_SEED_OUTPUT_FILE` is unset (gate.sh and the playwright config never set it, checked with grep), it uses the same path as before, `path.join(BACKEND,"seed-output.json")`. The gate's default is unchanged.

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope. The `seedOutput` override is in an owned helper and is needed for the card's scratch-stack verification.
- [x] Tests exercise the behavior, and none were weakened
- [x] Tenancy, idempotency, money, en/es: not applicable (e2e only; owner-scoped `channels.update` writes audit rows as R1 notes)
- [x] Decisions recorded where needed (R1 in plan-architect.md; follow-up B-261)

## Optional notes (not blocking)
- `helpers/api.ts` `holdAutoImport`: if one `update` in the `Promise.all` rejects, the connections already turned off are never returned, so they are never restored. This doesn't matter today (the seed has one API connection). A sequential loop that records each id would close it.
- `golden-path.spec.ts` `afterAll`: if `restoreAutoImport` throws, `context.close()` is skipped. A `try/finally` would fix it.
- Browser suite: a residual sync landing between Preview and Build can still grow that suite's pool by 1-3. Its assertions don't pin a count, so this is cosmetic. The report states it honestly.
