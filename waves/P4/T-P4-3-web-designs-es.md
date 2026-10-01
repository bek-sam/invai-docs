# T-P4-3: Web in Spanish: /catalog/designs checked and fixed; billing numbers confirmed (B-184)

| Field | Value |
|---|---|
| Wave | P4 |
| Scope ref | `always-in-scope: bug` (English leaks or wrong number formats under Spanish UI, `product/scope.md` en/es) |
| Spec | P3 hand-off ("Spanish screens not yet checked"); backlog B-184 |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (sonnet) |
| Risk flags | ui |
| Model | sonnet |
| Depends on | the P3 close-out push (invai-ui es money grouping) |

## Owned paths (edit)
- `invai-web/src/routes/_app/catalog/designs.index.tsx`, `invai-web/src/routes/_app/catalog/designs.$designId.tsx`, components used only by those two routes, `invai-web/src/routes/_app/settings/billing.tsx` (only if B-184 isn't fully fixed), `invai-web/src/i18n/en.ts`, `invai-web/src/i18n/es.ts`, `invai-web/scripts/i18n-es.json`, `invai-web/scripts/i18n-extra-en.json` (template-literal keys), unit tests next to them

## Read-only paths
- `invai-web/e2e/**` (QA), `invai-web/vite.config.ts`, `invai-ui/**` (product-designer), `invai-backend/**`, `invai-contracts/**`, `invai-floor/**`

## Acceptance criteria
1. /catalog/designs (list) and one design's detail page in Spanish at 1440 px and 390 px: no English text from our code (headings, buttons, empty states, badges, toasts, table headers), no raw keys, dates and numbers through the active locale (`dateLocale()`, the shared money formatter), nothing clipped. Each finding is fixed and listed with before/after screenshots. Backend-sent English (if any) is listed under "Blocked by other owners", not patched in the web.
2. B-184: `settings/billing.tsx` in Spanish shows usage numbers and money in the Spanish format (no bare `toLocaleString()`); if already right, screenshot proves it and no change.
3. English screens unchanged in meaning; `pnpm i18n` is NOT run (hand-edit the three catalog files in sync, `write-plain-language-copy`).

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 40` in `invai-web`.
- Exercised: own API `PORT=3142`, `REDIS_URL=redis://localhost:6379/12` in `invai-backend` (allow your preview origin in the API's web-origin env for this process only); web `VITE_API_URL=http://localhost:3142 pnpm build && pnpm preview --port 5186` (the dev server's CSP is fixed to :3000, B-212). Sign in as `owner@desertbloom.test` / `demo1234!`, switch to Español, screenshot the list, a detail page and billing at 1440 and 390 in `/tmp/p4-web/`; look at each.

## Rules
- Role file `.claude/agents/web-engineer.md`; `team/agent-brief.md`. Memory: `/Users/bekbolsun/invai/.claude/agent-memory/web-engineer/`.
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Record every PID you start and stop exactly those (by port); flush Valkey DB 12. Never reset the dev DB. Don't end your turn with a process still running.
- Report (≤ 60 lines) to `invai-docs/waves/P4/reports/T-P4-3.md`, one progress line per milestone.
