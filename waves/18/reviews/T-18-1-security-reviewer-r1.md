# Review of T-18-1 (round 1)

- Reviewer: security-reviewer on Sonnet 5
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 92b9260` | read the full diff: `src/contract/market.ts`, `src/schemas/market.ts` (426 lines), `src/roles.ts`, `src/schemas/ai.ts`, `src/market.test.ts` |
| `git -C invai-docs show e13cdda` | read `decisions/0015-global-market-cache.md` + README index row |
| `cd invai-contracts && pnpm typecheck` | `tsc --noEmit` clean |
| `cd invai-contracts && pnpm lint` | `Checked 52 files in 43ms. No fixes applied.` |
| `cd invai-contracts && pnpm test` | `Test Files 6 passed (6)`, `Tests 52 passed (52)` |
| `pnpm test src/market.test.ts src/roles.test.ts --reporter=verbose` (rerun myself, not trusting the report's paste) | `Test Files 2 passed (2)`, `Tests 21 passed (21)` — matches the author's pasted output |
| `grep -n publicReadPolicy invai-backend/src/db/schema/_shared.ts` | `pgPolicy(table_public_read, { for: "select", to: appRole, using: sql\`true\` })` — matches ADR §3 |
| `grep -n PUBLIC_READ_TABLES invai-backend/src/db/rls-coverage.test.ts` | `new Set(["plans", "trademark_marks"])`; T-18-3's grant adds `market_series_cache` here (not yet landed — out of this card's scope) |
| `grep -n "isProd\|allowMocks" invai-backend/src/env.ts` | `isProd = raw.NODE_ENV === "production"`, `allowMocks: raw.ALLOW_MOCKS` — matches ADR's description exactly, no new bypass |
| `cat invai-backend/src/modules/tenancy/demo-flag.ts` | `isSampleWorkspace` reads `demoOwnerUserId`/`settings.demoRetiredAt`, cached, matches the ADR's third disjunct and the existing `assertNotSampleWorkspace` pattern used elsewhere |
| read `src/db/schema/ai.ts` `trademark_marks` | confirms the cited precedent: no tenant column, `publicReadPolicy` + `.enableRLS()`, filled via `withSystem` |
| read `specs/market-signals.md` "Jobs and data" | "one fetch per (canonical query, source) for all shops" |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 additive, web/floor typecheck, floor baseline unchanged | yes | `pnpm typecheck` clean in contracts; report shows web/floor exit 0; `FLOOR_COMPAT_BASELINE` untouched in diff; no new `AssistantEvent` union member, only optional fields |
| 2 permission matrix + pagination | yes | diff to `roles.ts`: `market.niches.manage` added to `PERMISSIONS`, `OFFICE`, `DESIGNER` only (owner/admin via `SHOP_ALL`); `market.test.ts` "the matrix from roles.ts is exactly the agreed one" encodes designer refused on recommendations, presser/packer/receiver/vendor refused on all five; re-ran, passes |
| 3 vote idempotent | yes | doc comment on `market.recommendations.vote` states "the same `{id, vote}` twice stores one vote... the latest wins... output returns the stored `vote` and `votedAt`"; schema carries `vote`/`votedAt` |
| 4 cents/ratio+band/ISO/provenance-with-mock/PricePosition reason+n | yes | read `src/schemas/market.ts`: `Cents` throughout money fields, `confidence: Ratio` + `band: ConfidenceBand`, `SignalProvenance.mock: z.boolean()` (required, not optional — every outside fact must state it), `PricePosition` discriminated on `available`, `false` branch carries `reason` enum (`no_compliant_source \| not_connected \| too_few_comparables`) and `n` inherited from `PricePositionBase` |
| 5 niches.set ≤ 2, no hard-coded keys | yes | `DesignNichesSetInput` (referenced, not re-pasted) tested for `[]` clears, 3 rejected, blank/dup rejected; `NicheKey` is shape-only (kebab-case ≤ 64), key list left to the backend data file per the card |
| 6 ADR 0015 | yes, with one non-blocking note below | table shape, RLS (`publicReadPolicy` + `.enableRLS()`, app role select-only), `withSystem` writer with required comment, unique index, taxonomy validation + test, retention (7d/30d TTL, 5y purge), mock rule stated correctly, enforcement named with owners |
| 7 CHANGELOG | yes | 0.6.0 entry lists every schema, procedure, permission and event addition |

## Threat model (tenancy)
- **Entry points:** none live yet (contract + ADR only, no runtime). The five `market.*` procedures are `auth: user`, gated by `catalog.read` / `market.niches.manage` / `finance.read` — never reachable by floor sessions, station tokens or vendor sessions (confirmed by the matrix test; consistent with `authz.test.ts`'s existing pattern of vendor/floor/station getting nothing outside their own surfaces).
- **The one table without `company_id`:** `market_series_cache`. Columns are fixed to `(source, query, granularity, period, value, asOf, fetchedAt, licence, mock, id, createdAt, updatedAt)` — no tenant id, no connection id, no user id, no free text. `query` must equal a canonical taxonomy query, enforced by validation in the job plus a stated test ("every stored query is in the taxonomy"; "an insert with a non-taxonomy query is refused"). This is the same shape as the existing `trademark_marks` precedent (which this review already relies on daily), so the pattern itself is proven safe.
- **Cross-tenant inference via selective fetch (the question I was asked to judge):** could the nightly refresh leak which niches other shops use by only fetching series for niches that at least one tenant currently has designs in? I checked `specs/market-signals.md` "Jobs and data": "Nightly global demand refresh: one fetch per (canonical query, source) **for all shops**." Read together with ADR §2 ("`query` must equal one of the canonical queries of a taxonomy niche, exactly... `NICHES[*].queries`") and the card's framing that the taxonomy is fixed and the same series serve every shop, the intended design is a fixed cross-product over the *entire* taxonomy × sources, computed once nightly, independent of any tenant's data — not a tenant-usage-derived subset. That closes the inference channel: presence or freshness of a row can never depend on which shop uses that niche, because every niche's queries are always fetched regardless. **Non-blocking gap:** the ADR text itself doesn't say this in so many words — Decision §4/§5 describe validation of what's stored, not the selection rule for what gets fetched. A literal reading leaves room for T-18-3 to "optimize" by fetching only niches with an active design somewhere, which would reintroduce a low-severity but real side channel (freshness pattern reveals aggregate niche popularity across tenants). I'm filing this as a new Low finding (S-34) for T-18-3 to close explicitly, not blocking this card, because (a) the authoritative spec line already directs the full-taxonomy behavior, (b) the actual leak, even if introduced, would be extremely low-fidelity (a tercile-grade aggregate signal, no company identified, nothing resembling PII or orders), and (c) it's about *implementation* of a job that doesn't exist yet, not this contract/ADR card.
- **Mock visibility rule:** `!isProd || allowMocks || isSampleWorkspace` — sound. `isProd` and `allowMocks` in `env.ts` are exactly the existing `ALLOW_MOCKS` ops-only boot flag (not a new bypass, confirmed by reading `env.ts` directly — `ALLOW_MOCKS=true` only lets a demo/staging stage boot on mocks, with a warning). `isSampleWorkspace` already exists (`src/modules/tenancy/demo-flag.ts`) and is deliberately *not* `companies.demo` (the ADR correctly notes the seeded Desert Bloom has `demo=true` but must get real behavior) — this matches the existing `assertNotSampleWorkspace` pattern used by every other adapter factory (carrier, marketplace, billing, supplier, mail), so the market module is following, not inventing, the mock-boundary convention.
- **Permission matrix:** designer is refused `recommendations.list`/`vote` (only gets the three niche procedures); presser/packer/receiver/vendor are refused all five. Both are asserted by `market.test.ts`'s exact-matrix test, which I re-ran. `market.niches.manage` is a sensible new permission — office and designer can correct a niche without needing `catalog.manage`, and it grants nothing beyond that one write.
- **Enforcing tests, named and sufficient for this card's scope:** `invai-contracts/src/market.test.ts` (permission matrix incl. exact role table, pagination on `recommendations.list`, schema round-trips for cents/ratio/provenance/PricePosition branches, event additivity, version) — all re-run, all green. The ADR correctly defers the table-existence tests (`rls-coverage.test.ts` two-edit grant; a market-module test for no-`company_id`/taxonomy-only/refused-bad-query/idempotent-refresh) to T-18-3, with owners named (backend-engineer, co-reviewed by security-reviewer and backend-foundation) — that grant is already written in `wave.md` and I will verify it directly on T-18-3's card.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed — `git -C invai-contracts show --stat 92b9260` lists exactly `CHANGELOG.md`, `package.json`, `src/compat.ts`, `src/contract.ts`, `src/contract/market.ts`, `src/index.ts`, `src/market.test.ts`, `src/roles.test.ts` (not shown above but named in the author's report), `src/roles.ts`, `src/schemas/ai.ts`, `src/schemas/market.ts` — all inside the card's owned paths. `git -C invai-docs show --stat e13cdda` lists `decisions/0015-global-market-cache.md` + one hunk of `decisions/README.md`, also owned.
- [x] Nothing outside scope — no backend/web/floor implementation in either diff; digest procedures correctly deferred to wave 19.
- [x] Tests exercise the behavior, none weakened — new test file only; no `.skip`, no loosened assertion, no mock of the unit under test found in either diff.
- [x] Tenancy (`withTenant`, RLS on new tables) — no table is created by this card; ADR 0015 specifies RLS correctly for the table T-18-3 will create, matching the proven `trademark_marks` precedent.
- [x] Decisions recorded where needed — ADR 0015 itself is the record; I confirm it as `accepted`.

## Optional notes (not blocking)
- ADR 0015 §4 ("Writes happen only in the nightly `market.refreshDemand` job...") should say explicitly that the job iterates the *entire* fixed taxonomy (`NICHES[*].queries × sources`) every run, not a tenant-usage-derived subset — closing off the low-severity aggregate-inference channel described above before T-18-3 writes the job. Filed as S-34 in `security/v1-review.md`, owner backend-engineer (T-18-3), severity Low (aggregate/no-PII, not cross-tenant data access), due within this wave since it's a one-line spec-conformance check, not a 30-day clock item.
- `invai-contracts/README.md`'s namespace table (flagged by the author as a gap outside owned paths) should get its `market` row and `market.niches.manage` before the wave closes, for the same reason any permission list should stay accurate — not a security finding, just seconding the author's own note to the tech lead.

## ADR status
The ADR already carries `Status: accepted (2026-09-27; security-reviewer co-review on T-18-1 confirms)`. My review confirms it: the table shape, RLS, writer discipline, validation, retention and mock rule are all sound and match the proven `trademark_marks` precedent, and the one gap I found (S-34) is a documentation/implementation-time tightening for T-18-3, not a reason to change the ADR's decision or reopen it.
