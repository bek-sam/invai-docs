# Review of T-23-2 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: floor-engineer on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` (invai-floor) | 0 errors |
| `pnpm lint` (invai-floor, `biome check .`) | Checked 78 files, no fixes |
| `pnpm test --reporter=dot` (invai-floor) | 9 files / 96 tests passed |
| `VITE_API_URL=http://localhost:3000 pnpm build` | built, `index-*.js 919.01 kB / gzip 277.85 kB` (matches report) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor origin/main` | hits are all in `.github/workflows/*` from T-23-7 (a902ec3/f8af015), not in 382ad42; nothing to address for this card |
| `git -C invai-floor log --oneline origin/main..HEAD` | confirmed only 382ad42 is this card's commit |
| `git -C invai-floor diff --stat origin/main` / `git status --short` | only files listed in the commit; clean tree after my probes |
| Live probe: floor dev server on :5189 (`pnpm dev --port 5189 --strictPort`), demo mode `?demo=1&dev=1`, PIN 1155 (Pedro Presser), Playwright script | see below; server stopped, port confirmed free |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `REPRINT_REASONS` in `invai-contracts/src/schemas/production.ts:296-320` includes `under_cure`/`cracking`; both keys present in `src/i18n/en.ts:267-268` and `es.ts:271-272`. `ProblemDialog`/`ReasonDialog` already iterated the full enum before this card. |
| 2 | yes | Live probe (demo #1053, `demoMaintenanceStation: "press"`): scanning transfer+blank produced full-screen `data-tone="blocked"`, red panel, X icon, "Press under maintenance. Ask a lead." — visually and structurally distinct from the green `ok` tone (`ResultPanel.tsx` TONE map) and from the `error` audio tone (`feedback.ts`). `mismatch.station_maintenance` key traced through the generic `viewFromResult`/`blockedReason()` path (`src/scan/result.ts:59`, `src/outbox/outbox.ts:154-222`) with no new logic, confirming the report's claim that no other code change was needed. Backend-side maintenance-vs-offline-`scannedAt` correctness was already reviewed under T-22-4 (own memory note `floor-offline-replay-checks`); this card only adds the floor copy. |
| 3 | yes | Report screenshots plus my own live probe: pick queue shows "Old transfer (45d)" badge on #1044 (amber `AgeWarning`, `common.tsx:662-675`); `PressResult`/`TransferCard`/queue rows read `transferAgeWarning` but never gate `nextAction` or block a press — confirmed by reading `PressStation.tsx:390-397` (warning renders only inside the `tone === "ok"` block, never `blocked`/no early return). |
| 4 | yes | `QueueItem.blank.shelf`/`binCode` sourced straight from the contract (`invai-contracts/src/schemas/production.ts:159-160`, added under T-22-4); `PickStation.tsx:582-590` renders both; dead `FloorApi.shelfOf()` stub correctly removed from `types.ts`, `rpc.ts`, `demo.ts`. |
| 5 | yes | Live probe with `--use-fake-device-for-media-stream`: `getUserMedia` call count is 0 through PIN entry, station selection and Press-screen load, exactly 1 after tapping `[data-testid="camera-scan-button"]`. With `BarcodeDetector` deleted from `window`, tapping the button gives the fallback toast and 0 `getUserMedia` calls. Keyboard-wedge path (`useWedgeScanner`) untouched by this diff — still the default input, no gating added on it. |
| 6 | yes | build output above matches the report's number; `pnpm e2e` not re-run per the task's instruction (deferred to the gate). |

## Ownership and scope
`vite.config.ts` / `nginx.conf.template`: the tech lead's note accepts this as an in-role amendment (floor-engineer's own T-12-5 files), pending a separate security-reviewer co-review of the header change. I checked the diff is exactly `camera=()` → `camera=(self)` in both files, nothing else touched (`git show 382ad42 -- vite.config.ts nginx.conf.template`) — narrowly scoped, self-origin only, not `*`. Not blocking here per the tech lead's note; flagging for the security-reviewer's co-review as instructed.
All other changed files are inside `invai-floor/src/**` / owned catalogs. `git diff --stat origin/main` for this commit shows nothing outside scope.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`), plus the tech-lead-accepted `vite.config.ts`/`nginx.conf.template` amendment
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (scan script hits belong to a different card's commits, confirmed by `git log --oneline origin/main..HEAD`)
- [x] en/es text complete for every new/changed enum value (`under_cure`, `cracking`, `station_maintenance`, `camera.*`, `pick.binLabel`, `common.transferAge`); `es.ts` is typed `FloorStrings` from `en.ts` so a missing key fails `pnpm typecheck` (passed)
- [x] Demo fixtures (`src/api/demo.ts`) stay isolated: `demoMaintenanceStation` is a demo-only field stripped before the queue response (`demoMaintenanceStation: _m` destructure, `demo.ts:178`), never reaches `FloorApi`/contract types used by `rpc.ts`
- Tenancy/idempotency/money: not applicable — no new server calls, no new state transitions, purely display + one existing-enum-value plumbing

## Optional notes (not blocking)
- Pre-existing bundle overage (277.85 kB gzip vs. research 11's ≤150 KB budget) is honestly disclosed as not introduced by this card (~+1.4 KB); a backlog item for the tech lead, not this card's scope.
