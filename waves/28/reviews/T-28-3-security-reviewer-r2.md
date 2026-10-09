# Review: T-28-3 Amazon 18-month retention sweep (security co-review, round 2)
Reviewer: security-reviewer on Opus 5.5. Author: backend-engineer (privacy) on Opus 5.5. Input: invai-docs `6bc2d27` (docs only).

## Verdict: approve

## What I checked (round 1 blocking item only, no new scope)
- `decisions/0026-amazon-non-pii-retention.md`: `item_artwork` removed from the "InvAI's own records, keep" row and given its own line naming `values`, `file_key`, `preview_key` as buyer personalization (PII), not cleared today, to be cleared by the PII sweep, open gap S-56 / B-293, not part of this sweep. Accurate against `personalization/service.ts:494` and the `it.fails` proof in `src/modules/privacy/security.test.ts`.
- `labels` row added: tracking number and label key kept, label PDF removed by the 30-day S3 rule. Matches what I asked for.
- B-293 exists in `waves/backlog.md` (owner backend-engineer (privacy), due 2026-11-08, Medium 30-day clock).
- Code unchanged in round 2 (round 1 code checks stand: tenant scoping, counts-only logs/audit, idempotency, fences).

## Applied after approval (my paths)
- 0026 status: `proposed (security accepted 2026-10-09; compliance pending)`.
- `security/v1-review.md`: DPP 18-month row now Partial with the promised text (OI-19 titles/refund notes; S-56/B-293); S-56 note updated that 0026 was corrected.

## Optional notes
- Index row for 0026 in `decisions/README.md` still says `proposed`; correct as is until compliance accepts.
