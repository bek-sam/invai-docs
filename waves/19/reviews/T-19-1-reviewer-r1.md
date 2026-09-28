# Review of T-19-1 (round 1)

- Reviewer: reviewer on opus
- Author: architect on fable
- Verdict: approve

Scope reviewed: `invai-contracts` `e99ac21` (0.7.0, on top of `378d6ae` 0.6.1), ADR 0016 + index row and the report (`invai-docs` `a8110cb`). Inputs: card, wave.md "Agreed interfaces", "Binding plan-review changes" A1–A5, A9, A12, "Contract landed", `reviews/plan-architect.md`.

## Evidence I re-ran
| Command | Result |
|---|---|
| `node --version` (pnpm PATH) | v24.21.0 |
| `git -C invai-contracts status --short` | clean; HEAD `e99ac21` |
| `invai-contracts`: `pnpm typecheck && pnpm lint && pnpm test` | tsc clean; biome "Checked 55 files … No fixes applied"; `Test Files 7 passed (7)`, `Tests 68 passed (68)` |
| `invai-floor`: `pnpm typecheck` | clean (links `@invai/contracts` -> `../../../invai-contracts`) |
| `invai-web`: `pnpm typecheck` | exactly 1 error: `src/routes/_app/index.tsx(357,61): TS2366` (`alertKindLabel` exhaustive switch, `ai_summary_breaker`). Granted to T-19-5 in wave.md "Contract landed" |
| `invai-backend`: `pnpm typecheck` | 1 error: `src/modules/tenancy/router.ts(11,42) TS2741 'notifications' missing` (the T-19-4 day-1 stub, A6). The `router.ts` `digest` error is gone, so T-19-3's stub has landed |
| backend `node --import tsx -e` walking `listProcedures(contract)` | 236 procedures (the README count is right); `digest.list GET /digest/ finance.read`, `digest.get GET /digest/week finance.read`, `digest.latest GET /digest/latest finance.read`, `digest.feedback POST /digest/{digestId}/feedback finance.read`, `digest.recordClick POST /digest/{digestId}/clicks finance.read`, `digest.settings.get GET /digest/settings/ org.manage`, `.set PATCH org.manage`, `.setRecipientEmail POST /digest/settings/recipients/{userId}/email org.manage`, `digest.sendPreview POST /digest/preview org.manage`, `me.notifications.get GET /me/notifications/ org.read`, `.set PUT org.read` |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-contracts 378d6ae` | no deleted tests, skips, mocks, snapshots, config or test-only branches; 1 assertion removed (`market.test.ts` `toBe("0.6.1")`), see Checks |
| Fail-without-change: base `378d6ae` archived to scratchpad + new `src/digest.test.ts` copied, `vitest run` | `Test Files 1 failed` (the new schemas don't exist on base), so the test fails without the change. Scratch dir removed |
| `sed -n 40,84p src/contract.test.ts` | the pagination rule covers `.list$` with no exemption for `digest.list`. The GET path-param allowlist explains why the week key is a query param |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 Procedures, additive, consumers, floor baseline | yes (web exception granted) | All 11 procedures appear in the listProcedures walk. `digest.list` is `Page` -> `paginated(DigestSummary)` and passes `contract.test.ts` "list endpoints use cursor pagination". Only additions in the diff: new namespace, new `me.notifications` sub-router, enum values at the end, new event keys. Floor typechecks clean. `FLOOR_COMPAT_BASELINE` is still `0.3.0`, asserted in both `digest.test.ts` and `market.test.ts`. The web break comes from the granted `ai_summary_breaker` value only, and wave.md grants the fix to T-19-5 |
| 2 Permissions + matrix test | yes | Read procedures are `finance.read`; `settings.*` and `sendPreview` are `org.manage`; `me.notifications.*` is `org.read` (A1, A2). `digest.test.ts` "the matrix from roles.ts is exactly the agreed one": owner and admin get all 11; office gets read + notify (no settings/preview, spec AC27); designer, presser, packer, receiver and vendor get notify only. It also asserts admin has `billing.read` and office does not. `planUsage` is documented as `billing.read`-only in the schema doc, the contract doc and the README |
| 3 Schemas | yes | `WeekKey` regex W01..W53 is tested for good and bad keys. Money: `impactCents: Cents` (a fraction is rejected). Percents: `changePct`. `DigestFact {id, unit, value, formatted:{en,es}}`; a fact missing `formatted` is rejected. `DigestInsight` has `id, detector (D1..D8, market), rank, score, confidence (Ratio), action {kind, params, href}, facts[]`. `DIGEST_STATUSES = ["ready","skipped_quiet"]`; `building`/`failed` are rejected by `DigestSummary` (A4). `NARRATIVE_STATUSES` are the six values. `Digest.shape` has no `summary`/`narrative` key (A5). `recommendation: MarketRecommendation.nullable()` reuses the 0.6.x schema. Feedback reasons are the three; `reason` only goes with `down`. Settings: `day` mon..sun, `hour` int 6..10 (5, 11 and 7.5 rejected), `aiSummary`, plus read-only `aiSummaryMode`. Recipients `{userId, name, emailOn, deliverable}`; `setRecipientEmail` has `on: z.literal(false)` (A3). `DigestLatest {digest, paused}` (A4). `digest_narrative` is at the end of `CREDIT_KINDS` (A5) |
| 4 feedback/recordClick idempotent, documented | yes | Doc comments in `src/contract/digest.ts`: feedback is idempotent on (digest, insight, caller), latest wins; recordClick: first click wins, same `clickedAt` on repeat. Both are also in the CHANGELOG. `setRecipientEmail` and `me.notifications.set` are also documented idempotent |
| 5 `digest.ready` event | yes, as `{digestId, weekKey}` | `events.ts` and `realtime.ts` both carry `{digestId: Id, weekKey: WeekKey}`, tested through `Events[...].parse` and `parseRealtimeEvent`; a bad week key parses to null. The card's `companyId` is dropped per wave.md "Agreed interfaces" and "Contract landed" (the envelope carries the org, as for every other event); the binding changes override the card line |
| 6 Public link route shape in README (A9) | yes | README "Public link routes (not oRPC)" pins `${BETTER_AUTH_URL}/l/:token`; the purpose-bound key `hmacHex(BETTER_AUTH_SECRET,"links:v1")`; payload `{v,k,c,u,r<=128,exp}` with 400 d / 30 d lifetimes; POST unsubscribe-only (click -> 405), 200 on repeat, Undo `{undo:true}` within 24 h, else 409; GET unsubscribe -> 302 `${WEB_ORIGIN}/unsubscribe?token=`; click -> same-origin path; invalid -> `?error=invalid` / 400; no token in logs; `links` bucket 60/min; no `PUBLIC_WEB_URL`. ADR 0016 records it, and its index row is present |
| A12 wave row sync | yes | The wave.md T-19-1 row lists `contract/tenancy.ts` + `schemas/tenancy.ts` and `schemas/ai.ts` |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`git diff --stat`). 16 files, all in `invai-contracts`. Card/wave paths: `contract/digest.ts`, `schemas/digest.ts`, `contract.ts`, `index.ts`, `events.ts`, `realtime.ts`, `contract/tenancy.ts`, `schemas/tenancy.ts`, `schemas/ai.ts`, `package.json`, `CHANGELOG.md`, `README.md`, `digest.test.ts` (tests for new schemas). Outside the literal card list, but justified: `schemas/alerts.ts` (wave.md grant 2026-09-27); `compat.ts` (`CONTRACT_VERSION` must equal `package.json`, held by a test, so a forced part of the 0.7.0 bump); `market.test.ts` (version assertion). All three sit inside the architect's `invai-contracts/**`. Nothing in backend, web or floor was edited.
- [x] Nothing outside scope. Contract, docs and ADR only; no implementation.
- [x] Tests exercise the behavior, and none were weakened. The one removed assertion (`market.test.ts` `CONTRACT_VERSION === "0.6.1"`) became `isContractVersionAtLeast(…, "0.6.1")`. The exact version is still pinned in `digest.test.ts` (`toBe("0.7.0")`), and `compat.test.ts` still ties it to `package.json`, so no check was lost. The new test fails on the base code.
- [x] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text. No tables or request code (contract only). Idempotency is documented per procedure. Money is `Cents`/`impactCents`; formatted facts carry en and es. No PII beyond member names in the admin-only recipients list. Zod is on every input (`Page`, `WeekKey`, `Id`, enums, `z.literal(false)`, hour bounds, href regex).
- [x] Decisions recorded where needed: ADR 0016 (accepted, architecture, indexed). The report lists the local choices (week key as a query param, full `MarketRecommendation` instead of `RecommendationRef`, `EMAIL_SKIP_REASONS` in the contract).
- [x] InvAI invariants: floor untouched (baseline 0.3.0, no floor-facing shape changed); contract additive; opt-in enforced by type (an admin can only turn email off); no narrative text reaches clients (shadow fence); plan usage is `billing.read`-gated (fence); `DigestAction.href` accepts only in-app paths (`//`, schemes and `\` are rejected, tested).

## Optional notes (not blocking)
1. `invai-contracts/src/schemas/digest.ts:474-479` — `DigestFact.value` with `unit: "cents"` accepts non-integers (`z.number()`). `impactCents` is guarded, but a fact is not. A `.superRefine` (unit `cents` -> integer) would move the cents rule into the contract. For now it is the T-19-3 producer's duty; the digest reviewer should check it.
2. ADR 0016 Decision 3 says "`GET /l/:token` never mutates", but the README (and A9) have the click GET call the registered handler, which records the click. The intent is clear (GET never *unsubscribes*), but a link scanner following a click GET will inflate `digest_action_click_rate`. The T-19-4 and T-19-3 reviewers (and security-reviewer) should confirm the click write is harmless and idempotent (first click wins), and consider tightening the ADR wording in a later edit.
3. Card AC5's `companyId` in the payload and the card's owned-path list differ from what landed. wave.md governs, and the report says so. The tech lead may want to amend the card text so QA's acceptance tests don't assert `companyId`.
4. `market.test.ts` loosening the version check is fine with the new pinning scheme. A one-line note in the README "How to add a procedure" ("only the newest wave's test pins `CONTRACT_VERSION`") would keep the pattern stable.
