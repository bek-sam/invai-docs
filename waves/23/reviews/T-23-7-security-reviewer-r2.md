# Review of T-23-7 (round 2, security co-review)

- Reviewer: security-reviewer on Sonnet 5 | Author: platform-sre on Sonnet | Verdict: **approve**

## Scope
CI permissions (decision 0019): deploy-key restoration vs the ruling, no new secrets, `persist-credentials`, `permissions:`, SHA pins, no `pull_request_target`/deploy/`aws`, S-40 redaction, reviewer r2's N3. Round-2 diff only (infra range excludes T-23-6's `3215fc6`).

## Evidence I re-ran
| Check | Result |
|---|---|
| `git diff --stat` per repo | Only `.github/workflows/**` in 6 repos + `invai-infra/scripts/ci/run-e2e.sh` |
| Keys vs `git show origin/main:.github/workflows/ci.yml` | Restored to exactly pre-card pins: ui/backend key only contracts; web/floor key contracts+ui. No repo gained a new key |
| `e2e.yml` diff (backend/web/floor) | `on:` is `workflow_dispatch` only (`push:` removed); contracts/ui reuse the 2 keys; other siblings left uncredentialed (OI-21), not patched |
| checkout vs `persist-credentials: false`, all 9 workflows | 30/30, including own-repo checkouts |
| `grep -n "^permissions:"` | one top-level `contents: read` per workflow, no job widening |
| `grep -rn "secrets\."` | 12 hits, all `ssh-key:` on the 2 restored keys, none in `run:` |
| `pull_request_target` / `configure-aws-credentials` | no hits |
| `run-e2e.sh` redaction diff | `sed` (password, `st1.<uuid>.<base64url>`, `role=pin`) piped before `tee` — live log and uploaded file both redacted |
| Token format: `floor-auth.ts:69` → `crypto.ts:96-98` (`base64url`) | Redaction charset `[A-Za-z0-9_-]` exactly covers it — fix is correct, not just plausible |
| `actionlint` | Not installed here; author + `reviewer` r2 each independently ran v1.7.12, both 9/9 clean — accepted |

## N3 (reviewer r2): traces may carry the station token
Playwright `trace: "retain-on-failure"` records headers, so a failed floor E2E trace can carry
`Authorization: Station <token>` — a different capture path than S-40's seed log, untouched by the
`sed` fix. Same bounded blast radius as S-40 (random per-job token, scoped to an ephemeral Postgres
destroyed at job end, all 7 repos private, 7-day retention): not blocking. Filed as **S-43** (Low),
owner platform-sre.

## Blocking findings: none

## v1-review.md updates
S-40 and S-41 marked **Fixed** with round-2 evidence. New: **S-43** (Low, trace token exposure).

## Checks
- [x] Deploy keys restored only where they were; no new secrets; none in `run:`
- [x] `persist-credentials: false` on every checkout (30/30); top-level `permissions: contents: read`, no widening
- [x] SHA pins unchanged from r1 (diff doesn't touch pins); no `pull_request_target`, deploy or `aws` steps
- [x] S-40 redaction verified correct against the real token format
- [x] N3 assessed and recorded (S-43), no control weakened
