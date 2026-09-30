# Wave 23b: P2 sweep, part 2b: imaging, AI polish and E2E coverage

- Split from wave 23 on 2026-09-29 (owner approved T-23-6 and T-23-7, and the 5-card cap applies). Card files stay in `waves/23/` under the same ids. Plan reviews as for wave 23 (PM and architect, 2026-09-28). Decision 0019 co-reviewer cuts are already applied.
- Runs after wave 23's gate, and before or alongside analytics A1, as the PM ranks it.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-23-3 Imaging polish and film-use metric (B-103 rest, B-41) | imaging-engineer | sonnet | reviewer (opus) + architect (bounds in contract) | files | planned |
| T-23-4 AI and market polish: markdown and footer, stream close, mock follow-ups, eval cleanup, detrended seasonality in code, shared ConfidenceBadge adoption (B-114, B-131, B-132, B-135, B-165; B-134 via a product-designer grant) | ai-engineer (+ backend-engineer market for the B-131 engine by grant; never `specs/**`) | sonnet | reviewer (sonnet) | ai | planned |
| T-23-5 E2E and test coverage: roles, Spanish, offline replay, clickIfShown, property tests, axe, visual regression, runtime contract test, i18n drift, scale seed profiles, market tool latency (B-22 rest, B-34, B-38, B-97 rest, B-138, B-142) | qa-engineer | sonnet | reviewer (opus) | — | planned |

## Integration gate
- [ ] `pnpm gate` (T-23-6) passes on a fresh seed; screens looked at in en/es
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
