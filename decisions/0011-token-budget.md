# 0011: The team works to a token budget

- Status: accepted (2026-09-25), at the owner's request
- Type: process

## Context
The plan's usage limits stopped the team twice. Per card, usage was:
- Opus builders: 250–400k tokens
- reviewers: 150–300k
- gates: 100–450k

The main drivers were Opus builders on routine cards, up to 40 screenshots per card viewed again by reviewers, the full E2E suite run three times per card, long doc reading, and long reports.

## Decision
- Builders run on Sonnet. Opus is kept for cards flagged payments, security, concurrency or data integrity.
- Reviewers use a model different from the builder's, usually Sonnet.
- Every agent reads `team/agent-brief.md` plus its card, instead of the full doc set.
- At most 6 screenshots per builder, and reviewers look at at most 3.
- Only the wave gate runs the full golden-path suites.
- Agent replies are at most 8 lines; full detail goes in the report file.

What stays unchanged: an independent review of every change, co-reviews for risk flags, and the full integration gate before every push.

## Consequences
We expect roughly 40–60% less usage per wave. If a gate starts catching bugs that a card review should have caught, bring back reviewer E2E for that area.
