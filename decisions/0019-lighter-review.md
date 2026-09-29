# 0019. Lighter review: co-reviewers only for real risk; full suites once per wave

- Status: accepted
- Date: 2026-09-29
- Decided by: owner

## Context
In waves 20–25, cards averaged about 3 reviews each (75 review files for about 25 cards), and every reviewer re-ran every repo's full suite (about 5 minutes for the backend). The gate then ran it all again. Since 2026-09-28, about a quarter of the lines written were product code. The owner asked for most of the effort to go to development.

## Decision
- **Every card still gets an independent primary review.** The primary reviewer also covers UI, consumer impact and golden-path risk.
- **Co-reviewers only for real risk:**
  - `architect` for contract changes
  - `backend-foundation` for migrations
  - `security-reviewer` for tenancy, PII, auth, webhooks, files, payments, or platform-sre changes to secrets, IAM, network or CI permissions
  - `ai-engineer` for prompts
  - `product-designer` for new screens or components
  - QA's check moves to the integration gate.
- **Reviewers re-run** typecheck, lint, the changed and affected tests, and the RLS and authz tests. They run the full suite only when shared code changed. The full suites and E2E run once per wave, at the integration gate, which stays mandatory before any push.
- **Waves 24 and 25** (deploy and CI prep) wait until the owner starts the AWS setup. Analytics A1 and A2 go first.

## Consequences
- Fewer agent runs per card, and more of the budget goes to features.
- Regressions outside a card's modules are caught at the gate rather than in review, so a gate failure can mean a second round for one card. Watch the gate failure rate. If it rises above one in three waves, restore full suites in review.
