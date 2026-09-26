# Wave 13 plan review — architect, r1

Scope: contracts and quality. Read-only on code (contracts, `invai-floor/src/outbox` + `src/api`,
`invai-backend/src/api/orpc.ts` + `context.ts`, all four repos' CI workflows, `invai-backend/src/db/seed`)
plus git history on `invai-backend/src/db/seed/{builder,index}.ts`. No DB writes, no commits outside
`waves/13/**`, no push.

## Ownership split
Three cards touch fully disjoint files and none of them touch `invai-contracts/package.json`, so they run
in parallel: **T-13-1** (contracts `_base.ts`/new `compat.ts` + backend `api/orpc.ts`/`lib/env.ts`/
`lib/errors.ts` + floor `api/rpc.ts`/`api/errors.ts`/`outbox/*`), **T-13-4** (web/floor `e2e/**` +
Playwright configs + all three CI workflows, additive only), **T-13-5** (`db/seed/builder.ts` +
`data.ts` only). **T-13-3** and **T-13-2** both need to touch `invai-contracts/package.json`'s version
line and `CHANGELOG.md` — sequence T-13-3 after T-13-1's contracts commit lands, then T-13-2 last (its
consumer-CI check is only meaningful once there's a real bumped-version precedent to check against).
Full table in `wave.md`.

## T-13-1: version-handshake design
Verified against the real guard chain (`invai-backend/src/api/orpc.ts`'s `guard` middleware switches on
`meta.auth` — `"user" | "floor" | "station" | "public"`, matching `_base.ts`'s `AuthMode`) and the floor
client (`src/api/rpc.ts`'s `RPCLink.headers()` currently sends only `Authorization`; `src/api/errors.ts`'s
`classifyStatus`/`FailureKind` has no slot for "must upgrade"; `outbox/db.ts`'s `ParkReason` has 5 values,
none of which distinguish "this queued write's shape is stale").

Design, locked into `wave.md` and the card:
- **Header:** `X-Contract-Version`, added to floor's `RPCLink.headers()`; value from a new `CONTRACT_VERSION`
  constant re-exported by `invai-contracts/src/index.ts` (floor already depends on the package — no new
  wiring needed to read it at build time).
- **Minimum version:** backend config (`MIN_FLOOR_CONTRACT_VERSION` in `src/lib/env.ts`), not contracts.
  Reasoning: contracts is shared with web and the vendor portal, neither of which needs a floor-specific
  gate, and the ADR's N-day grace window (AC4) is an ops-controlled deploy-time policy, not a contract
  fact — bumping the floor's minimum shouldn't require a contracts release.
- **Enforcement:** in `guard`, gated on `meta.auth === "floor" || "station"` — station is included
  deliberately so `floor.login` itself (a station-token call, per `_base.ts`'s own comment "the PIN login
  itself") is caught, meaning an old tablet sees the update screen before it can even attempt a PIN.
- **Error:** `CLIENT_TOO_OLD` added to contracts `COMMON_ERRORS`, **HTTP 426** (Upgrade Required — the
  correct status for this, distinct from every existing 401/403/409 in the map), `data: { minVersion,
  current }`.
- **Outbox park reason:** new `ParkReason` value `"stale_version"`. Requires stamping `OutboxEntry` with
  the contract version active at `enqueue()` time (new field) so `flushOutbox` can tell "old queued write,
  new server no longer accepts its shape" (park as `"stale_version"`, lead alert) apart from an ordinary
  business-rule `"rejected"`. This is the one non-obvious addition beyond what the acceptance criteria
  state explicitly, and it's necessary — without the stamp there's no way for the client to know *why* a
  replay was rejected.

## T-13-3: unused procedures
Cross-checked every one of A-FE's 13 no-UI procedures against the actual routes/screens named elsewhere in
the same audit (e.g. `inventory/purchase-orders.index.tsx:81` for B-86, `settings/stations.tsx:121` for
B-92, `settings/channels.tsx:42` for B-85). 12 of 13 back a screen or workflow that's already partially
shipped — removing them would be removing live product surface, not dead code. Only `production.scanBatch`
has no caller anywhere in `invai-floor/src/api/rpc.ts` (floor scans one unit at a time via
`production.scan`) — recommend `contract-deprecation` for that one only. Flagged to the tech lead that
wiring up the 12 "use" verdicts is real feature work and doesn't fit T-13-3's stated scope; the card should
either shed that work to follow-up cards or restrict itself to the removal + its other four ACs.

## T-13-4: CI time budget
Checked both Playwright configs directly: `invai-web/playwright.config.ts` and
`invai-floor/playwright.config.ts` are both `workers: 1, fullyParallel: false`. Checked all four
`.github/workflows/ci.yml` files: **none run E2E today** — lint/typecheck/unit/build only. Baseline
durations from `build/qa-report.md`: web `pnpm e2e` ~1 min (15 specs), floor ~3 s (1 spec), API golden path
~10 s, plus an undocumented 65 s wait between phases (audit A-QA) in the manual sequence. AC3 alone adds
~18 new flows across web and floor; AC1 adds 5 role specs; AC2 doubles the golden-path run for Spanish;
AC5 adds an axe pass per screen. None of `fast-check` or `@axe-core/playwright` are installed yet (checked
both `package.json`s) so this is greenfield tooling, not a tuning pass. **Verdict: not realistic as a
single 15-minute number across three independent CI jobs, each of which pays its own checkout/install/
service-boot before a single test runs.** Recommended reading the budget per-workflow and parallelizing
the state-independent additions; kept the recommendation, not a card-blocking change, since it's a
clarification the QA engineer needs before writing the workflow YAML, not a design flaw.

## T-13-5: efficiency-drop cause
Confirmed via `git log`/`git diff` on `invai-backend` (not the docs repo): commit `72c1139` ("Onboarding
checklist, demo workspace and the reusable seed builder (T-5-3)") replaced the pre-refactor packing
algorithm (commit `a061c46`, "QA: numeric print sizes, realistic seed size mix... seeded sheets are laid
out from the real sizes" — the commit that produced the 86–91% figure in `CLAUDE.md`'s lesson log) with a
different algorithm: the old one placed items in **fixed pairs of 2 per row** regardless of width; the new
one (`builder.ts:1038-1054`) does a real width-overflow shelf pack but sorts the chunk only by
`placedAt` (chronological), never by size. An unsorted greedy shelf pack wastes width whenever a wide item
follows narrower ones mid-row — a classic bin-packing ordering bug, not a size-mix or spacing regression.
Two later commits (`8b728b1`, `5ba3c8f`, both T-9-2/B-79) add real per-row/per-sheet overhead
(`LABEL_HEIGHT_IN` 0.35→0.42in, a new 0.45in `HEADER_HEIGHT_IN` band) that compound the loss but are
correct and shouldn't be reverted. Fix: sort each `PER_SHEET` chunk by `widthIn` descending
(first-fit-decreasing) before the layout loop — a one-line change that doesn't touch the overhead
constants. Recommended the builder verify against a full 300-order seed run, not a spot check, since the
packing loss compounds per-sheet.

## Changes made
Same file list as the product-manager review (`wave.md`, all 5 card files, this pair of review docs).
