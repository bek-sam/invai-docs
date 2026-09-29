# 0018. Token budget for the agent team

- Status: accepted
- Date: 2026-09-29
- Decided by: owner

## Context
On the night of 2026-09-28 to 29, the session usage limit stopped the whole team about every 4–5 hours, and 10-minute stream stalls stopped it several more times. Each stop cost more than the pause itself:
- Relaunched agents redid work they had already finished; the T-22-1 reviewer was launched three times.
- One tech-lead agent stayed alive across waves 20–25, so every turn re-read a very long context.
- Up to 6 agents ran at once, against a cap of 3–4.
- Test and E2E output went into context untrimmed.

The owner asked for the most work per token.

## Decision
- Every agent follows the "Token budget" section of `CLAUDE.md`: trim command output, read narrowly, test in layers, keep handoffs short, and save progress after each milestone.
- The tech lead chooses the cheapest model that can do each card and records it on the card:
  - `sonnet` is the default for builders and co-reviewers.
  - `haiku` is for mechanical work.
  - `opus`/`fable` are for primary reviews, security, money and side-effect code, migrations and planning.
- At most 3 agents at once, reviewers included.
- A fresh tech lead starts for each wave from `wave.md`, instead of one long-lived tech lead.
- Role file defaults move to `sonnet` for roles whose work is mostly writing or UI: product-manager, product-designer, compliance-officer, customer-success, growth-marketer, data-analyst, web-engineer and floor-engineer.
- The review rules don't change: an independent review of every card, with co-reviewers per risk flag.

## Consequences
- Much lower cost per card, and fewer limit hits.
- Some risk of lower quality on UI and doc work, which the unchanged opus primary review offsets. If sonnet UI cards fail review twice as often as before, move `web-engineer` and `floor-engineer` back to opus.
- The tech lead reports "tokens per card" in the wave metrics (already in `team/operating-system.md`), so the effect is measured.
