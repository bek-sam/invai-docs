# T-P5-1: Seed reprints are partial and about 3% of pressed items (B-243); seed previews go through the catalog path (B-233 seed part)

| Field | Value |
|---|---|
| Wave | P5 |
| Scope ref | `always-in-scope: bug` (demo data shapes the product's numbers: the seed's 57 reprints sit in 44 orders, each 100% reprinted, so Profit and the reprint report show only all-reprint orders) |
| Spec | backlog B-243, B-233 (seed part); decision 0020 (a reprint is the same item re-pressed: `isReprint` on that item, a `reprints` row, a second transfer); `waves/P3/reports/T-P3-4.md` |
| Owner | backend-foundation (seed) |
| Reviewer | reviewer (opus) |
| Co-reviewers | none |
| Risk flags | none (seed only; no schema, no product code) |
| Model | sonnet |
| Depends on | nothing (T-P4-1's model is pushed) |

## Owned paths (edit)
- `invai-backend/src/db/seed/**`

## Read-only paths
- everything else, including `src/modules/**` (T-P5-2 owns `modules/catalog/**`), `src/db/schema/**`, `src/test/**`, every other repo

## Acceptance criteria
1. On a fresh seed, reprinted items are 2–4% of pressed items (pressed = items that reached `pressed` or later, including history), and at least 70% of orders containing a reprint also contain at least one item that was not reprinted. Today: 57 items in 44 orders, 0% partial.
2. Every seeded reprint follows decision 0020: the same `order_items` row with `isReprint = true`, a `reprints` row, and a second transfer cost on that item's sheet path; no sibling revenue-0 rows. The existing AC-Seed1 spread stays (at least 3 reasons, 2 stations, 2 vendors, and `reprint_cost` "vendor (via gang sheet)" with more than one value).
3. Golden-path inputs do not move: the counts the E2E suites read (open orders by state, the golden-path seed orders, Today tiles at seed time, users, PINs, station token) are the same before and after. Prove it with one SQL count script run on a seed from `origin/main` and on yours (paste both outputs, ≤ 20 lines each).
4. Profit sanity on your seed after recompute: count of orders with a reprint that lose money, and orders with $0 revenue among reprint orders (expect 0). Paste the numbers.
5. B-233 seed part: the seed creates design previews through the same code the app uses (`renderDesignPreviews` in `modules/catalog/service.ts`, called read-only) instead of calling `imaging.preview` directly, keeping today's behavior when imaging is unreachable (seed still finishes). If that is impossible without changing catalog code, don't change catalog: leave the direct call, and write the exact reason in your report (the tech lead closes that part).
6. The seed stays deterministic (same counts on two runs) and its run time does not grow by more than 10%.

## Verification
- Scratch DB only: `invai_p5_seed`, imaging on :8031, `REDIS_URL` pinned to Valkey DB 13 **before** any `db:reset` (B-219 wipes queues in whatever Redis it sees). Never reset the shared `invai` DB. Drop `invai_p5_seed` at the end.
- `pnpm typecheck && pnpm lint 2>&1 | tail -n 20` and `pnpm vitest run src/db/seed --reporter=dot 2>&1 | tail -n 20` in `invai-backend`. The gate runs the full suite and E2E.
- The SQL from AC1, AC3, AC4 with outputs in the report.

## Out of scope
- Any change outside `src/db/seed/**`; B-130 (longer history), B-198 (Amazon shipping), B-204 (bins). New schema.

## Rules
- Role file `.claude/agents/backend-foundation.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/backend-foundation/`.
- Other agents at the same time: architect (invai-contracts), backend-engineer on T-P5-2 (`modules/catalog/**`, `modules/orders/mapping.ts`). Don't touch their files.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; don't end your turn with a run or a process going. Record every PID you start and list it (stopped) in the report.
- Trim output (`2>&1 | tail -n 40`). Report (≤ 60 lines) to `invai-docs/waves/P5/reports/T-P5-1.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
