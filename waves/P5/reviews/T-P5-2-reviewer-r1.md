# Review of T-P5-2 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: backend-engineer on Opus 5.5 (card model: sonnet)
- Verdict: approve

## Evidence I re-ran (own worktree `/tmp/p5-rev-t2` at 0aa67d8, own DB `invai_rev_p5t2`, Redis 13; both removed after)
| Command | Result |
|---|---|
| `tsc --noEmit` (whole repo) | exit 0 |
| `biome check .` (whole repo, clean tree, no other agents' WIP) | 458 files, no issues |
| `vitest run src/modules/catalog src/modules/orders/mapping.test.ts src/modules/orders/preview-backfill.test.ts` | 5 files, 25 passed (then "close timed out" on 2 Vite servers, exit only) |
| Red on base: `service.ts` = `git show 19a85c3:`, `preview-backfill.ts` removed | AC1 test x, AC3 test x, `preview-backfill.test.ts` fails (module missing); AC2 keep-test green (vacuous on base, as the report says) |
| Mutation: `stillReferenced` check disabled | AC2 keep-test goes red, so it carries weight |
| Mutation: drop `artworkKey IS NULL` + `artworkStatus='none'` guards | "own artwork / existing key untouched" test goes red |
| `scan-test-weakening.sh invai-backend 19a85c3` | 2 `expect.any` hits + untracked `timeline.test.ts` are other agents' WIP; `git show 0aa67d8` has 0 skip/only/mock/expect.any and 0 removed `expect(` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `service.ts:240-269` reads old `preview_key`s in the tx before the delete; `afterCommit` hook (router opens the outer `withTenant`, `router.ts:21`, so the hook runs after commit, `db/client.ts:62`). `cleanupOldPreviewKeys` re-reads all four R2 columns in a fresh `withTenant` and skips referenced keys; `deleteObject` errors are a warn log, and hook errors are caught by `runHooks`. AC1 test (real MinIO) red on base, green on head |
| 2 | Yes | candidates need `isCompanyKey` and the `${cid}/preview/design/` prefix (`service.ts:250-254`); originals, sheets and labels can't qualify. Code-read only, no test (note 2) |
| 3 | Yes | `preview-backfill.ts` is R2's SQL, guarded by `IS NULL`/`'none'`, plus an explicit `company_id` filter. Called only when the guarded `design_files` write lands, in the same short `withTenant` (`service.ts:475-488`). Unit tests cover idempotency, own artwork, an existing key and a second tenant. The integration AC3 test is red on base |
| 4 | Yes | re-proved above; the AC2 keep-test is paired with AC1 and was mutation-proved |

## Blocking findings
none

## Checks
- [x] Only owned paths: 4 files, `catalog/service{,.test}.ts`, `orders/preview-backfill{,.test}.ts`
- [x] Nothing outside scope: no migration, no contract change, no seed change, no sweep
- [x] Tests exercise the behavior; none weakened (see the scan row)
- [x] Tenancy: no `withSystem`, `withTenant` everywhere, no new table; idempotency: the `IS NULL` guard; no money, no strings
- [x] Decisions: follows R2 exactly; the known windows (crash before the hook, a mapping race) are listed in the report

## Optional notes (not blocking)
1. R2's backfill has no item-state filter. Take a shipped item that was mapped while its file had no preview, and a later replace whose new file renders: that item gets the new art's thumbnail, not the art it was printed with. Architect's call. Flag it for a later card if history accuracy matters.
2. No test pins the prefix filter or the `item_artwork`/`gang_sheets` reference checks. Today a mutation there would survive. One test with a non-preview key in `design_files.preview_key` would close it.
3. The delete runs inside `scoped()` before the request returns, which adds one MinIO round-trip per old file to the PATCH latency. That's fine at today's counts.
4. I didn't re-run the live API/MinIO exercise. The integration tests run against real MinIO and `invai_test`, and the author's live run with the presser FORBIDDEN case is in the report.
5. Processes: I started no servers. I didn't flush Redis DB 13 (33 keys) because another client was attached to it.
