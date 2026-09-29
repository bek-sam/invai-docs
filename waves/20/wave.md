# Wave 20: digest and market copy that is right on today's date, plus evidence (wave 14, part 1)

- Dates: 2026-09-28 →
- Goal (user outcome): on any real calendar date, in English or Spanish, the digest, the assistant's market answers and Today never tell a shop to prepare for a peak that has passed, never show an English date in Spanish, never show a raw timestamp or raw permission error, and show percent-point changes as points. Every money or outside side effect has a test that proves "one effect, even on retry". Agents can't write outside their role's paths (tech lead and reviewer first). The demo seed runs safely next to a running worker.
- Sources: wave 19 gate issues 1–5 (`waves/19/reviews/gate.md`), backlog B-136, B-137, B-140, B-141 (always in scope: bugs in shipped features), B-71, B-106 (seed part), B-47 + B-116 (roadmap wave 14; process/security).
- Rules: `team/agent-brief.md`. **Every prompt says "Don't push; only the tech lead pushes after the gate."** Every grant is written below when given. Every prompt names the agent's absolute memory path `/Users/bekbolsun/invai/.claude/agent-memory/<role>/` and asks it to record every PID it starts in its report.
- Budget: at most 3 builder agents at once (a product-manager research agent runs in parallel this session).
- Plan reviewed by: product-manager (2026-09-28, approve with 2 changes; wording rule approved, specs updated), architect (2026-09-28, approve with changes A1–A4). All applied to the cards.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-20-1 Digest, market and Today copy on real dates (B-136, B-137, B-140, B-141 backend) | backend-engineer (market, digest, today) | opus | reviewer (sonnet) + product-manager (wording rule), integrations-engineer (mock `asOf` hunk), qa-engineer (Today is golden path) | data-integrity | waiting (QA acceptance) |
| T-20-2 Web digest copy, permission errors and number format (B-141 web, gate issue 5 web) | web-engineer | sonnet | reviewer (opus) + product-designer | ui | planned |
| T-20-3 Side-effect and live-adapter tests (B-71) | qa-engineer | fable | backend-engineer (shipping) as feature owner + reviewer (opus) | payments, marketplace-policy | building |
| T-20-4 Path guard for tech lead and reviewer, segment-aware push rule (B-47, B-116) | platform-sre | opus | reviewer (sonnet) + security-reviewer | auth (guard) | security r1 changes-required; round 2 |
| T-20-5 Seed safe next to a running worker; stale jobs after reset (B-106 seed part, gate issue 6) | backend-foundation | fable | reviewer (opus) + qa-engineer (seed feeds the golden path) | floor-correctness | building |
| QA acceptance tests for T-20-1 and T-20-2 (not a card; wave step 3) | qa-engineer | sonnet | feature owner (T-20-1, T-20-2) + reviewer | — | building |

## Order and ownership
1. Batch 1 (3 agents): QA acceptance tests for T-20-1/T-20-2, T-20-4, T-20-5.
2. Batch 2 as slots free: T-20-1 (after QA's acceptance commit), T-20-3; then T-20-2 after T-20-1's commit lands (architect A3).
3. No contract change in this wave. If T-20-1 or T-20-2 finds one is needed, stop and tell the tech lead (architect card).

| Card | Owns (exclusive) |
|---|---|
| T-20-1 | `invai-backend/src/modules/market/{rules,read,service,signals,compute}.ts` and their non-acceptance tests; `src/modules/digest/{market-watch,render,facts,detectors,build}.ts` and their non-acceptance tests; `src/modules/today/service.ts` (alert message only) + its test; grant below for the mock `asOf` |
| T-20-2 | `invai-web/src/components/digest/**`, `src/routes/_app/digests/**`, `src/routes/_app/settings/notifications.tsx`, `src/lib/errors.ts` or wherever `errorInfo()` lives (the `FORBIDDEN` case only), `src/i18n/en.ts` + `es.ts` (keys it adds, by hand) |
| T-20-3 | new `*.acceptance.test.ts` files under `invai-backend/src/modules/{shipping,inventory,ai,personalization,orders}/**` and `src/integrations/{carriers,channels,suppliers}/**` (A1); `invai-docs/build/qa-report.md` |
| T-20-4 | `invai-docs/team/hooks/**` (new `guard-paths.py`, `guard-bash.py` push segment, tests), `invai-docs/team/settings.json`; after review, the synced copies `.claude/hooks/**` and `.claude/settings.json` through `invai-docs/team/sync.sh` |
| T-20-5 | `invai-backend/src/db/seed/**`, `invai-backend/scripts/**` (a reset helper if needed), `invai-backend/package.json` (script lines only) |
| QA acceptance | `invai-backend/src/modules/{digest,market,today}/*.acceptance.test.ts` (new or extended), `invai-web/e2e/digest*.spec.ts` |

## Grants (written when given)
- 2026-09-28 T-20-2 (after the fact, accepted): the unit tests next to granted files, `src/lib/errors.test.ts` and `src/components/market/recommendation-copy.test.ts`.
- 2026-09-28 T-20-2 AC4 amended by the tech lead: es-US in Spanish for digest numbers (PM decision on T-20-1); billing page is B-184.
- 2026-09-28 T-20-2: `invai-web/src/components/market/recommendation-copy.ts` (R1 peak-under-way line), found by T-20-1.
- 2026-09-28 T-20-1: `invai-backend/src/integrations/market/mock*.ts`, only the `asOf` computation (end of the last complete week, never a future date). integrations-engineer co-reviews that hunk.

## Wording rule proposed for PM approval (T-20-1, T-20-2)
- **Past peak (act-by date before the digest week's end or today):** the item is not shown in Market watch and R1 doesn't emit it.
- **Peak under way (today is inside the peak month):** R1 text becomes "The {{niche}} season is on now. Make sure {{design}} is listed and in stock." / "La temporada de {{niche}} ya empezó. Asegúrate de que {{design}} esté publicado y con inventario." No act-by date is shown.
- **Percent metrics (margin %, on-time %):** change in points, one decimal: "+6.9 pts" / "+6,9 pts". Zero change on any metric: "unchanged" / "sin cambio", with no arrow.
- **Mock outside source date:** the end of the last complete ISO week, shown as "week ending Sep 27" / "semana al 27 sep".

## Ports, test DBs, Redis DBs
| Who | API port | Test DB | Redis DB |
|---|---|---|---|
| T-20-1 | 3111 | `invai_t20_1` | 11 |
| T-20-2 | 3112 | (dev copy `invai_t20_2`) | 12 |
| T-20-3 | 3113 | `invai_t20_3` | 13 |
| T-20-5 | 3115 | `invai_t20_5` (+ a seed copy) | 14 |
| QA acceptance | 3116 | `invai_t20_qa` | 15 |
| Reviewers | 3171–3179 | `invai_t20_rev_<card>` | 10 |

## Build log
- 2026-09-28 T-20-4 built (invai-docs `9a1a445`): 57 tests, 302 subtests. Tech lead answers to its open questions: logging writes with no agent type to `team/state/guard-paths.log` is fine (no content logged); the stricter push denials (`--prune`, abbreviated long flags, `$`-substituted arguments) are accepted. Sync to `.claude/` only after reviewer and security approve, by platform-sre, diffing live `.claude/settings.json` first.
- 2026-09-28 T-20-4: reviewer r1 approve; security r1 **changes-required** (finding 1, Medium: `guard-bash.py:487-502` `kill_by_pattern` lets a process lister feed a kill through a temp file or a `cat` substitution, which the old guard denied). Round 2 to platform-sre with the security-reviewer's proposed fix and its 6 deny cases (X12–X17).
- 2026-09-28 **Usage-limit stop (429 session limit).** Every running agent stopped. State on disk at resume:
  - QA acceptance: uncommitted `invai-backend/src/modules/digest/date-copy.acceptance.test.ts`, `invai-web/e2e/digest-dates.spec.ts` (typecheck clean, spec not yet run). Its API on 3116 (pid 73809 + tsx parent 73793, DB `invai_t20_qa_dev`) stopped by the tech lead. DBs `invai_t20_qa`, `invai_t20_qa_dev` still exist.
  - T-20-5: uncommitted `invai-backend/src/db/reset.ts`, `src/db/reset.test.ts` (new), `src/db/seed/{builder,index}.ts`, `src/db/seed/outbox-hold.ts` + test (new), `invai-backend/README.md`, `src/modules/README.md` (both READMEs are backend-foundation's; accepted). Next step was: worker on Redis DB 14 against the fresh copy, seed with it running (run A), then with it stopped (run B), compare counts. DBs `invai_t20_5`, `invai_t20_5_seed` exist.
  - T-20-3: uncommitted new files `src/integrations/{carriers/easypost-live,channels/shopify-live,suppliers/ss-live}.acceptance.test.ts`, `src/modules/{ai/publish,inventory/side-effects,personalization/render,shipping/side-effects}.acceptance.test.ts`; not yet run. DB `invai_t20_3` exists; no worktree left.
  - T-20-1, T-20-2: not started. T-20-4 security r1 was written before the stop.
  - Port 3142 (pid 68589) is the pre-wave-19 orphan, not wave 20's; left alone. Port 3000 (pid 68649) is the shared dev API.
  - invai-docs has 3 unpushed docs-only commits (`539ea0c` PM research 16, `9a1a445` T-20-4, `9df549f` analytics v2 spec); they go out with the wave 20 gate push.
- 2026-09-28 Resume: fresh agents for QA acceptance, T-20-5 and T-20-4 round 2 (3 builders), each told what is on disk; T-20-3 resumes when a slot frees, then T-20-1, then T-20-2.
- 2026-09-28 T-20-4: security r2 **approve** (f0d4b1e); reviewer r1 approve. **All required approvals in.** Synced to `.claude/` by platform-sre (diff limited to T-20-4's changes; settings.json parses).
- 2026-09-28 QA acceptance done: backend `b307de0` (7 tests, fail for the right reasons), web `f5af662` (`e2e/digest-dates.spec.ts`; added the missing T-20-2 AC2 check), report docs `339131f`. Env note for builders: dev copies from `createdb -T invai` lack `invai_app` grants; reapply `drizzle/0001_grants_extensions.sql` GRANTs.
- 2026-09-28 T-20-1 started (after QA's commit).
- 2026-09-28 T-20-3 built `44c76d9` (27 tests, 15 regression proofs; no product bug found), docs `eaf2975`. Reviewer r1 approve; feature owner (backend-engineer shipping) r1 approve. **All required approvals in.** Process note: the feature-owner reviewer briefly toggled a guard in `shipping/service.ts` in the shared tree and reverted it (verified byte-identical with `git diff`); lesson added.
- 2026-09-28 T-20-1 built `bfae180` (QA's 7 acceptance tests green). It changed the approved R1 rule's effect on wave 18's `market.acceptance.test.ts:627`; QA agreed and updated its own test in `8814acb`. QA co-review approve. Found a web gap: `components/market/recommendation-copy.ts` still says "before {{peak}}" for an under-way peak; granted to T-20-2 (AC5). Open for PM: Spanish decimal convention mix ("31.4%" next to "+3,3 pts").
- 2026-09-28 T-20-5 built `8fdc733` (root cause: `sheet.built` → `billing.recordSheetBuilt` upserts `usage` mid-seed; the seed now holds the outbox per phase; reset obliterates the 5 app queues only). Reviewer r1 **changes-required**: a running worker's 5-min alert sweep collides with the seed's plain `alerts` inserts (`builder.ts:1521`, `~1609`). Round 2 started.
- 2026-09-28 T-20-1: integrations r1 approve (mock `asOf` hunk), QA r1 approve, PM r1 **changes-required**: Spanish digest numbers use es-US everywhere, points included ("+6.9 pts" in Spanish too); drop `PTS_LOCALE` in `facts.ts`. QA must update `date-copy.acceptance.test.ts:290-293` to the same form. Reviewer r1 pending.
- 2026-09-28 T-20-2 built `f59438f` (local `GlanceTile` because `@invai/ui` `StatCard` has no neutral state; `settings/billing.tsx` Spanish numbers still "10,000", outside the grant). In review (reviewer, product-designer).
- 2026-09-28 **Disk incident:** the data volume hit 100%; Docker stopped mid-run and was restarted (`docker compose up -d`, volumes intact). 3.8 GB free after; stale test DBs dropped. OI-20 asks the owner about clearing Docker's build cache / other projects' images.
- 2026-09-28 Round 2s: T-20-1 `076dd69` (es-US points) + QA `d6a19f1`; PM r2 **approve**. T-20-2 `d092a4b` (R1 no-niche fallback to the peak month; es-US digest numbers) + QA `6e7db2f` (AC4 re-pointed to the digest page); designer r1 approve.
- 2026-09-28 **Second usage-limit stop.** Lost mid-task: reviewer r2 for T-20-1 and T-20-2 (no file written), T-20-5 round 2 (uncommitted WIP in `src/db/reset.ts`, `reset.test.ts`, `src/db/seed/builder.ts`, `src/modules/README.md`, new `src/db/seed/sweep-race.test.ts`; it was proving queue scoping with a decoy prefix). The earlier `facts.ts`/`pure.test.ts` WIP seen by QA was T-20-1 r2, since committed in `076dd69`. No wave 20 listener left (3142 is the old orphan). Disk now 14 GB free.
- 2026-09-28 Resume: T-20-5 r2 (fresh agent told the WIP), reviewer r2 for T-20-1/T-20-2.
- 2026-09-28 Reviewer r2 **approve** on T-20-1 (`076dd69`) and T-20-2 (`d092a4b`). **T-20-1, T-20-2, T-20-3, T-20-4 have every required approval.** T-20-5 round 2 in progress.
- 2026-09-29 Push coupling: wave 22's T-22-1 landed backend day-1 stubs `2cda6e2` (needs contracts 0.8.0) between wave 20's commits. Since `main` can't be pushed around a middle commit, T-22-1 (contracts 0.8.0 + stubs) is reviewed before the wave 20 gate and goes out in the same push; the gate runs on HEAD with it.
- 2026-09-29 T-20-5 round 2 `8ffff2b` (seed upserts alerts/inventory_settings/usage; sweep-race test; reset test on its own BullMQ prefix). Reviewer r2 and the T-22-1 reviewer stopped twice (usage limit, stream stall) without writing a verdict. Tech lead cleanup: stopped the r2 reviewer's orphan worker (pid 23804/23795, DB `invai_t20_rev5b_seed`, Redis 12), dropped stale DBs `invai_t20_rev5b*`, `invai_t20_5r2`, `invai_t22_2_dev`, flushed Redis 12, removed worktree `invai-backend-t20-5`. T-22-2 stalled before any edit; restart after wave 20's gate.
- Wave 21: T-21-1 `3cffec0` (legal drafts, OI-19 counsel question), T-21-2 `b2d3565`/`fa7e6cd` (IR plan, access control), T-21-3 `ed0ef87` (security docs; S-15/S-28/S-31 marked fixed; 4 DPP items without backlog ids) built; reviews next.
- 2026-09-28 Watch at the gate: the full backend run under load showed `market/service.test.ts` beforeAll timing out at 120 s (the suite took 746 s with several agents' suites running). Re-run alone at the gate before calling it a bug.

## Integration gate (2026-09-29, `reviews/gate.md`, qa-engineer)
- [x] Fresh reset, migrate, seed **with two workers running** (T-20-5 proven)
- [x] Repo checks green in contracts, backend, web, floor (backend `outbox-hold.test.ts` flaky under load, green alone: issue 4)
- [x] API golden path 13/13, floor 3/3, full browser run 35/35 in one go (digest-dates 7, digest 8, golden path 13, market 5, screens smoke 2), no 429s
- [x] Digest on today's real date: no past act-by item, Spanish heading in Spanish, points "+2.8 pts", "sin cambio", readable Today alert, translated no-access page
- [x] Key screens looked at by the tech lead (gate-shots 01 digest es 390, 05 notifications refused es 390): correct; noted "~704,47 US$" chip (issue 3) and a "Reintentar" button on a no-access page (cosmetic, B-190)
- [x] Pushed to `main` 2026-09-29: invai-contracts `78d2469` (0.8.0 incl. T-22-1, approved), invai-backend `8ffff2b` (wave 20 + T-22-1 stubs), invai-web `d092a4b` (T-21-5 `ae906ad` held for its own review), invai-docs (this commit chain)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
| Primary reviewer r1: 3 of 5 (T-20-3, T-20-4 approve; T-20-1, T-20-2, T-20-5 changes-required). All required reviewers r1: 1 of 5 (T-20-3). Every card approved by round 2 | not planted (OI-15 open) | 0 from approved cards so far; gate found 1 High deploy-readiness issue (CSP blocks browser uploads to S3 in production, pre-existing) and 2 Medium (market mock sources after a worker-seeded reset; assistant still prints "Act by <past date>") | 0 | about 24 h wall clock including three usage-limit stops, two stream stalls and a disk-full Docker stop | builders about 190k–320k per card; reviews 100k–220k |

## Retro
- **What worked:** acceptance tests first caught a real kit bug (StatCard had no neutral state) and a missing AC; co-reviews caught cross-repo drift twice (Spanish decimal convention; empty niche slot on the web while the email fell back to the month). Security caught a real regression in the guard (a lister relaying PIDs through a file). T-20-5's reviewer reproduced a seed/worker race the author missed.
- **What slipped:** the card's own copy example ("+6,9 pts") contradicted the older digest rule (es-US), costing a round on two cards; three usage-limit stops and two stalls meant fresh agents had to resume from disk several times; the disk filled once and stopped Docker; an agent edited invai-web while the gate's browser run used the shared dev server.
- **Lessons added:** reviewers reproduce regression proofs only in a worktree; dev DB copies need GRANTs. Proposed: any copy example in a card is checked against the spec's existing locale rules before the card is issued (tech lead practice); no builder edits a repo whose dev server the gate is using (gate slot covers web/floor too).
