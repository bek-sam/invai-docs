# Review of T-13-1 (round 1)

- Reviewer: qa-engineer (co-review) on Sonnet 5
- Author: architect + floor-engineer + backend-foundation on Opus 5.5
- Verdict: changes-required (deferring to reviewer/architect's blocking finding; test coverage itself is sound)

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm --dir invai-contracts vitest run src/compat.test.ts` (`perl -e 'alarm 120; exec @ARGV'`) | 4/4 passed |
| `pnpm --dir invai-backend vitest run src/api/contract-version.test.ts src/api/email-gate.test.ts` | 11/11 passed |
| `pnpm --dir invai-floor vitest run src/outbox/outbox.test.ts` | 32/32 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh <repo> origin/main` for all three repos | contracts/floor: no hits. backend: hits present but all trace to other commits sharing the repo (T-12-1 retry/backoff tests, T-12-4 privacy sweeps) — read each hit's context and confirmed none touch `orpc.ts`, `env.ts`, `errors.ts`, `contract-version.test.ts` or `email-gate.test.ts` |
| Read `invai-backend/src/api/contract-version.test.ts` in full | covers: unit-level `enforceFloorContractVersion` for old/missing/current/newer on both `floor` and `station` modes, the `user`-mode no-op, and the web-session-on-floor-procedure exemption; through-the-guard test on a real `production.queue` call; an HTTP-level test on `/rpc/floor/staff` proving 426 fires before any session exists |
| Read `invai-floor/src/outbox/outbox.test.ts` "contract version" block | covers: `classifyStatus` mapping, version stamp set on enqueue, an old-but-still-accepted entry replaying normally, an old/unstamped entry that's refused parking as `stale_version` vs. a current one parking as plain `rejected`, `CLIENT_TOO_OLD` keeping the whole queue pending, and the sync engine alerting specifically on `stale_version` |
| Read `invai-floor/src/i18n/en.ts`, `es.ts`, `screens/UpdateNeededScreen.tsx`, `components/SyncStatus.tsx` | `updateNeeded.*` (title/body/button/checking/versions) and `problems.reason.stale_version` present in both locales; screen and sync-status UI both wired to the new strings, not left as raw keys |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Version header, backend minimum | Yes | re-ran tests confirm header sent + enforced |
| 2. Old-version → typed error + translated screen | Yes | HTTP-level 426 test + en/es strings present and distinct (not machine-translated placeholders) |
| 3. Old queued writes replayed or parked, nothing silently lost | Yes | both replay and park-on-refusal branches have dedicated tests; confirmed by reading `park()` that it's a status update, not a row delete |
| 4. Compatibility policy documented | See reviewer/architect finding | out of QA's lane to adjudicate the design, but noting it here so this file isn't silent on it: the ADR text and the tests both describe the *intended* 14-day/pin behavior correctly — the gap the other two reviews found is in the env-var default mechanics, not in anything QA would catch by running tests, since the tests pass real explicit version arguments rather than exercising "what happens across a week of unattended redeploys" |
| 5. Tests: old refused, current passes, old outbox replayed/parked | Yes | all three cases directly asserted, not inferred |

## Blocking findings
None found independently in this round beyond the one already raised in `T-13-1-reviewer-r1.md` and `T-13-1-architect-r1.md` (the `MIN_FLOOR_CONTRACT_VERSION` default tracking `CONTRACT_VERSION` instead of a hand-bumped floor-compat constant). Per the wave rule that a card needs every required reviewer's file to say `approve`, this file tracks that finding as blocking too rather than approving around it.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — scan run in all three repos, hits triaged and traced to unrelated commits
- [x] Idempotency: outbox replay is unchanged where it matters (same `clientScanId`/command-id reuse); no money, no new tenant tables
- [ ] Decisions recorded where needed — ADR 0012 needs the correction described in the other two files before it's accurate

## Optional notes (not blocking)
- Would like a follow-up test (not blocking this card) that simulates the ops-override *not* surviving a redeploy mid-grace-window, once the `FLOOR_COMPAT_BASELINE` fix lands — i.e. a test that never sets the env var at all and asserts the default equals the hand-maintained constant, not whatever `CONTRACT_VERSION` happens to be that build. That would have caught this on its own.
- No golden-path E2E suite touches floor auth/version handshake yet; not this card's job (T-13-4 owns E2E), but flagging so T-13-4 knows the update-needed screen and stale_version parking are currently only unit-tested.
