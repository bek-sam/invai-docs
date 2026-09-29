# Review of T-22-5 (round 1)

- Reviewer: architect on Sonnet 5
- Author: backend-engineer on opus
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 9e8ea0c` vs `git -C invai-contracts show 81afad4` | Identical diff (`src/channels.ts`, `src/schemas.test.ts`); only the commit SHA/date differ. The 184149c/78d2469→0f2f413/9e8ea0c revert-then-reapply is the known gated-commit dance (memory: `project_gated_contract_commits.md`), not drift. |
| `invai-contracts`: `pnpm typecheck` | `tsc --noEmit` clean |
| `invai-contracts`: `pnpm test` | `Test Files 8 passed, Tests 88 passed` (matches report) |
| Read `CHANGELOG.md` 0.8.0 entry | Coherent: 3-commit gated release explicitly documented, no floor-compat bump needed (additive only) |

## Design checklist
- **Vendor email as outbox/job:** `sendSheetToVendor` writes `pending` row + emits `sheet.sent` inside the tx; `deliverSheetJob` (queue `ship`, jitter-free but 5 attempts/exp backoff) runs after commit via `onEvent`. Matches the catalog/shipping job pattern (emit-in-tx, act-outside-tx).
- **State machine (pending→sending→sent/unknown/failed):** correct claim-then-act shape; the DB row's status guard (not the BullMQ jobId) is the true idempotency key, consistent with `idempotent-job` skill guidance.
- **No auto-retry on `unknown`:** justified — shipping's label buy/void *does* read back (EasyPost `GET /shipments/{id}`) before deciding to resend; SMTP has no equivalent read-back API, so "surface unknown, let a human resend" is the correct application of the same principle (idempotent-side-effect: "only call again when the read-back proves nothing happened"), not an inconsistency.
- **resendEmail → contract error:** `RESEND_TOO_SOON` (429, `retryAfterSec`/`lastSentAt` in `data`) is declared on `vendors.sheets.resendEmail` in `src/contract/vendors.ts` and thrown by `resendSheetEmail`; web can translate it directly. `SHEET_NOT_SENT`/`VENDOR_USES_PORTAL` also match.
- **Listing attributes, ADR 0017:** `foldAttributes()` in `modules/ai/service.ts` is the sole fold point (trim, drop-empty, first-wins, `__proto__` stays data via `Object.fromEntries`), matching the ADR's rule 2–3 exactly; no other shape introduced.
- **Advisory lock key:** `pg_advisory_xact_lock(hashtextextended('order_import:<connectionId>', 0))` — a hashed 64-bit key, distinct namespace prefix from `privacy/service.ts`'s `tenant_export:<companyId>` (same hashtextextended pattern, already precedent) and from the migration lock's plain small integer `468_241` (`pg_advisory_lock`, single-arg, session-level in `db/migrate.ts`). Collision risk is negligible and the pattern is now used twice consistently.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| Contract coherence (0.8.0 story) | yes | CHANGELOG's 3-commit gated plan matches the actual revert/reapply history; content identical to 81afad4 |
| Vendor email job design | yes | `delivery.ts`/`jobs.ts` reviewed above |
| Listing attributes one-shape | yes | `foldAttributes` reviewed above |
| Advisory lock non-collision | yes | reviewed above |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (backend: vendors/finance/orders/ai grant, per card; contracts: architect's own prior commit)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; no weakening observed in the diffs read
- [x] Tenancy/idempotency/money/en-es: not in architect's scope this round (primary + backend-foundation cover); contract side is additive, cents/inches conventions untouched
- [x] Decisions recorded where needed (ADR 0017 applied correctly)

## Optional notes (not blocking)
None.

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
