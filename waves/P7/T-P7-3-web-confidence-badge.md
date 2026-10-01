# T-P7-3: Market screens use the kit badge; local copy removed (B-134, web half); assistant spend-cap message translated (B-262)

| Field | Value |
|---|---|
| Wave | P7 |
| Scope ref | `scope.md#market-signals` (B-134); `always-in-scope: bug` (B-262: an English-only server message shown to Spanish users) |
| Spec | backlog B-134; T-P7-2 card (props) |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | product-designer (sonnet) |
| Risk flags | ui |
| Model | sonnet |
| Depends on | T-P7-2 committed in `invai-ui` (`ConfidenceBadge` exported) |

## Owned paths (edit)
- `invai-web/src/components/market/recommendation-card.tsx`, `invai-web/src/components/market/confidence-badge.tsx` (delete), any other `invai-web/src/**` file that renders a confidence band (grep `band` / `confidence` first; list them in the report), `invai-web/src/i18n/en.ts`, `invai-web/src/i18n/es.ts`, `invai-web/scripts/i18n-es.json`, `invai-web/scripts/i18n-extra-en.json` (only if a `market.band.*` key goes away or stays template-built), `invai-web/src/routes/_app/assistant.tsx` (B-262 only: the stream `error` event branch, line ~140)

## Read-only paths
- `invai-ui/**` (T-P7-2), `invai-web/e2e/**` (qa-engineer, T-P7-1), every other repo.

## Acceptance criteria
1. The market recommendation card shows the kit `ConfidenceBadge` for each band; the local component file is gone and nothing imports it.
2. On screen nothing changes for the user: same text in English and Spanish (pass the web's translated `market.band.*` text as `label`, or drop the keys if the kit text is identical; say which), same colors and icons.
3. `pnpm typecheck && pnpm lint && pnpm test && pnpm build` pass in `invai-web`; `recommendation-copy.test.ts` still passes unchanged.
4. Screenshots of the market screen with all three bands visible if the seed has them (otherwise the ones it has), en and es at 1440 and 390 px, looked at; no raw keys, no truncation.

5. **B-262.** When the assistant stream sends `{type:"error", code:"spend_cap"}` (`invai-backend/src/modules/ai/service.ts:1320`), the chat shows a translated message (en and es, plain language: what happened and what to do, e.g. that the shop's AI limit for today is reached and to try again tomorrow or ask the owner), not the server's English text. Other codes keep today's behavior. A unit test covers the mapping (spend_cap → translated key; unknown code → the server message as today).

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint && pnpm test --reporter=dot 2>&1 | tail -n 20 && pnpm build 2>&1 | tail -n 10`.
- UI: `pnpm dev --port 5181` against the API on :3000 only if it is already up; never start or stop the gate slot. If :3000 is down, say so; the tech lead looks at the screen at the gate.

## Out of scope
- Any change in `invai-ui` (report gaps to the tech lead for T-P7-2 round 2), the digest, other market UI.

## Rules
- Role file `.claude/agents/web-engineer.md`. Strings: hand-edit `en.ts`, `es.ts`, `scripts/i18n-es.json` (never run `pnpm i18n`). Memory: `/Users/bekbolsun/invai/.claude/agent-memory/web-engineer/`.
- Other agents at the same time: qa-engineer (`invai-web/e2e/**`), ai-engineer (`invai-backend/src/ai/**`).
- Commit only your paths, attribution line at the end. **Don't push; only the tech lead pushes after the gate.** Stop your dev server (record its PID) before you hand back.
- Trim output. Report (≤ 60 lines) to `invai-docs/waves/P7/reports/T-P7-3.md`, one line per milestone as you go.

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
