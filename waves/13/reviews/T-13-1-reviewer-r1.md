# Review of T-13-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: architect + floor-engineer + backend-foundation on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts log --oneline -3` / `show --stat 35048ff` | 6 files, matches owned paths (`compat.ts`, `_base.ts`, `index.ts`, `package.json`, `CHANGELOG.md`, `compat.test.ts`) |
| `git -C invai-backend show --stat 586b7de` | 6 files: `app.ts` (granted), `contract-version.test.ts` (new own test), `email-gate.test.ts` (granted), `orpc.ts`, `env.ts`, `errors.ts` (all owned) |
| `git -C invai-floor show --stat b5bbcd8` | 12 files, all owned or granted (`App.tsx`, `UpdatePrompt.tsx`, `SyncStatus.tsx`, `sync.ts` per wave.md "grants approved after the fact"; rest owned) |
| `pnpm --dir invai-contracts vitest run src/compat.test.ts` (under `perl -e 'alarm 120; exec @ARGV'`) | 1 file, 4/4 passed |
| `pnpm --dir invai-backend vitest run src/api/contract-version.test.ts src/api/email-gate.test.ts` | 2 files, 11/11 passed |
| `pnpm --dir invai-floor vitest run src/outbox/outbox.test.ts` | 1 file, 32/32 passed |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts origin/main` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-floor origin/main` | no hits |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend origin/main` | hits, but all in T-12-1/T-12-4 code (`jobs.ts`, `sweeps.ts`, retry/backoff tests) — not in 586b7de's diff, out of scope for this card |
| Read `invai-backend/src/api/orpc.ts` (guard middleware) | confirms `enforceFloorContractVersion` runs after the `switch(mode)` auth check, so an anonymous call to `auth:"floor"` still gets 401 first; `station` has no prior auth branch, so first contact gets 426 |
| Read `invai-floor/src/outbox/outbox.ts` (`flushOutbox`, `park`) | `park()` is an `db.outbox.update()` (status → `parked`), never a delete; `pruneDone` only touches `status:"done"`. `tooOld` kind isn't in `countsAsAttempt`, so it falls to `report.stoppedBy = failure; break` — flush stops, nothing counted |
| Read `invai-floor/src/i18n/en.ts` / `es.ts`, `screens/UpdateNeededScreen.tsx` | `updateNeeded.*` and `stale_version` strings present in both locales, wired into the screen and `SyncStatus` |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. Version header, backend minimum | Yes | `rpc.ts` sends `X-Contract-Version` on every call (`api/rpc.ts` diff); `env.ts:MIN_FLOOR_CONTRACT_VERSION` — see blocking finding on its default |
| 2. Old-version request → typed error + screen | Yes | `contract-version.test.ts` HTTP case: `floor.staff` with old/missing header → 426 `CLIENT_TOO_OLD`; floor `classifyStatus` maps 426→`tooOld`; `UpdateNeededScreen` renders en/es strings, T-4-4 update button reused |
| 3. Old queued writes replayed-or-parked, no silent loss | Yes | `isStaleVersion` + `park(entry,"stale_version",...)` confirmed as an update not a delete; accepted-old-shape entries replay via the normal "sent" path (no special-case rejection); `outbox.test.ts` "contract version" block covers accepted/refused/current cases |
| 4. Documented compatibility policy | Partially — see blocking finding | ADR 0012 exists with the additive/breaking/14-day rule, but the mechanism that's supposed to hold `MIN_FLOOR_CONTRACT_VERSION` at the old value for those 14 days is a mutable env-var default that silently re-resolves to "current" on every redeploy unless ops actively re-pins it each time |
| 5. Tests: old refused, current passes, old outbox replayed/parked | Yes | All three re-run above, green |

## Blocking findings
1. **`invai-backend/src/env.ts` (`MIN_FLOOR_CONTRACT_VERSION` default) + `invai-docs/decisions/0012-floor-contract-compat.md:11,26`** — the minimum defaults to `CONTRACT_VERSION`, i.e. to *whatever contracts version this backend build happens to be on*, not to an explicit, hand-maintained "oldest floor-compatible shape" marker. ADR 0012 §5 promises that during a breaking change's 14-day window "`MIN_FLOOR_CONTRACT_VERSION` stays at the last version that sends the old shape" — but nothing makes that true by default; it's true only if ops sets an explicit env-var override and that override survives *every* redeploy for the whole 14 days.
   - Concrete failure: T-13-3 lands right after this card (wave.md's batch-2 sequencing) and bumps `package.json` again. Say a later wave removes a floor/station procedure the same way (a real ADR-0012 "breaking change"). The card promises tablets 14 days on the old shape. But at the moment of that deploy, `env.ts`'s default re-evaluates to the *new* build's `CONTRACT_VERSION` unless ops's override is already in place — and if any intervening deploy in that 14-day window (a hotfix, an infra restart, a redeploy that doesn't carry forward custom env vars) drops the override, the window silently collapses to zero: every tablet still on the old build gets `CLIENT_TOO_OLD` mid-shift, with no code change at fault and no alert that the grace window broke early. This also means, more mundanely, that *every* contracts bump — including next wave's web-only changes — forces a floor update unless ops remembers to re-pin the var on that specific deploy, every time.
   - **Exact fix** (both files are inside T-13-1's owned paths):
     1. In `invai-contracts/src/compat.ts`, add a second, independently-bumped constant, e.g.:
        ```ts
        /**
         * Oldest contracts version whose floor/station-facing shapes the backend must still
         * accept. Hand-bumped only when a floor-facing breaking change ships (ADR 0012 §5),
         * alongside the CHANGELOG line that says "affects floor: yes" — never tied to
         * CONTRACT_VERSION, so a web-only or non-floor bump doesn't move it.
         */
        export const FLOOR_COMPAT_BASELINE = "0.3.0";
        ```
     2. In `invai-backend/src/env.ts`, default `MIN_FLOOR_CONTRACT_VERSION` to `FLOOR_COMPAT_BASELINE` instead of `CONTRACT_VERSION`.
     3. Update ADR 0012 §2/§6 to say the default tracks `FLOOR_COMPAT_BASELINE`, hand-raised only on a floor-facing breaking release after its 14 days close (the existing env-var override stays as the emergency/rollback lever, no longer as the thing carrying the grace-period guarantee across every intervening deploy).

## Checks
- [x] Only owned paths changed (`git diff --stat` reviewed per repo above)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; scan found no weakening in this card's own diff (backend scan hits are from other cards' commits sharing the repo)
- [x] Tenancy n/a (no new tables); idempotency: outbox park/replay stays idempotent (`clientScanId` reuse unaffected by this change); no money involved; en/es text present and correct
- [ ] Decisions recorded where needed — ADR 0012 exists but needs the correction above before it accurately describes the mechanism

## Optional notes (not blocking)
- `env.ts` vs. the card's stated `src/lib/env.ts` — the report flags this as a deviation (the file is at `src/env.ts`); confirmed that's simply where the existing file already lived, no issue.
- Nice touch: the HTTP-level test hits `floor.staff` with zero prior session state, proving 426 really does fire at first contact.
