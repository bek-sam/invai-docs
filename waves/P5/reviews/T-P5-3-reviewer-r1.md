# Review of T-P5-3 (round 1)

- Reviewer: reviewer on sonnet
- Author: architect on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show --stat d6d038b` | 6 files: package.json, src/compat.ts, src/p5-reasons.test.ts (new), src/schemas/alerts.ts, src/schemas/orders.ts, src/today-actions.test.ts |
| `pnpm typecheck && pnpm lint && pnpm test` (invai-contracts) | tsc clean; biome "Checked 61 files, no fixes"; 11 files / 132 tests passed |
| `pnpm typecheck` (invai-web) | exit 0, no output |
| `pnpm typecheck` (invai-floor) | exit 0, no output |
| `pnpm typecheck` (invai-backend) | exit 0 (`tsc --noEmit`); `git status --short` shows only `M src/db/seed/builder.ts` as other agents' WIP, not touched by this card, and it did not cause any error |
| `scan-test-weakening.sh invai-contracts origin/main` | 1 removed assertion (`CONTRACT_VERSION toBe("0.10.0")`), replaced by `isContractVersionAtLeast(..., "0.10.0")` in the same file; exact version pinned instead in the new `p5-reasons.test.ts` (`toBe("0.11.0")`) — the documented, non-weakening pattern |
| `grep -rln "ALERT_MESSAGE_CODES\|TIMELINE_REASON_CODES\|messageCode\|reasonCode"` across backend/web/floor `src` | one hit, a comment in `invai-web/src/features/orders/timeline-reason.ts` — no functional consumer to break |
| `git -C invai-contracts diff --stat origin/main` | same 6 files as above; all inside owned paths (`src/**`, plus `package.json` — bump explicitly granted) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | `Alert.messageCode?: AlertMessageCode`, `Alert.params?: AlertParams` added, both optional; doc comment on `AlertParams` lists keys per code via `ALERT_MESSAGE_PARAM_KEYS`; `shipBy` is `Timestamp` (ISO string, `z.iso.datetime`); `title`/`message` unchanged |
| 2 | yes | `TimelineEntry.reasonCode?: TimelineReasonCode` (22-value closed enum) + `reasonParams?: TimelineReasonParams` (sheetName/reprintReason/holdReason/cancelReason, each by its existing enum); matches R1's producer-derived list exactly (unknown_sku … carrier_delivered) |
| 3 | yes | Diff touches no existing enum array (`ALERT_KINDS`, `TIMELINE_KINDS`, `HOLD_REASONS`, `CANCEL_REASONS`, `REPRINT_REASONS` all untouched in the hunks, and pinned by `p5-reasons.test.ts`'s "keeps the existing enums exactly as they were" test); all new fields `.optional()`; nothing removed; consumer typechecks above all green |
| 4 | yes | `invai-docs/waves/P5/reviews/plan-architect.md` R1 has the field names, both enums' full value lists, `ALERT_MESSAGE_PARAM_KEYS`, and the reason-mapping rules; the shipped code matches it value-for-value (spot-checked `ALERT_MESSAGE_CODES`, `AlertParams` keys, `TimelineReasonParams` keys) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` above; `package.json` bump was pre-granted per the card)
- [x] Nothing outside scope (no procedure added, no backend/web code touched, matches "Out of scope")
- [x] Tests exercise the behavior, and none were weakened — the one changed assertion is a legitimate version-pin handoff (memory: contract-version-pin-tests), confirmed the new test pins the exact 0.11.0 version and both enums' round-trip/old-shape/unknown-code/param-filtering cases
- [x] Tenancy/idempotency: n/a (contract-only, no DB or request-path code)
- [x] Money in cents, en/es text: n/a to this card (no UI strings, no money fields added)
- [x] Decisions recorded where needed: none needed — report explains this follows the existing `DigestActionParams` precedent, not a new cross-cutting rule; agree

## Optional notes (not blocking)
- `TIMELINE_REASON_CODES` ordering in the source array differs slightly from R1's prose order (e.g. `on_sheet`/`sheet_received`/`scan_match`/`reprint` grouped earlier than in R1's rule-4-then-rule-3 narrative); the value set is identical (22/22) and order carries no semantic weight here since no test pins a specific order for this array. Not blocking.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
