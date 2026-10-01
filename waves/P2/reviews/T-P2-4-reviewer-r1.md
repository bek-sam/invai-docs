# Review of T-P2-4 (round 1)

- Reviewer: reviewer on Claude Opus 5.5
- Author: web-engineer on Claude Opus 5.5 (the card asked for sonnet)
- Verdict: **escalate**. The code is correct for AC1, but AC2 as the card states it is unmet. The card, architect ruling 1 and wave.md line 38 disagree on what AC2 means, so this is a scope call for the tech lead, not a fix the author can make.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test --reporter=dot` (invai-web @81615f3) | exit 0; 20 files, 133 tests passed |
| `pnpm build` | fails at config load because `VITE_API_URL` must be set (expected, the T-P2-1 CSP guard). `VITE_API_URL=http://localhost:3000 pnpm build`: built in 3.15s |
| `scan-test-weakening.sh invai-web 81615f3~1` | no hits (the card adds no tests) |
| `git show --stat 81615f3` | 4 files: order-detail.tsx, en.ts, es.ts, scripts/i18n-es.json, all owned; worktree clean |
| node check of `ORDER_ITEM_STATES` against invai-ui `orderState` en/es | 0 missing in either language |
| `grep timelineNewState` in en.ts:1505, es.ts:1533, i18n-es.json:1272 | consistent ("New"/"Nuevo"); `scripts/i18n-es-missing.json` absent |
| dev DB (read-only): `select reason,count(*) from order_item_transitions where reason is not null` | non-null reasons on many rows: buyer_request 24, qc_fail 17, mapped 15, "on sheet … #1" 38, scan match 4, QC pass 3 |
| Browser | not re-run. I relied on the author's 6 screenshots plus a code read, because the blocking issue below is not visual |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | order-detail.tsx:434-445 reuses the ui `StatusBadge` (`orderState.*`, every state has en and es). "New"/"Nuevo" shows when `from` is null. No English state codes remain in the state_changed path |
| 2 | **no** | The card says the reason "stays as the backend gives it, shown after the translated states". order-detail.tsx:434 now renders only the badges for `state_changed` and never shows `e.message`, so the reason is gone in both languages. Before this change, en users saw "(qc_fail)", "(buyer_request)", "(reprint: …)" |
| 3 | yes | Audit rows always send `from`/`to` null (backend orders/service.ts:648-649), so the old badge branch never fired. They still get `e.message` unchanged (order-detail.tsx:447) |
| 4 | yes | One new key, en "New" / es "Nuevo" (an adjective agreeing with "estado"). The three hand-edited files match; the missing-keys file is absent |

## Blocking findings
1. `invai-web/src/features/orders/order-detail.tsx:434-448`: for `kind === "state_changed"` the `e.message` branch is dropped, and with it the only carrier of the transition reason (backend `orders/service.ts:639`). Failure scenario: a presser reports a reprint (`floor.ts:636`, `reprint: <code>`) or QC fails an item (`qc_fail`). The office opens the order drawer and sees "Pressed → …" with no reason, in English or Spanish. The current UI shows that reason.
   - Why this is an escalation and not changes-required: the card forbids parsing `message`, and the only other way to show the reason is the raw message, which brings back the English state words AC1 removes. wave.md line 38 records "reason shown as given per ruling 1", which is not what shipped. The author's report says AC2 is "descoped", but the card text was never amended.
   - Options for the tech lead:
     - A) Amend AC2 to "deferred" and log the lost reason as a known regression until `reasonCode` lands.
     - B) Pull the architect's additive `reasonCode` (or `reason`) field forward: contracts, then a one-line backend change, then web renders `t("transitionReason.<code>", raw)`. Note that some reasons are dynamic ("on sheet 2026-10-01 #1", "reprint: <code>"), so B needs a code plus params.
     - C) Show the raw reason only in en until B lands.
   - My recommendation: B. If B can't be scheduled this wave, then A with an explicit backlog row.

## Checks
- [x] Only owned paths changed (4 files, all on the card)
- [x] Nothing outside scope
- [~] Tests: none weakened, but none added either. The new branch has no unit test, and the `from === null` path was never exercised (no seed row, per the author's report)
- [x] Tenancy, idempotency and money: not touched (web render only). en/es text present
- [ ] Decisions recorded: the AC2 descoping is not reflected in the card, and wave.md line 38 misstates it (see finding 1)

## Optional notes (not blocking)
- A small render test for `Timeline` (state_changed with null `from`, plus an audit kind) would cover the gap the seed can't.
- The card's `Model` says sonnet, but the report says Opus 5.5.
