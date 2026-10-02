---
name: docs-policy-review-checks
description: How to review ops/security/compliance docs cards (incident plan, access policy, v1-review status tables) — claims contradicted by the cited file are the real defects, not missing links.
metadata:
  type: feedback
---

For docs-only policy cards, a link check alone catches almost nothing. The defects are claims that the cited file contradicts. Found 2026-09-28 in T-21-2/T-21-3 r1:
- Claims that "guard-bash.py blocks X": probe the hook with a JSON payload via python subprocess, building the command string by concatenation (the live guard blocks inline strings, and guard-paths blocks writing payload files outside reviews/memory). `sst secret set` and `gh api -X PUT .../protection` are NOT blocked.
- Alert kinds listed as detection sources: grep backend for where each is raised (`qc_fail_spike` is never raised). All alerts are tenant rows (shop-visible, not InvAI-visible).
- "Runs on the mock when the key is missing": false in production (env.ts PRODUCTION_KEYS + ALLOW_MOCKS refuse boot). Stripe is live (B-53), and research 12 G12 is stale.
- BETTER_AUTH_SECRET rotation also breaks every floor PIN (FLOOR_TOKEN_SECRET fallback, not an SST secret).
- "No backlog id yet" cells: grep backlog.md by topic (B-23 KMS, B-74 RDS backups, B-75 log retention, B-77 missing SST secrets).
- S-id count lines: tally the rows with a script. Summary lines drift from the table.
- Etsy breach path is in research 10 (24 h, dpo@etsy.com + seller). Amazon address differs between research 10 and research 12.

**Why:** these docs feed the Amazon/Shopify evidence pack; an overstated control there is a compliance risk.
**How to apply:** for every "enforced by X" or "system does Y" sentence, open X and check.

Round 2 (T-21-2/T-21-3, same day): both authors fixed every blocking finding correctly and cited real
backlog ids (new ones like B-185..189 do get filed between rounds — always re-grep backlog.md, don't
assume a round-1 "no id yet" is still true). One recurring non-blocking pattern worth flagging but not
blocking on: cited line numbers drift by 1-2 lines from the actual field/call-site line (e.g. citing a
function's opening line instead of the specific field inside it) — still verifiable, not worth a third
round, but call it out so the author tightens citation habits.
