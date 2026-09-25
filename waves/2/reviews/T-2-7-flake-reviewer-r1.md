# Review of T-2-7 flake fix (round 1)

- Reviewer: reviewer + web-engineer (feature owner, vendor portal) on Sonnet 5
- Author: qa-engineer
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web log --oneline -1` | `33d15a4 Fix clickIfShown flake: bounded wait instead of instant isVisible` |
| `git -C invai-web status --short` | clean |
| `git -C invai-web diff --stat 33d15a4^ 33d15a4` | `e2e/golden-path.spec.ts \| 60 +++++++++++++++++++++++++++++++++++++++++--------` (1 file, +51/-9) |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-web 33d15a4^` | "Result: no hits" (deletions=none, skips/mocks/sleeps=none, assertions removed=0 added=2, snapshots=none, config=none, test-only branches=none) |
| `pnpm typecheck` (invai-web) | pass (`tsc --noEmit`, no errors) |
| `pnpm lint` (invai-web) | pass (`biome check .`, 117 files, no fixes needed) |
| `git -C invai-contracts show a3b4067:src/states.ts \| grep -n "SHEET_TRANSITIONS" -A6` (read `invai-contracts/src/states.ts` directly) | `sent: ["acknowledged", "printed", "cancelled"]` — printed is directly reachable from `sent` |
| `grep -n "SHEET_TRANSITIONS\|934" invai-backend/src/modules/production/sheets.ts` | line 934: `if (!opts.force && !SHEET_TRANSITIONS[from].includes(to))` — the state machine's own transition table is enforced generically, not re-implemented per-step |
| `sed -n '180,200p' invai-web/src/routes/_app/vendor/sheets.$sheetId.tsx` | `{update \&\& s === "sent" \&\& (...Acknowledge...)}` and `{update \&\& (s === "sent" \|\| s === "acknowledged") \&\& (...Mark printed...)}` — the vendor portal itself shows "Mark printed" directly from `sent`, no forced Acknowledge step |

Did not re-run E2E per the tech lead's instruction; the author (qa-engineer) ran `pnpm e2e` 15/15 on three fresh seeds (documented in `invai-docs/waves/2/gate.md` §6) plus a required `E2E_API=1 api-golden-path.spec.ts` pass (13/13), with full cleanup recorded. That evidence is credible given the detail (including an honestly-reported unrelated Valkey lock artifact from the author's own worker-restart cycling, fixed and re-verified) and is consistent with what the diff itself would be expected to do.

## Acceptance criteria (from gate.md §6, this task's spec)
| # | Criterion | Met? | Evidence |
|---|---|---|---|
| 1 | `clickIfShown` no longer does a single instantaneous check; waits (bounded) for the button | Yes | Diff: `button.waitFor({ state: "visible", timeout })` replaces `button.isVisible().catch(() => false)`, default `timeout = 8_000` |
| 2 | A button that's genuinely not needed still resolves promptly as "not shown" (no suite-wide slowdown) | Yes | `waitFor` still resolves `false` via `.catch`, bounded at 8 s per call, not a suite-wide timeout |
| 3 | Steps 6–7 assert domain state after each *required* click, so a wrongly-skipped click fails loudly at the point of the skip | Yes | Three new/strengthened `poll(...)` calls: sheet off `"ready"` after send, sheet in `["printed","shipped","received"]` after Mark printed, sheet in `["shipped","received"]` after Mark shipped (was a single `api...get()` read, now polled), item in `["transfer_in","pressed","packed","shipped"]` after Mark received (was a single read, now polled) |
| 4 | Acknowledge stays optional and matches backend behavior | Yes | `invai-contracts/src/states.ts` `SHEET_TRANSITIONS.sent = ["acknowledged","printed","cancelled"]`; backend enforces this table generically (`sheets.ts:934`); vendor portal UI shows "Mark printed" whenever `s === "sent" || s === "acknowledged"`, not gated on acknowledge. The comment added at the Acknowledge call site ("no state to assert for it here beyond the toast") is accurate — there's genuinely no separate domain-state consequence of acknowledging that isn't already covered by the printed-state poll |
| 5 | No product code touched, only `e2e/golden-path.spec.ts` (qa-engineer's owned path) | Yes | `git diff --stat` shows exactly one file, `e2e/golden-path.spec.ts` |
| 6 | `pnpm typecheck` / `pnpm lint` pass in invai-web | Yes | Re-ran both, both pass |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` — `e2e/golden-path.spec.ts` only, qa-engineer's `e2e/**`)
- [x] Nothing outside scope (test-code-only fix for the filed flake in gate.md §4; no product code, no unrelated refactors)
- [x] Tests exercise the behavior, and none were weakened — scan script: 0 assertions removed, 2 added, no skips/mocks/sleeps/loosened config/rewritten snapshots; the suite is strictly stronger (bounded wait instead of instant check, plus 3 new/strengthened poll-based state assertions after every required click in steps 6–7)
- [x] Tenancy / idempotency / money-in-cents / en-es — n/a, this diff touches only E2E test helper/assertion code, no product logic, no user-facing strings, no DB access patterns changed
- [x] Decisions recorded where needed — n/a, no new decision required; this closes the flaky-test quarantine opened in gate.md §4 per the 14-day disposition, and the fix itself is documented in gate.md §6

## Optional notes (not blocking)
- The `waitFor` bounded timeout (8 s) and `poll` timeout (60 s default from `e2e/helpers/api.ts`) are asymmetric by design — the click-wait only needs to cover render latency, the state-poll needs to cover an actual backend round trip (vendor action → outbox/DB write). Both are reasonable; no change requested.
- Nice touch: the new comment at the Acknowledge call site is precise about *why* no extra assertion was added there rather than just omitting one silently — makes the intentional asymmetry between Acknowledge and the required clicks legible to the next reader.

Recommend closing the flaky-test quarantine from gate.md §4 on this approval.
