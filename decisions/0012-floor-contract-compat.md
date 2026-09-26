# 0012: Floor contract compatibility window

- Status: accepted (2026-09-26), T-13-1 (B-82), design r1 by product-manager + architect; minimum default corrected to `FLOOR_COMPAT_BASELINE` in review r1
- Type: architecture

## Context
Floor tablets are installed PWAs. They update when someone taps "Update app", and they keep an offline outbox of scans, QC results, bin moves and packs in IndexedDB. After a deploy, a tablet can keep running an old build for hours or days. It can also replay entries that it saved under an old build. Before this decision the backend had no way to tell which contract a request was written against, so an old shape could be accepted wrongly or refused with a generic 400. The work would then be parked as "bad input" and nobody would learn why.

## Decision
1. **Handshake.** Every floor request sends `X-Contract-Version`, set to `CONTRACT_VERSION` from `@invai/contracts`. That value always equals the package's `version`, and a test enforces it.
2. **Minimum on the backend.** `MIN_FLOOR_CONTRACT_VERSION` is a backend env var. It defaults to `FLOOR_COMPAT_BASELINE` in `@invai/contracts` (`src/compat.ts`), a hand-maintained constant separate from `CONTRACT_VERSION`: the oldest contracts version whose floor/station shapes the backend still accepts. A contracts version bump alone never moves it. The `guard` in `orpc.ts` checks it for `auth: "floor"` and `auth: "station"` procedures, including `floor.login` and `floor.staff`, so a tablet hears about it at first contact. Web user sessions calling floor procedures are exempt. A missing header counts as too old.
3. **Refusal.** A tablet below the minimum gets `CLIENT_TOO_OLD` with HTTP 426 and `data: { minVersion, current }`. The floor then shows the translated "Update needed" screen, which uses the T-4-4 update prompt. The outbox neither retries nor parks: every entry stays pending until the new build sends it.
4. **Old queued writes.** Each outbox entry is stamped with the version it was saved under. Rows from before this change count as older than any version. On replay, an entry older than the running app is sent as it is:
   - if the server accepts it, it completes normally;
   - if the server refuses it with any 4xx, it is parked as `stale_version` and raises the lead alert, instead of the generic `rejected`.
   Nothing is dropped silently.
5. **Compatibility rule for contract changes that affect the floor.** This covers any procedure with `auth: "floor"` or `auth: "station"`, and any schema those procedures use.
   - **Additive changes** need no window: optional input fields, new output fields, new procedures and new enum values that the floor never sends. Bump the minor or patch version; `FLOOR_COMPAT_BASELINE` stays where it is, so no tablet has to update.
   - **Breaking changes** are removed or renamed fields, fields that become required, narrowed enums and removed procedures. They follow `contract-deprecation`. The backend keeps accepting the old input shape for **N = 14 days** after the release that ships the new shape. For those 14 days, `FLOOR_COMPAT_BASELINE` (and so the default minimum) stays at the last version that sends the old shape. This holds across every deploy in the window with no env var to carry. Tablets keep working, and outbox entries saved under the old shape still replay.
   - After 14 days, a contracts release raises `FLOOR_COMPAT_BASELINE` to the new version by hand, with a CHANGELOG line that says it affects the floor, and the old-shape handling can then be removed. Tablets that still haven't updated see "Update needed". Their stale queued entries replay after the update, and anything the server no longer accepts parks as `stale_version`, which a lead handles.
   - Every version bump gets a `CHANGELOG.md` line in `invai-contracts` that says whether it affects the floor.
6. **Ops lever.** `MIN_FLOOR_CONTRACT_VERSION` is only an emergency override: ops can set it lower after a bad release, or higher to force an update, without a contracts release. The grace window doesn't depend on it.

## Consequences
- An old tablet can't write old shapes after the window closes, and any stale work it has queued is visible to a lead instead of lost.
- Tablets are asked to update only when `FLOOR_COMPAT_BASELINE` is raised, which happens only when a floor-facing breaking change's window closes. Web-only and additive contracts bumps never refuse current tablets (tested in `invai-backend/src/api/contract-version.test.ts`).
- Web and the vendor portal aren't gated. They reload on every deploy and don't keep an offline outbox.
