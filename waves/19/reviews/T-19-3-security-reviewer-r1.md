# Review of T-19-3 (round 1)

- Reviewer: security-reviewer on opus
- Author: backend-engineer (digest) on opus
- Verdict: approve

## Evidence I re-ran
Own worktree `invai-backend-sec-t19-3` (`git worktree add ../invai-backend-sec-t19-3 bef6158`, `node_modules` symlinked, `node_modules/.bin/*` invoked directly), own test DB `invai_t19_sec3`, Redis DB 9 (`REDIS_URL=...:6379/9`).

| Command | Result |
|---|---|
| `node_modules/.bin/vitest run src/modules/digest/pure.test.ts src/modules/digest/digest.test.ts src/modules/digest/market.test.ts src/db/rls-coverage.test.ts` (own DB) | 47 passed, 0 failed (re-ran twice, same result) |
| Read `src/db/schema/digest.ts` (all 7 tables) | every table has `companyId`, `tenantPolicy(<table>)`, `.enableRLS()`; every child (`digest_insights`, `digest_feedback`, `digest_clicks`, `digest_views`, `digest_deliveries`) uses a composite `foreignKey({columns:[companyId,parentId], foreignColumns:[parent.companyId, parent.id]})` (S-26), not a bare `.references()` |
| Read `digest.test.ts:573-624` "another shop's week…" | proves more than RLS-shaped equality: `digest.get`/`digest.list` NOT_FOUND and empty for shop B; `recordClick`/`feedback` on shop A's insight id NOT_FOUND for B; B inserting a `digest_insights` row that points at A's `digestId` under B's own tenant **rejects** (composite FK, not just RLS); A inserting a `digests` row carrying `companyId: other.id` **rejects** (RLS `WITH CHECK`) — this is the mutation-style proof I look for, not decoration on top of RLS |
| Read `src/modules/digest/jobs.ts` `dueShops` (line 34-68) | the only cross-tenant (`withSystem`) read on the request/schedule path selects `companies.id` and a computed local date only (no PII, no order/buyer data); reasoned in a code comment; each due shop is then built via `buildDigest` which opens its own `withTenant` |
| Read `src/modules/digest/jobs.ts` `purgeJob` (line 140-153) | the only other `withSystem` use is a retention delete by `week_start` age, no row data read back |
| `grep -n "withTenant\|withSystem" src/modules/digest/{build,deliver,service}.ts` | every read/write in `build.ts`, `deliver.ts`, `service.ts` runs inside `withTenant(companyId, …)`; no bare pool access |
| Read `src/modules/digest/service.ts` (`getDigest`, `toSummary`, `visibleByWeek`) | `narrative` is loaded into the row object (plain `tx.select()`) but every returned shape is built field-by-field (`toSummary`, then `out: Digest = {...toSummary(...), timezone, steady, …}`); no `...row` spread anywhere in the file; `grep -n "\.\.\.row" src/modules/digest/*.ts` → no hits |
| `grep -n "\.narrative" src/modules/digest/{deliver,render}.ts` | no hits: the email path (`composeEmail` → `renderModel` → `renderEmail`) never touches the stored narrative field |
| Read `src/modules/digest/build.ts` (narrate step) | only `narrativeStatus`/`narrative` columns are written by the shadow-summary step; matches the docstring "only ever updates `narrative_status`/`narrative`" |
| Read `src/modules/digest/market-watch.ts` + `build.ts:186` | `marketCandidates(recs, { mockAllowed: !env.isProd })` — mock-sourced items are dropped whenever `env.isProd` is true, independent of `allowMocks` (stricter than the market module's own `!isProd \|\| allowMocks` test-override rule, which only matters for whether recommendations are *computed*, not whether the digest *shows* them) |
| Read `src/modules/digest/service.ts` `recipients`/`FINANCE_ROLES` (line 434-482) | recipients are every active member whose **role's permission set** includes `finance.read` (`ROLE_PERMISSIONS[r].includes("finance.read")`), computed from the same static role table the permission guard uses — not a role-name string match, and there is no per-user permission override in this codebase (`grep -rn "permissionsFor" src/api/context.ts` → role-keyed only) that could diverge from it |
| Read `src/modules/digest/deliver.ts` `sendPreview` (line 234-271) + `router.ts:51` | rate-limit key `digest:preview:${companyId}:${userId}` is per caller; `companyId`/`userId` come from the session (`me.companyId`, `me.userId` in `router.ts`), never from client input, so a caller can't rate-limit-bomb another user or company by supplying ids |
| Read `src/modules/digest/service.ts` `clickTarget` (line 379-398) | filters the insight lookup on `ctx.companyId` AND the caller-supplied `digestId`/`insightId` (still tenant-scoped, RLS is a second line); returns only `action.href` already stored on the row — never builds a URL from request input |
| `grep -n "href" src/modules/digest/detectors.ts src/modules/digest/market-watch.ts` | every `action.href` is a fixed, hardcoded internal path (`/settings/channels`, `/analytics/...`, `/catalog/designs/${enc(id)}`, `COST_LINE_HREF` lookup table) with only `encodeURIComponent`-escaped ids interpolated into query strings — no detector or Market watch candidate can produce an absolute or cross-origin URL, so `clickTarget`'s "same-origin only" holds structurally, not just by convention |
| `grep -in "buyer\|shipTo\|customer" src/modules/digest/{facts,detectors,snapshot,render}.ts` | no hits: facts are counts/cents/channel/design/blank names only, matching the schema file's own comment ("No buyer PII is stored here") |
| `grep -n "log\.\(warn\|info\|error\)" src/modules/digest/{build,deliver}.ts` | every log call carries `companyId`/`digestId`/`userId`/error data only — no buyer name, email or address fields |

## Acceptance criteria (my checklist items from the coordinator's brief)
| # | Item | Met? | Evidence |
|---|---|---|---|
| 1 | RLS + isolation on the 7 new tables | yes | schema read + `rls-coverage.test.ts` green + `digest.test.ts` composite-FK/RLS-WITH-CHECK proof above |
| 2 | Sweep's cross-tenant query (`withSystem`) only selects due shop ids | yes | `dueShops` SQL selects `companies.id` + a date computation only |
| 3 | Every build/deliver runs under `withTenant` | yes | grep confirms no bare pool/`withSystem` use in `build.ts`/`deliver.ts`/`service.ts` |
| 4 | Shadow narrative text never returned by any procedure, email or render | yes | no `...row` spread in `service.ts`; no `.narrative` reference in `deliver.ts`/`render.ts` |
| 5 | Market watch drops mock items in production | yes | `mockAllowed: !env.isProd` at the one call site |
| 6 | Recipients chosen by `finance.read` | yes | `FINANCE_ROLES` derived from `ROLE_PERMISSIONS`, permission-based |
| 7 | Preview rate limit per user | yes | Redis key keyed on session `companyId`+`userId` |
| 8 | Click handler redirects only to stored same-origin hrefs | yes | all hrefs are hardcoded internal paths with encoded params; `clickTarget` never echoes request input into the returned path |
| 9 | No buyer PII in digest facts, emails or logs | yes | grep across facts/detectors/snapshot/render/logs found no buyer/customer fields |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git show cadc338/bef6158 --stat`; matches T-19-3's owned globs — `src/modules/digest/**`, `src/db/schema/digest.ts` + its migration, the three named grant lines)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — the cross-tenant test at `digest.test.ts:573` specifically proves the FK and RLS `WITH CHECK` mechanisms fail closed (not just an equality assertion that RLS could make pass by accident)
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text — the two `withSystem` call sites are both reasoned in-line and read/write no tenant data beyond ids and ages
- [x] Decisions recorded where needed — none needed for the tenancy/PII surface

## Optional notes (not blocking)
1. `market-watch.ts`'s mock-drop rule (`!env.isProd`) is stricter than the market module's own `!isProd || allowMocks` pattern — intentional (AC31 says "in production a mock-sourced item never shows", full stop), but worth a one-line comment next to `build.ts:186` noting the deliberate divergence so a future refactor doesn't "fix" it into matching the other module's rule.
2. I did not re-verify T-19-4's `sendUserEmail`/link-signing internals (out of this card's paths, already reviewed under T-19-4); my recipient/preview checks stop at the digest module's boundary with that shared helper.

## Blocked by other owners
None from this review. (The `authz.test.ts:129` item noted in the T-19-3 report is mine and is already fixed and committed at `013f3d6`, separate from this card.)
