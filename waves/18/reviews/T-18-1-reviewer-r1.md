# Review of T-18-1 (round 1)

- Reviewer: reviewer on opus
- Author: architect on fable
- Verdict: approve

Scope of review: `invai-contracts` commit `92b9260` (11 files) and `invai-docs` commit `e13cdda` (ADR 0015 + one README index row), against the card, `wave.md` "Agreed interfaces" / "Hard fences" / "Grants", and the author's report.

## Evidence I re-ran
| Command | Result |
|---|---|
| `node --version` | `v24.21.0` |
| `invai-contracts`: `pnpm typecheck && pnpm lint && pnpm test` | `tsc --noEmit` clean; `Checked 52 files ... No fixes applied.`; `Test Files 6 passed (6)`, `Tests 52 passed (52)` |
| `readlink {invai-web,invai-floor,invai-backend}/node_modules/@invai/contracts` | all three `../../../invai-contracts` (shared link untouched) |
| `invai-web`: `pnpm typecheck` | exit 0 |
| `invai-floor`: `pnpm typecheck` | exit 0 |
| `invai-backend` (shared tree, with other agents' uncommitted WIP): `pnpm typecheck` | 2 errors, both in uncommitted T-18-3 WIP `src/modules/market/compute.ts` (`./read` missing, implicit any), unrelated to the contract |
| `git archive 7ed3b4f` of `invai-backend` (T-18-3 stub router) into a sibling dir, `node_modules` symlinked, `./node_modules/.bin/tsc --noEmit` | exit 0: the stub compiles against contract 0.6.0 (dir removed after) |
| same at backend `HEAD` `9ed71b9` (stub + T-18-2 + QA acceptance tests, committed only) | exit 0 (dir removed after) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts 8713a63` | `removed=0 added=66` ... `Result: no hits` |
| `git -C invai-contracts show 92b9260 --stat` / `git -C invai-docs show e13cdda --stat` | only the card's owned paths (see Checks) |
| All 69 `key:` values in `invai-backend/src/modules/market/niches.ts` checked against `NicheKey` (`^[a-z0-9]+(-[a-z0-9]+)*$`, ≤ 64) | 0 violations, so the contract's shape check can't refuse a real taxonomy key |
| Fact check of the ADR against code: `_shared.ts:43` `publicReadPolicy` (`for: select`, `using true`); `rls-coverage.test.ts:26` `PUBLIC_READ_TABLES`, `:96` "app role cannot write the global catalogs" (`ins/upd/del`); `:13` `GLOBAL_TABLES`; `env.ts:208` `allowMocks: raw.ALLOW_MOCKS`; `src/modules/tenancy/demo-flag.ts` exists | all references resolve; ADR decision 1's exception list equals `GLOBAL_TABLES` ∪ `PUBLIC_READ_TABLES` today |

No API, worker or DB was started; no test DB created. The contract has no runtime; refused cases are proven from `roles.ts` by the matrix test and belong live to T-18-3.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | web and floor typecheck exit 0 against the shared link; `compat.ts` diff changes only `CONTRACT_VERSION` 0.5.0 → 0.6.0, `FLOOR_COMPAT_BASELINE` untouched (and asserted "0.3.0" in `market.test.ts`). Diff is additive: `contract.ts` +3 lines (import + `market`), no procedure removed or renamed; `tool_call.name` gets 4 values at the end; `tool_result` keeps `type/name/summary` and adds only optional `mock/sources/recommendations`; `AssistantMessage` adds only optional fields; no new union member. `schemas/ai.ts` → `schemas/market.ts` import has no cycle (market imports only `common`, `states`). |
| 2 | yes | `contract/market.ts`: taxonomy/get `catalog.read`, set `market.niches.manage`, list/vote `finance.read`, all default `auth: user`. `roles.ts`: new permission in `OFFICE` and `DESIGNER` (owner/admin via `SHOP_ALL`). Test "the matrix from roles.ts is exactly the agreed one" computes the role×procedure matrix via `hasPermission` and asserts designer = 3 niche procs, presser/packer/receiver/vendor = none, passes. `contract.test.ts` "list endpoints use cursor pagination" matches `\.list$` and passes with `market.recommendations.list` (`Page.extend` + `paginated(...)`). `ids` `.min(1).max(20)` tested (0 and 21 refused). |
| 3 | yes | `market.recommendations.vote` doc comment: same `{id, vote}` twice stores one vote, latest wins, output returns stored `vote` and `votedAt`; output is `MarketRecommendation` which carries `vote` (nullable enum `done|not_useful`) and `votedAt`. |
| 4 | yes | All money fields are `Cents` (signed `z.number().int()`, so a negative `netPerUnitCents` for an R3 loss-maker is representable); `confidence: Ratio` + `band: ConfidenceBand`; all instants `Timestamp` (ISO with offset), day fields `DateOnly`; `SignalProvenance {source, licence, asOf, fetchedAt, mock}` with `mock` required (test rejects it missing); every signal carries `sources: SignalProvenance[]`; `PricePosition` is a discriminated union on `available`, the `false` branch has `reason` enum of exactly the 3 values and inherits `n`. |
| 5 | yes | `DesignNichesSetInput.niches`: `array(NicheKey).max(2)` + distinct refine; `NicheKey` trims then `min(1)` (so `""`/`"  "` refused); no key list in the contract; `[]` accepted and documented as clearing the correction; `UNKNOWN_NICHE` 400 error declared for the backend's taxonomy check. |
| 6 | yes (status wording, see note 1) | `decisions/0015-global-market-cache.md`: sole new table without `company_id` is `market_series_cache`; exact column list (+ `id`/timestamps); no tenant/connection/user id, no shop free text, `query` must equal a canonical taxonomy query; `publicReadPolicy` + `.enableRLS()`, app role SELECT only; writes only in nightly `market.refreshDemand` under `withSystem` with a reason comment; unique `(source, query, granularity, period)` + idempotent upsert; job-side taxonomy validation + test; retention 7-day weekly / 30-day Census TTL, purge > 5 years; mock rule with the one-line `ALLOW_MOCKS` note; enforcement named (`rls-coverage.test.ts` `PUBLIC_READ_TABLES` + app-role-cannot-write list; market test for no `company_id`, taxonomy-only queries, refused insert, run-twice); owners named per bullet. Index row added. |
| 7 | yes | `CHANGELOG.md` 0.6.0 lists the namespace and all 5 procedures, every exported enum/schema from `schemas/market.ts` (cross-checked against the file), the permission, the 4 tool names and the optional event/message fields. |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`): contracts `CHANGELOG.md`, `package.json`, `src/compat.ts`, `src/contract.ts`, `src/contract/market.ts`, `src/index.ts`, `src/market.test.ts`, `src/roles.ts`, `src/roles.test.ts`, `src/schemas/ai.ts`, `src/schemas/market.ts`; docs `decisions/0015-global-market-cache.md` and one row of `decisions/README.md`. All inside the card's owned list. `invai-contracts` working tree clean.
- [x] Nothing outside scope: no backend/web code, no digest procedures; `schemas/ai.ts` changes limited to `AssistantEvent` and `AssistantMessage` (wave.md agreed interfaces name `AssistantMessage` explicitly).
- [x] Tests exercise the behavior, and none were weakened: scan script "no hits", 0 removed test lines; `market.test.ts` is new and imports `./schemas/market` and `contract.market`, so it cannot pass on the base commit; the matrix is computed from `roles.ts`, not hard-coded booleans.
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text: no table in this card; the ADR keeps the only non-tenant table public-read, app-role read-only, taxonomy-keyed, `withSystem` writer only in the job. Vote idempotency documented. Cents/ratio/ISO verified above. en/es labels are data (`NicheTaxonomyEntry.labelEn/labelEs`); no UI strings here.
- [x] Decisions recorded where needed: ADR 0015 + index row.
- [x] InvAI invariants: floor untouched (no floor-facing shape changed, baseline unchanged); mock provider path preserved (ADR keeps mocks in dev/test/`ALLOW_MOCKS` stages and filters at read time); contract additive.

## Optional notes (not blocking)
1. ADR 0015 status reads `accepted (2026-09-27; security-reviewer co-review on T-18-1 confirms)` before that co-review exists (`waves/18/reviews/` has no security-reviewer file for T-18-1 yet). The card says `accepted` *after* the co-review. The push gate already requires security-reviewer's approve, so this isn't blocking, but if security-reviewer objects the status line must change before the push.
2. ADR decision 1 opens with "Exactly one table may exist without `company_id`" and then lists the existing exceptions; reads fine, but "exactly one *new* table" would be less ambiguous for a future grep-based check.
3. `market.recommendations.list` takes `ids`/`rule` arrays on a `GET`. The apps use the RPC link, so this is fine; an OpenAPI consumer would need bracket-style query arrays. No action unless an OpenAPI client appears.
4. Author's own gaps stand: `invai-contracts/README.md` namespace table and permission list need a `market` row / `market.niches.manage` (not in owned paths), and `wave.md` should link ADR 0015 (tech lead).
5. Backend `pnpm typecheck` on the shared tree is currently red from uncommitted T-18-3 WIP (`src/modules/market/compute.ts` imports a `./read` that tsc can't resolve yet); nothing to do with this card, but the gate should re-check it.
