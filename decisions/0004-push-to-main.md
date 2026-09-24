# 0004: Work on main, push after tests and an independent review

- Status: accepted (2026-09-24); review requirement added 2026-09-24 by the owner's team rules
- Type: owner

## Context
The owner does not want branches, pull requests or merges. The owner also requires that nothing ships without passing tests and a review by a different agent.

## Decision
- All work happens on `main`, and the owner never has to merge or pull.
- A task is pushed with `git push origin main` only after its definition of done passes **and** the `reviewer` (plus any required co-reviewers) approves it with evidence.
- In a wave, owners commit their own paths and the tech lead pushes after the integration gate. An agent working alone pushes only after its review passes.
- Never force-push or rewrite pushed history.

## Consequences
Review happens before the push, not in a PR. The review record lives in `invai-docs/waves/<n>/reviews/`.
