# T-P5-5: Web shows Today alert lines and timeline reasons from codes, in English and Spanish (B-224, B-238)

| Field | Value |
|---|---|
| Wave | P5 |
| Scope ref | `always-in-scope: bug` (Spanish leak on Today and the order drawer timeline; en/es is MVP item 5) |
| Spec | backlog B-224, B-238; the contract from T-P5-3 and its rulings in `reviews/plan-architect.md` |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (sonnet): ui |
| Risk flags | ui |
| Model | sonnet |
| Depends on | T-P5-3 committed (build against the contract); the live check needs T-P5-4 committed |

## Owned paths (edit)
- `invai-web/src/routes/_app/index.tsx` (alert detail), `invai-web/src/features/orders/**` (timeline reason), their tests
- `invai-web/src/i18n/en.ts`, `src/i18n/es.ts`, `scripts/i18n-es.json`, `scripts/i18n-extra-en.json` (template-literal keys)

## Read-only paths
- `invai-contracts/**`, `invai-backend/**`, `invai-ui/**`, every other web file

## Acceptance criteria
1. Today: when an alert has `params`, the detail line is built from `kind` + params with `t()`, in English and Spanish (order number, ship-by date formatted with `Intl` in the active locale, hours with plural forms). Without params (old rows, worker/AI alerts), today's behavior stays (English detail in en, title only in es).
2. Order timeline: when an entry has `reasonCode`, the reason shows translated (with `reasonParams`, for example the sheet name, the reprint reason through the existing reprint-reason labels if there are any); without a code, today's `extractTimelineReason` fallback stays.
3. No raw key, no internal word, no English in es on these lines; Spanish fits at 390 px and 1440 px.
4. Unit tests for the alert line and the reason mapping (with and without codes); `scripts/i18n-es-missing.json` absent or without your keys.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 20` in invai-web.
- Exercise for real (after T-P5-4 commits): API `PORT=3152` (Valkey DB 11) from invai-backend, web `pnpm build && pnpm preview --port 5190` with `VITE_API_URL=http://localhost:3152`. As `office@desertbloom.test`, screenshots of Today alerts and one order drawer timeline (reprint or sheet step) in en and es at 1440 and 390, into `/tmp/p5-web/`. Look at them; list the file names in the report.

## Out of scope
- Backend and contract, the 8 older es drifts (B-247), other screens.

## Rules
- Role file `.claude/agents/web-engineer.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/web-engineer/`.
- Never run `pnpm i18n`; hand-edit the three catalog files (write-plain-language-copy).
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Foreground test runs only; record every PID you start and list it (stopped) in the report.
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P5/reports/T-P5-5.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
