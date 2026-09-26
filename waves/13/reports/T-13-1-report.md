# T-13-1 report: floor API version handshake (B-82)

Status: **done, not pushed**. Reviewed: pending.

## Commits
| Repo | SHA | What |
|---|---|---|
| invai-contracts | `35048ff` | `src/compat.ts` (`CONTRACT_VERSION`, `CONTRACT_VERSION_HEADER`, numeric semver helpers, plus a test that `CONTRACT_VERSION` equals `package.json`), `CLIENT_TOO_OLD` (426, `{ minVersion, current }`) in `COMMON_ERRORS`, bump **0.2.0 → 0.3.0**, new `CHANGELOG.md`. It landed first; T-13-3 bumps on top of it. |
| invai-backend | `586b7de` | `MIN_FLOOR_CONTRACT_VERSION` in `src/env.ts` (x.y.z, defaults to `CONTRACT_VERSION`), `clientTooOld()` in `lib/errors.ts`, `enforceFloorContractVersion` called from `guard` in `api/orpc.ts`, new `api/contract-version.test.ts` |
| invai-floor | `b5bbcd8` | Header in `api/rpc.ts`, `tooOld` FailureKind, `screens/UpdateNeededScreen.tsx` (en and es), outbox `contractVersion` stamp and `stale_version` park reason with a lead alert, tests |
| invai-docs | (this report's commit) | `decisions/0012-floor-contract-compat.md` and its README row, this report, screenshots in `reports/T-13-1/` |

## Acceptance criteria
1. **Version header.** Every floor RPC sends `X-Contract-Version: 0.3.0`, set in the `RPCLink` `headers()` next to `Authorization`. The backend minimum is the `MIN_FLOOR_CONTRACT_VERSION` env var.
2. **Old-version request.**
   - Old tablets are refused on `floor`/`station` procedures with typed `CLIENT_TOO_OLD`, HTTP 426. A missing header counts as too old.
   - The floor maps 426/`CLIENT_TOO_OLD` to the new non-retryable `tooOld` kind. `rpc.ts`'s `call()` sets a store flag, and `App` swaps in the translated "Update needed" screen.
   - The screen's button applies the T-4-4 waiting service worker when there is one. Otherwise it runs `registration.update()`, or reloads.
3. **Old queued writes.**
   - Entries are stamped with `contractVersion`. Rows saved before this change have no stamp and count as older than any version.
   - On replay, an older entry the server accepts completes normally.
   - An older entry the server refuses with any 4xx parks as `stale_version`, is always alerted (sync engine, `onReplayRejected`) and gets its own problems-sheet text in en and es.
   - While the tablet itself is too old, the flush stops and every entry stays pending with no attempt counted.
4. **Compatibility policy.** ADR 0012:
   - additive changes need no window;
   - breaking floor-facing changes keep the old input shape accepted for **14 days**, with the minimum pinned to the old version, before ops raises it;
   - every bump gets a CHANGELOG line.
5. **Tests.**
   - Backend (`contract-version.test.ts`):
     - unit tests for old, missing, current and newer versions, and the web-user exemption;
     - through the guard: `production.queue` with an old floor session gets `CLIENT_TOO_OLD`, and a current one gets OK;
     - over HTTP: `/rpc/floor/staff` returns 426 with `data` when the version is old or missing, and not 426 when it's current.
   - Floor (`outbox.test.ts`, "contract version" block):
     - `classifyStatus`, and that the version stamp is set;
     - an old entry that's still accepted replays;
     - an old or unstamped entry that's refused parks as `stale_version`, and a current one parks as `rejected`;
     - `CLIENT_TOO_OLD` keeps everything pending;
     - the sync engine alerts on `stale_version`.

## Verification
- contracts: `tsc` clean, `biome check .` clean, vitest 35/35 passing.
- backend: `tsc` clean. Biome is clean on the touched files. vitest on the touched and adjacent files passes 40/40 (contract-version, email-gate, authz, orpc, ratelimit, env, floor-auth, app), run on its own DB `t131_test` with Valkey DB 13.
- floor: `tsc` clean, `biome check .` clean, vitest 92/92 passing, `pnpm build` OK.
- **Real run** (API on :3131 against a station and PIN I seeded into `t131_test`):
  - `floor.staff` with 0.2.0 → 426 `CLIENT_TOO_OLD {minVersion:"0.3.0",current:"0.2.0"}`; with 0.3.0 → 200 with the staff list;
  - `floor.login` with 0.2.0 → 426; with 0.3.0 → 200 and a session;
  - `production.queue` as a floor session with 0.2.9 → 426; with 0.3.0 → 200;
  - CORS preflight from the floor origin now allows `X-Contract-Version`.
- **Browser:** floor dev (:5175) against the API with `MIN_FLOOR_CONTRACT_VERSION=0.9.0`. Pairing the station showed "Update needed", "This app: 0.3.0 · Needed: 0.9.0". Screenshots: `reports/T-13-1/update-needed-en.jpg` and `update-needed-es.jpg`.
- Cleanup: killed my API and vite PIDs, dropped `t131_test`, flushed Valkey DB 13, closed the browser tab.

## Decisions and deviations (please review)
- **Web user sessions are exempt** from the gate even on `auth: "floor"` procedures. `floor` mode also accepts web sessions, and web doesn't send the header, so without the exemption web calls to floor procedures would get 426.
- The version check runs **after** the auth-mode check. An anonymous call to an `auth: "floor"` procedure still gets 401, which keeps `authz.test` unchanged. `station` procedures have no auth check, so first contact still gets 426.
- `CONTRACT_VERSION` is a literal in `compat.ts`, pinned to `package.json` by a test, rather than a JSON import. That avoids import-attribute differences between Node, tsx and Vite. T-13-2's semver check can rely on that test.
- `env.ts` is at `src/env.ts`; the card says `src/lib/env.ts`, which doesn't exist.

## Edits outside the card's owned paths
Each one was needed to make the design work. Only my hunks were staged.
- `invai-backend/src/api/app.ts`: `X-Contract-Version` added to CORS `allowHeaders`, a single hunk. T-12-4 and T-12-5 hunks in the same file were left unstaged. Without it, a cross-origin floor (`VITE_API_URL` set) fails preflight on every call.
- `invai-backend/src/api/email-gate.test.ts`: its floor-session case now sends the version header, otherwise it gets `CLIENT_TOO_OLD`.
- `invai-floor/src/App.tsx`: mounts the Update needed screen.
- `invai-floor/src/components/UpdatePrompt.tsx`: exports `useUpdateReady`/`applyUpdate` so the screen reuses the T-4-4 prompt.
- `invai-floor/src/outbox/sync.ts`: alerts on `stale_version`.
- `invai-floor/src/components/SyncStatus.tsx`: the reason text for `stale_version`.

## Notes for others
- **Ops consequence:** the minimum defaults to the backend's own contracts version. Each contracts bump (T-13-3 next) therefore makes tablets update on the next backend deploy, unless `MIN_FLOOR_CONTRACT_VERSION` is pinned lower. For additive bumps, pin it to the previous version. The runbook should mention the env var; I didn't edit `runbook.md` because it isn't owned.
- T-13-3: bump from **0.3.0** and add your CHANGELOG entry above mine.
- `invai-floor/vite.config.ts` is modified in the working tree by someone else. I didn't touch or stage it.
