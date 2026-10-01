# Review of T-P1-5 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: floor-engineer on Opus 5.5 (card says sonnet; ui copy-only flag, no cross-model requirement)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test --reporter=dot` (invai-floor @ ef1d926) | pass; 100/100 tests |
| `pnpm build` (no env) | fails: vite.config requires `VITE_API_URL` (pre-existing CSP guard, not this diff) |
| `VITE_API_URL="" pnpm build` | pass, dist + sw.js generated |
| `scan-test-weakening.sh invai-floor ef1d926~1` | 0 removed / 2 added assertions; hits = `vi.mock` of collaborators (`@invai/ui`, queue hook, store, `submit`, feedback), not of `QcStation`; no skip/only, no snapshot/config change |
| New `QcStation.test.tsx` run on base (`git archive ef1d926~1`) | 2 failed: "expected 'Aprobar' to be 'Aprobado'", "'Rechazar' to be 'Rechazado'" — test proves the fix |
| `grep` e2e for QC text | `e2e/press.spec.ts:85-86` uses button "Pass" and "Passed: order …"; heading "Passed" does not contain that string, so no strict-mode clash |
| Screenshot `/tmp/qc-05-pass-result-es.png` (looked at) | 1280×800 es: green panel, check icon, "APROBADO", "Aprobado: pedido #1048", "Enviado", "Siguiente"; no raw keys, no truncation |
PIDs started: none.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `QcStation.tsx:145-146` uses `floor.qc.passResult`/`failResult`; buttons at :126/:133 keep `pass`/`fail`. es "Aprobado"/"Rechazado" vs "Aprobar"/"Rechazar" |
| 2 | Yes | Order line unchanged (`reason` = `floor.qc.passed/failed`); tone ok vs warn (:140), sound `feedback` ok vs warn (:89) unchanged; screenshot shows pass |
| 3 | Yes | Keys in `en.ts:248-249`, `es.ts:251-252`; typecheck green. Past-tense result words; no verb so tú form n/a |
| 4 | Yes | `QcStation.test.tsx` two es tests on the h1; red on base, green on head |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (en.ts, es.ts, QcStation.tsx, QcStation.test.tsx)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened (mocks are collaborators only)
- [x] Tenancy/idempotency/money n/a (copy-only); en and es both present
- [x] Decisions: none needed

## Optional notes (not blocking)
- Report AC2 says fail uses the red/X "blocked" tone; the code uses `warn` (amber triangle) for fail and `blocked` only for errors. Behavior unchanged and still distinct from pass; just a report inaccuracy.
- Fail path verified only by unit test, not in browser (disclosed).
- Card's verification command omits `VITE_API_URL` for `pnpm build`; future floor cards should include it.
