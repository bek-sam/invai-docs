# T-P4-2: Floor in Spanish: the header pill fits (B-241); QC result and busy panel checked

| Field | Value |
|---|---|
| Wave | P4 |
| Scope ref | `always-in-scope: bug` (floor copy wraps; Spanish-first pressers, `product/scope.md` en/es) |
| Spec | backlog B-241; B-222 (done in T-P1-5, recheck); T-P3-2 r2 busy copy |
| Owner | floor-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (sonnet) |
| Risk flags | ui |
| Model | sonnet |
| Depends on | the P3 close-out push (invai-ui money grouping lands first) |

## Owned paths (edit)
- `invai-floor/src/components/SyncStatus.tsx`, the header component that hosts it, `invai-floor/src/stations/QcStation.tsx`, `invai-floor/src/stations/PressStation.tsx` (busy panel layout only), `invai-floor/src/i18n/en.ts`, `invai-floor/src/i18n/es.ts`, and unit tests next to them

## Read-only paths
- `invai-floor/e2e/**` (QA; if a spec's text must change, say so in the report), `invai-floor/src/outbox/**`, `invai-floor/src/sync*` (scan logic: no behavior change on this card), `invai-backend/**`, `invai-ui/**`, `invai-web/**`

## Acceptance criteria
1. B-241: at 1280×800 in Spanish, the header sync pill stays on one line for "1 escaneo por sincronizar", "12 escaneos por sincronizar" and "2 necesitan revisión" (shorter copy or a pill that sizes; use `write-plain-language-copy`, tú form, glossary words). English unchanged in meaning.
2. QC result in Spanish: after a pass and after a fail, the result banner uses the past-tense result text (not the button's "APROBAR"), the order number shows, and nothing wraps or clips. If it is already right (T-P1-5), no change; screenshots prove it.
3. Busy panel in Spanish (T-P3-2 r2 copy, "se reintenta solo"): the amber OCUPADO panel at 1280×800 shows no clipped or wrapped button text and no raw key; the wrong-blank BLOCKED panel stays red while busy. Fix layout or copy only if broken.
4. No scan behavior changes: the floor unit tests pass unmodified apart from copy assertions you changed on purpose (list them).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40` in `invai-floor`.
- Exercised: own API `PORT=3141`, `REDIS_URL=redis://localhost:6379/14` in `invai-backend`; floor dev on `:5185` pointed at it; pair with the station token from `invai-backend/seed-output.json`, PIN 1111–1188. Screenshots at 1280×800 in en and es of: header with 1 and 12 pending, header with "needs review", QC pass result, QC fail result, busy panel (simulate the 429 as T-P3-2 did), saved under `/tmp/p4-floor/`. Look at each one and list them in the report.

## Rules
- Role file `.claude/agents/floor-engineer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/floor-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Record every PID you start and stop exactly those (identify by port with `lsof -iTCP:<port>`, never by command line); flush Valkey DB 14. Never reset the dev DB. Don't end your turn with a test or dev process still running.
- Report (≤ 60 lines) to `invai-docs/waves/P4/reports/T-P4-2.md`, one progress line per milestone.
