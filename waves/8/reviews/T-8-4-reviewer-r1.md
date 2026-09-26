# Review of T-8-4 (round 1)

- Reviewer: reviewer on sonnet
- Author: ai-engineer + web-engineer on sonnet
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend diff --stat a32b682 f3b0eea` | 4 files, all within owned paths (`trademark.ts`, `service.ts`, `service.test.ts`, `router.ts`) |
| `git -C invai-web diff --stat 5c6ab28 98a47a9` | 4 files, all within owned paths (`drafts.$draftId.tsx`, `confirm-dialog.tsx`, `i18n/en.ts`, `i18n/es.ts`) |
| backend worktree at `f3b0eea`: `tsc --noEmit` | clean |
| backend worktree: `biome check .` | "Checked 268 files... No fixes applied" |
| backend worktree: `tsx src/db/migrate.ts` against a copy of `invai_test` | "up to date" (T-8-4 needed no new migration, per report) |
| backend worktree: `vitest run src/ai/ai.test.ts src/modules/ai/service.test.ts src/modules/channels/listings.test.ts` | 56/56 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend a32b682` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web 5c6ab28` | no hits |
| New-test-fails-on-base-code: archived `a32b682`, dropped in the new `service.test.ts`, ran `vitest run src/modules/ai/service.test.ts` | 3 of the 4 new gate tests failed against the old code (`recordTrademarkReview` didn't exist; `publishDraft`/`exportListingsCsv` had no gate at all) — real proof of AC2 and AC4 |
| web worktree at `98a47a9`: `tsc --noEmit` | clean |
| web worktree: `biome check .` | "Checked 143 files... No fixes applied" |
| web worktree: `vite build` | succeeds, same pre-existing >500kB chunk warning noted in the report, unrelated |
| `grep -rn "acknowledgeRisk" invai-backend/src invai-web/src invai-contracts/src` | only in the deprecated, unused contract input field and comments/tests explaining its removal — no live bypass path |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Blocked range (>=60), no override | Yes | `assertTrademarkGate` in `trademark.ts:186-206` throws `HIGH_TRADEMARK_RISK` unconditionally for `riskLevel === "high"`, before checking `reviewed` at all. `approveDraft` no longer takes `acknowledgeRisk`; router ignores the contract's (deprecated) input flag. Test "`>= 60` blocks even after a review is recorded" forces a `trademarkReviewedBy` directly onto the row and still gets blocked. Web: no "approve anyway" path exists; the old `ConfirmDialog`/flag is removed. |
| 2. Review range (25-59) needs recorded review | Yes | `recordTrademarkReview` (`service.ts:673-716`) requires `riskLevel === "medium"` (409 `TRADEMARK_REVIEW_NOT_APPLICABLE` otherwise), sets `trademarkReviewedBy/At/Note`, audit-logs `listing_draft.trademark_review` with `{riskScore, note}` — matches wave.md Contract stub A exactly, confirmed against `invai-contracts/src/contract/ai.ts:114-124`. Report's real-DB spot check found the matching audit row. |
| 3. Low range (<25), no gate | Yes | `assertTrademarkGate` returns immediately unless `riskLevel` is `"high"` or `"medium"`; test "< 25 publishes clean" passes. |
| 4. Enforced live in backend, current field, not cached | Yes | All three call sites (`approveDraft` service.ts:625, `publishDraft` :991, `exportListingsCsv` :956) call `assertTrademarkGate` against `row.trademark` from a fresh `loadDraft(tx, ctx, id, true)` (`for update`) inside that call. Test "re-checks the current trademark field live..." approves at low risk, mutates the row to high afterward, and confirms both `publishDraft` and `exportListingsCsv` still block — and this test fails against the pre-card code (no gate existed there at all), which is real proof, not just an assertion that passes either way. |
| 5. Quality: en/es, tests per range | Yes | `i18n/en.ts`/`es.ts` diffs are 1:1 (6 new keys each, 3 orphaned keys removed from both, grep confirms nothing else references the removed keys). Backend has one test per range plus the live-recheck case; `scan-test-weakening.sh` found no hits in either repo, and the existing high-risk test was strengthened (now asserts the block persists across repeated attempts and only clears once the trademarked text is edited away), not loosened. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots) — scan clean, and the 4 new gate cases run against a real Postgres DB, not mocked
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — no new tables; all handlers still wrapped in `withTenant`; `recordTrademarkReview` uses the existing `trademark_review` audit action; no money/idempotency surface in this card
- [x] Decisions recorded where needed — wave.md already carries the contract stub (T-8-1 landed first per the batch-2 sequencing); no new decision needed

## Optional notes (not blocking)
- The report flags no live browser pass was done for the review dialog/banner; I traced the diff instead of driving a browser (token budget, and the behavior underneath is fully covered by real-DB integration tests). Confirmed by code reading, not screenshots: `onError` on both `approve` and `publish` mutations opens the review dialog only on `TRADEMARK_REVIEW_REQUIRED` (not on `HIGH_TRADEMARK_RISK`, which has no dialog and just shows the server message next to the always-visible panel); the banner's three text branches (`trademarkNoticeHigh`/`Medium`/`Reviewed`) match the three gate states; `RelativeTime` and the `bg-danger`/`bg-warning` tokens used in the banner are real exports/tokens already used elsewhere in `invai-web`. If either co-reviewer wants a browser pass on this, it's a small follow-up, not a blocker.
- `recordTrademarkReview` has no draft-status precondition (can be recorded on a `needs_review` draft before anyone tries to approve). This matches wave.md's contract stub verbatim and is called out as a deliberate decision in the report — not a gap.
