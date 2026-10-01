# Review of T-P2-3 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: qa-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show edc66d9 --stat` | 1 file changed: `e2e/helpers/ui.ts` only (11 insertions, 6 deletions) |
| `git -C invai-web show edc66d9 \| grep -nE '\.skip\|\.only\|sleep\(\|allow-?list'` | no matches |
| `pnpm typecheck` (invai-web) | `tsc --noEmit`, no errors |
| `pnpm lint` (invai-web) | "Found 1 warning" in `src/content/markdown.test.ts` (pre-existing, unrelated to the diff) |
| Isolated probe in `/tmp/review-tp23` (symlinked `node_modules`, copied `ui.ts`+`api.ts`, minimal playwright config, `page.setContent` only — no dev stack): test 1 `settled(page, 1200)` against a page with one `[data-slot=skeleton]` that never clears → rejected with `settled(): 1 skeleton/spinner element(s) still present at <url>`; test 2 against a clean page resolved immediately. `node_modules/.bin/playwright test --reporter=line` → 2 passed. Temp dir deleted after. |
| `grep -rn "settled(" e2e \| grep -v helpers/ui.ts` | 50 call sites, all default timeout, none pass an explicit longer timeout — matches the report's claim |
| `grep -n "test.skip" e2e/digest.spec.ts` | pre-existing mailpit-env conditional skip, line 149, untouched by this commit |

Playwright 1.63 `FunctionAssertions.toPass` type doc (`node_modules/.pnpm/playwright@1.63.0/.../types/test.d.ts:8815`): "Retries the callback until all assertions within it pass or the timeout value is reached," with its own `intervals`/`timeout`, independent of global expect timeout — matches the probe result and confirms `toPass` only paces the poll; the callback itself contains a single `count()` (no nested auto-retrying locator action), so no hidden action-level retries are introduced.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | Diff removes `.catch(() => {})`; probe test proves the timeout path throws `settled(): <n> skeleton/spinner element(s) still present at <url>` for real, not just by inspection |
| 2 | yes | No `.skip`/`.only`/sleep/allow-list in the diff (grep above); `toPass` polls the same locator, it doesn't retry or sleep around a flaky action |
| 3 | not independently re-run (no stack started, per instructions) — author's report shows `pnpm e2e --reporter=line`: 34 passed, 1 skipped (pre-existing), 0 failed, including `market.spec.ts:197` and `screens.smoke.spec.ts`. Call-site grep is consistent with "no call site needed an explicit longer timeout." |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show edc66d9 --stat`: `e2e/helpers/ui.ts` only)
- [x] Nothing outside scope (single helper function, test-only)
- [x] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks; confirmed with a real timeout-firing probe, not just reading the diff)
- [x] N/A — no tenancy, migration, money or idempotency surface (test helper code only, risk flags: none)
- [x] N/A — no cross-cutting decision needed

## Optional notes (not blocking)
- None.
