# Review of T-P2-4 (round 2)

- Reviewer: reviewer on Claude Opus 5.5. Author: web-engineer (report says Opus 5.5, session Sonnet 5). Commit `59155c1`.
- Verdict: **approve**. The round 2 ruling is met. r1 finding 1 (dropped reason) is fixed, and there are no new findings.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test --reporter=dot` (invai-web @edc66d9) | exit 0; 21 files, 136 tests passed |
| `VITE_API_URL=http://localhost:3000 pnpm build` | built in 1.40s |
| `git show --stat 59155c1` | 3 files: order-detail.tsx (+24/-11, Timeline only), timeline-reason.ts, timeline-reason.test.ts. All owned |
| Throwaway probe test (built messages with the exact backend template, then deleted the file; tree left clean) | 1 passed: null `from` + `reprint: misprint` → reason `reprint: misprint`; `a (b) c: d` and `x)` → kept verbatim; empty reason → none; `->` arrow and `""` → raw |
| `scan-test-weakening.sh invai-web 81615f3` | the only hits are in `e2e/helpers/ui.ts` from T-P2-3 `edc66d9`, not this card; this card adds 9 assertions and removes none |
| Browser | skipped as instructed; the gate covers the screen |

## Helper vs backend (`orders/service.ts:639`)
The backend builds `${fromState ?? "new"} → ${toState}${reason ? ` (${reason})` : ""}`. The helper builds the same prefix from the same row's `from`/`to` (`timeline-reason.ts:18`), then takes everything between ` (` and the final `)`. That keeps any parentheses or colons inside the reason. An empty reason gives no wrapper, so nothing shows. A message that doesn't start with the prefix is shown whole. Audit kinds still take the untouched `e.message` branch (order-detail.tsx:459-460).

## Acceptance criteria (card plus round 2 ruling)
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | Badges unchanged from r1 (order-detail.tsx:437-447). "New"/"Nuevo" shows when `from` is null |
| 2 (ruling) | yes | The reason shows untranslated after the badges, in `(…)`. The fallback shows the whole message. Covered by 3 unit tests plus my probe |
| 3 | yes | The non-`state_changed` branch is identical |
| 4 | yes | No new strings; `scripts/i18n-es-missing.json` absent |

## Blocking findings
none

## Checks
- [x] Owned paths only; no scope creep. [x] Tests added (3), none weakened. [x] Tenancy, money, idempotency and PII: not touched (web render only).

## Optional notes (not blocking)
- On the fallback path, the raw message can show English state words in es. The ruling accepts this, and the backend never produces this format today.
- The typed `reasonCode` follow-up (with B-224) stays with the architect.
