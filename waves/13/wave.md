# Wave 13: contracts and quality

- Goal:
  - Old floor tablets can't corrupt data after a deploy.
  - Contract changes are checked against every consumer.
  - The contract has no dead or undelivered parts.
  - The E2E suites cover roles, Spanish and the key flows, and run in CI.
  - Demo numbers are credible.
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push".**

## Cards
| Card | Owner | Flags | Model |
|---|---|---|---|
| T-13-1 Floor API version handshake (B-82) | architect + floor-engineer + backend-foundation | floor-correctness | opus |
| T-13-2 Contract CI and versioning (B-83) | architect + platform-sre | — | sonnet |
| T-13-3 Contract drift cleanup (B-104, B-110, attributes drift) | architect | — | sonnet |
| T-13-4 E2E coverage and CI (B-22, B-97): roles, Spanish, flows, property tests, axe in CI | qa-engineer | — | sonnet |
| T-13-5 Realistic seed efficiency (B-111) + the seed locale for floor staff | backend-foundation | — | sonnet |

## Ownership split (r1, product-manager + architect review)

**Batch 1 — run in parallel (3 agents):**

| Card | Owns (exclusive) |
|---|---|
| T-13-1 | `invai-contracts/src/contract/_base.ts` (`CLIENT_TOO_OLD` in `COMMON_ERRORS`) + new `invai-contracts/src/compat.ts` (version helpers); `invai-backend/src/api/orpc.ts`, `src/lib/env.ts`, `src/lib/errors.ts`; `invai-floor/src/api/rpc.ts`, `src/api/errors.ts`, `src/outbox/db.ts`, `src/outbox/outbox.ts`, its update-needed screen + `src/i18n/*`; `invai-docs/decisions/` (new ADR, AC4) |
| T-13-4 | `invai-web/e2e/**`, `invai-web/playwright.config.ts`, `invai-web/.github/workflows/ci.yml`; `invai-floor/e2e/**`, `invai-floor/playwright.config.ts`, `invai-floor/.github/workflows/ci.yml`; `invai-backend/.github/workflows/ci.yml` (new e2e job only); the Shopify OAuth-state test file; `fast-check`/`@axe-core/playwright` devDeps in web + floor |
| T-13-5 | `invai-backend/src/db/seed/builder.ts`, `src/db/seed/data.ts` only |

No file overlap between these three, and none of them touch `invai-contracts/package.json`, so they don't collide on the version bump either.

**Batch 2 — sequenced after T-13-1's contracts commit lands (same repo, same `package.json.version` field):**

| Card | Owns | Waits on |
|---|---|---|
| T-13-3 | `invai-contracts/src/contract/*.ts` (procedure removals), `src/events.ts`, `src/schemas/*.ts` (attributes shape, `Org.demoOwned`), `src/contract.ts`; `invai-backend` routers for the removed/used procedures, `events.ts` emit sites, `src/integrations/imaging/client.ts` (contract test); `invai-web/src/features/demo/is-own-demo.ts` | T-13-1's contracts commit (both bump `package.json` version + `CHANGELOG.md`; T-13-3 rebases its bump on top so there's one clean version history, not two agents racing the same line) |
| T-13-2 | `invai-contracts/.github/workflows/ci.yml`, `package.json` (`check:consumers` script, semver-check script), `README.md`, `CHANGELOG.md` header | T-13-1 and T-13-3's contract changes (its "every change bumps the version" check needs a real precedent to validate against, and its consumer-CI checkout needs both repos' contract edits to already exist) |

T-13-1 and T-13-3 could theoretically run wall-clock in parallel since their contracts edits touch different files, but **only one may hold the `package.json` version bump + `CHANGELOG.md` entry at a time** — land T-13-1's contracts commit first, then T-13-3 bumps again on top of it.

## T-13-1: version-handshake design (r1)

- **Header:** `X-Contract-Version`, sent by `invai-floor/src/api/rpc.ts` on every request (added to the `RPCLink` `headers()` callback alongside `Authorization`), value = `@invai/contracts`'s own `package.json` version at floor's build time (re-export it as a constant, e.g. `CONTRACT_VERSION`, from `invai-contracts/src/index.ts` — floor already depends on the package, so no new dependency).
- **Minimum version:** lives in the **backend**, not in contracts — `MIN_FLOOR_CONTRACT_VERSION` in `invai-backend/src/lib/env.ts` (env var, defaults to the current contracts version at deploy time). Contracts is shared by web and the vendor portal too, which don't need this floor-specific gate; keeping the floor's minimum in backend config lets ops hold it back during the ADR's N-day grace window (AC4) without a contracts release. Compare with plain semver `>=` (0.x rule: compare `[major, minor, patch]` numerically).
- **Enforcement point:** the `guard` middleware in `invai-backend/src/api/orpc.ts`, gated on `meta.auth === "floor" || meta.auth === "station"` (station covers `floor.login` itself, so an old tablet gets the update screen at first contact, not after PIN entry). Missing header on a floor/station call is treated the same as too-old.
- **Error code:** `CLIENT_TOO_OLD`, added to contracts `COMMON_ERRORS` (`_base.ts`), HTTP status **426 Upgrade Required** (the correct semantic — distinct from `401`/`403`), `data: { minVersion: string, current: string | null }`. Floor's `classifyStatus` (`src/api/errors.ts`) gets a new `FailureKind` (`"tooOld"`, not retryable) so the outbox never retries it and the UI shows the T-4-4 "Update needed" screen instead of the PIN/auth screen.
- **Outbox park reason:** add `"stale_version"` to `ParkReason` (`invai-floor/src/outbox/db.ts`). Stamp every `OutboxEntry` with the `contractVersion` active when it was enqueued (new field, captured from the same constant sent in the header). On replay (`flushOutbox`), if the entry's stamped version is older than the running app's version and the server rejects it (any 4xx, not just `CLIENT_TOO_OLD` — a same-day contract-deprecation removal fails as a plain shape/validation error), park it as `"stale_version"` instead of the generic `"rejected"`, and raise the lead alert on that reason specifically (distinct from "bad input, ask the customer" style rejections). If the server still accepts the old shape (within the deprecation window), it replays and completes normally.

## T-13-3: unused procedures (r1)

From audit A-FE's no-UI list. Recommendation per procedure — "use" means wire up a UI entry point this wave/next; "remove" means run `contract-deprecation` now (all are internal-only, no vendor/partner traffic, so removal can skip the ADR wait-out and go straight to release 1+2 in one wave per the skill's step 6 exception for non-partner-facing procedures... no — skill still requires the deprecation period; call this out to the architect for the removal cards):

| Procedure | Verdict | Why |
|---|---|---|
| `finance.adSpend.*` | **Use** | Ad spend is seeded and shown nowhere; `analytics/profit.tsx` already renders profit — add an ad-spend panel there instead of removing real data capture. |
| `inventory.purchaseOrders.create/update` | **Use** | PO list exists (`inventory/purchase-orders.index.tsx:81`, B-86) with no create/edit entry point — this is the missing half of a shipped screen, not dead code. |
| `inventory.count` | **Use** | Cycle count is core inventory-accuracy workflow (also an E2E gap in T-13-4's "stock adjust" flow) — needs a UI, not removal. |
| `inventory.settings.*` | **Use** | `InventorySettings` schema exists (`inventory.ts:196`, B-86) with no settings screen. |
| `production.reprints.*` | **Use** | Floor already calls `production.reprints.request` (`invai-floor/src/api/rpc.ts:143`); the web side (reprint queue/list for a lead) is the missing consumer. |
| `production.bins.list` | **Use** | Floor calls `bins.assign`/`bins.release`; `list` backs a bin-status view that doesn't exist yet on web. |
| `production.scanBatch` | **Remove** | No caller anywhere (floor scans one at a time via `production.scan`); looks like a leftover from an earlier design. Run `contract-deprecation`. |
| `orders.setTags` | **Use** | Tag filters exist in Order Hub (`orders/index.tsx:180-193` tab counts); tagging UI is the missing piece. |
| `orderItems.setRush/setFlag/setArtwork` | **Use** | `setArtwork` backs the manual-map/override flow already documented in the module map; rush/flag are small additions to `order-detail.tsx`. |
| `channels.imports/health` | **Use** | `settings/channels.tsx:42` reads only `import` results (B-85); `imports`/`health` back the missing connection-health surface. |
| `stations.revokeToken` | **Use** | `settings/stations.tsx:121` (B-92) has no revoke action; security-relevant, should ship, not be removed. |
| `ai.listings.publishStatus` | **Use** | `listings/drafts.$draftId.tsx:170` needs publish-status polling (B-89 area). |
| `ai.credits.ledger` | **Use** | Billing/usage screens show credit totals but not the ledger; low effort, real user value (support debugging "why did my credits drop"). |

Net: **12 of 13 to wire up, 1 (`production.scanBatch`) to remove.** Flag to the tech lead: T-13-3's card only budgets for "list them"; wiring up 12 procedures' UI is real feature work that likely doesn't fit inside T-13-3's own scope/time — split the "use" set into its own follow-up cards (or T-13-3 lists them for the backlog and only performs the one removal + the other three ACs (events, `Org.demoOwned`, attributes shape, imaging contract test)).

## T-13-4: CI time-budget check (r1)

**Not realistic as scoped, without changes.** Evidence:
- Both `invai-web/playwright.config.ts` and `invai-floor/playwright.config.ts` are pinned to `workers: 1`, `fullyParallel: false`. Current baseline: web `pnpm e2e` ~1 min (15 specs), floor `pnpm e2e` ~3 s (1 spec), API golden path ~10 s. AC3 alone adds ~14 new web flows and 4 new floor flows; AC1 adds 5 role specs; AC2 adds 2 Spanish smoke passes; AC5 adds axe scans on every screen visited. Serially, that's a low-single-digit-minutes-per-suite baseline growing to a plausible 5–8 min for web alone, before axe and property tests, and before counting the fresh seed + service startup + the documented **65 s wait** between API and web E2E phases (audit A-QA) that today's manual sequence relies on.
- **Neither backend, web nor floor CI currently runs any E2E** — AC6 is adding this from zero, not extending it, so the "under 15 minutes" budget has to cover: Postgres/Valkey/MinIO service boot, migrate, seed (own AC in T-13-5, budgeted under 60 s), imaging up, api+worker+web/floor dev servers up, then the suites — inside three separate GitHub Actions jobs (backend, web, floor), each paying its own checkout/install/service-boot cost independently (they don't share a runner).
- Recommend to the architect: (1) read "under 15 minutes" as **per workflow/job**, not summed across all three — otherwise it's unachievable given three independent jobs already paying ~1–2 min of setup each before a single test runs; (2) turn on `fullyParallel: true` with `workers: 2-4` for the new specs where state doesn't collide (property tests and axe scans are natural candidates — they don't touch the shared seeded DB the way golden-path does), keeping the golden-path/API spec serial; (3) budget imaging and worker startup explicitly, since neither is in today's CI at all.

## T-13-5: efficiency-drop root cause (r1)

**Confirmed.** `invai-backend/src/db/seed/builder.ts:1038-1054`'s greedy row-packing (added by the T-5-3 reusable-builder refactor, commit `72c1139`) replaced the pre-refactor algorithm (commit `a061c46`, the one that produced the 86–91% numbers in `CLAUDE.md`'s lesson log) that laid out chunks in **fixed pairs of 2 per row**. The new version instead does a width-overflow shelf pack (`if (x > marginIn && x + c.widthIn > filmIn - marginIn) newRow`) over `chunk` **sorted only by `placedAt`** (order arrival time), never by width. Without a width sort, a wide item (e.g. `back`, 12 in) landing mid-row after a couple of `adult` items (10.5 in) forces an early wrap and leaves the rest of that row's ~22 in width unused — the old fixed-pairs version didn't have this failure mode because two arbitrary items were always placed regardless of fit. Two later, unrelated commits compound it further: `8b728b1` (`LABEL_HEIGHT_IN` 0.35→0.42 in, +0.07 in per row) and `5ba3c8f` (new 0.45 in `HEADER_HEIGHT_IN` band per sheet), both real production-accuracy fixes (T-9-2/B-79) that add overhead the row-packer's utilization math doesn't compensate for.
- **Fix for the T-13-5 builder:** sort each `PER_SHEET` chunk by `widthIn` descending (first-fit-decreasing) before the row-fill loop at line ~1045, restoring the tight packing the pairs version got by luck from the size mix being ~60% one width. This is a one-line change (`chunk` → `[...chunk].sort((a, b) => b.widthIn - a.widthIn)`), keeps the real `LABEL_HEIGHT_IN`/`HEADER_HEIGHT_IN` overhead intact (don't undo those — they're correctness fixes), and should be verified against the 85–92% target on a full 300-order seed, not just spot-checked.
- **Decisions (tech lead, 2026-09-26):**
  - T-13-3 removes only `production.scanBatch` (via contract-deprecation) and does the drift items (events, `demoOwned`, attributes, imaging contract test). The other 12 unused procedures stay, harmless, and become backlog B-112 (wire UIs as screens need them).
  - T-13-4's 15-minute CI budget is per repo job; parallelize the specs that don't depend on shared state.
- **Decision (tech lead, 2026-09-26):** T-13-5 seed film efficiency of 83% average (77–87%) with real imaging `/nest` is accepted as realistic. The 85–92% target isn't reachable with this art mix because 12 in back prints can't pair. Commit `3bc8f53` needs a light review. The seed took 211 s under host contention; watch it in CI.
- **Grants approved after the fact (tech lead, 2026-09-26):** T-13-1's CORS header line in backend `app.ts`, the `email-gate.test.ts` floor header, and the floor `App.tsx`, `UpdatePrompt.tsx`, `sync.ts` and `SyncStatus.tsx`. Runbook: add `MIN_FLOOR_CONTRACT_VERSION` (B-106).
- The workspace moved to `/Users/bekbolsun/invai` on 2026-09-26 (owner), out of the iCloud-synced Desktop. All paths in prompts use the new location.
- **Grant (tech lead, 2026-09-26):** T-13-4 may edit the web and floor `e2e/**`, the CI workflow E2E steps in backend, web and floor, and the load-flaky Shopify OAuth-state tests.
- **Grant (tech lead, 2026-09-26):** T-13-3 may make the consumer updates in backend, web and floor for its contract changes (`demoOwned` detection, attributes shape).
