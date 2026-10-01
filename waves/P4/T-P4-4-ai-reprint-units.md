# T-P4-4: Assistant and analyst answers count reprinted units as sales (B-242, AI half)

| Field | Value |
|---|---|
| Wave | P4 |
| Scope ref | `always-in-scope: bug` (assistant profit answers leave out reprinted units; same cause as B-242) |
| Spec | backlog B-242; `decisions/0020-is-reprint-means-re-pressed.md`; `reviews/plan-architect.md` ruling 6 |
| Owner | ai-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (no prompt or model change; query filter only) |
| Risk flags | money (numbers in answers) |
| Model | sonnet |
| Depends on | the P3 close-out push; no dependency on T-P4-1 |

## Owned paths (edit)
- `invai-backend/src/modules/ai/analyst-queries.ts` (`:385`), `invai-backend/src/modules/ai/assistant-tools.ts` (`:601`), and their tests

## Read-only paths
- every other module (T-P4-1 owns finance, orders, analytics, market), prompts and model config, `src/db/**`, `src/test/**`, `invai-contracts/**`

## Acceptance criteria
1. The two queries no longer filter `eq(profitLines.isReprint, false)`: a reprinted, non-cancelled unit counts as a sale (decision 0020); refunded and cancelled handling stays as it is.
2. A test with a fixture shop: an order with 2 units, one reprinted, gives 2 units and both units' revenue in each tool's answer data. It fails on the base commit.
3. No prompt, model, effort or credit change; mock provider still used.

## Verification
- While building: only the two test files (foreground). Once at the end: `pnpm typecheck && pnpm lint 2>&1 | tail -n 10` and the `src/modules/ai` tests; the gate runs the full suite. Don't run the full suite while the gate or T-P4-1's full run is going (max 2 heavy runs).

## Rules
- Role file `.claude/agents/ai-engineer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/ai-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Start no API unless needed; record and stop any PID. Run tests in the foreground.
- Report (≤ 40 lines) to `invai-docs/waves/P4/reports/T-P4-4.md`.
