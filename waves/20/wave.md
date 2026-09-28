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

## Integration gate
- [ ] Fresh reset, migrate, seed (with the worker running, to prove T-20-5)
- [ ] `run-golden-path` passes (API, browser, floor)
- [ ] Digest built on today's date: no past act-by item, Spanish heading in Spanish, points for margin, "unchanged" for flat metrics
- [ ] Key screens looked at by the tech lead
- [ ] Pushed to `main` (commits: …)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Retro
- What slipped:
- Lessons added:
