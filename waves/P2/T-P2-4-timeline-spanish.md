# T-P2-4: Order drawer timeline shows item states in the user's language (B-223)

| Field | Value |
|---|---|
| Wave | P2 |
| Scope ref | `always-in-scope: bug` (B-223, Low: English text under the Spanish UI on a golden-path screen); PM rank 1 (`reviews/plan-pm.md`) |
| Owner | web-engineer |
| Reviewer | reviewer (opus) |
| Co-reviewers | none (no contract change: the timeline entry already carries `from` and `to` state codes, `invai-contracts/src/schemas/orders.ts:~230`) |
| Risk flags | ui (copy only) |
| Model | sonnet |
| Depends on | T-P2-1 committed (same agent role, same repo; runs after it) |

## Tech lead's notes
- Backend builds `message` as `` `${from ?? "new"} → ${to}${reason ? ` (${reason})` : ""}` `` (`invai-backend/src/modules/orders/service.ts:639`); web prints it raw (`invai-web/src/features/orders/order-detail.tsx:434`).
- B-224 (Today alert bodies) needs a contract change (alert params); it is **not** in this card (next wave, architect first).

## Round 2 ruling (tech lead, after reviewer r1 escalate)
- r1 dropped the transition reason entirely (it lived only in `message`), a regression (qc_fail, buyer_request, reprint rows). Ruling, superseding the "don't parse `message`" line for this card only: render the translated badges, then the reason **as the backend wrote it** (no translation), taken as the text after the exact prefix the backend builds (`<from ?? "new"> → <to>`, `orders/service.ts:639`) and its ` (`…`)` wrapper. If the message doesn't start with that prefix, show the whole message under the badges. One small pure helper with unit tests (prefix match, no reason, unexpected format). A typed `reasonCode` with translations is the architect's follow-up (backlog, with B-224).

## Owned paths (edit)
- `invai-web/src/features/orders/order-detail.tsx` (the timeline rendering only); a small helper beside it if needed; generated i18n via `pnpm i18n` (`src/i18n/*.ts`, `scripts/i18n-es.json`).

## Read-only paths
- `invai-backend/**`, `invai-contracts/**`, `invai-web/e2e/**`, every other web file.

## Acceptance criteria
1. For `state_changed` entries the drawer renders `from` and `to` through the same translated item-state labels the app already uses elsewhere (find them; reuse, don't duplicate), with "new" when `from` is null. Under es no English state word shows.
2. The transition reason stays as the backend gives it, shown after the translated states (architect ruling 1: reason has no typed field, only the free-text `message`; a `reasonCode` field is the architect's follow-up with B-224). Don't parse `message`.
3. Other timeline kinds render exactly as before.
4. en and es strings written with `write-plain-language-copy`; `scripts/i18n-es-missing.json` absent or without your keys.

## Verification
- `cd invai-web && pnpm typecheck && pnpm lint && pnpm test && pnpm build 2>&1 | tail -n 30`.
- Slot: API :3000 + web :5173 (after T-P2-1 frees it; record and stop PIDs; no reseed). Open an order with pressed/packed items, screenshots at 1440 and 390 px, en and es; look at them.

## Budget
- About 1.5 hours.

Commit only your paths. Don't push. Report: `invai-docs/waves/P2/reports/T-P2-4.md` (at most 60 lines).
