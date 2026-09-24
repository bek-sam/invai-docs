# Postmortem: <title>

- Incident: `invai-docs/ops/incidents/<YYYY-MM-DD>-<slug>.md` (or escaped defect: card T-<n>-<k>)
- Severity: SEV<n>. Status: draft / reviewed / actions done
- Author: <role>. Reviewers: tech-lead, <owner role of the failing path>, security-reviewer (security incidents)
- Written within 48 h of resolution: <resolved at> → <written at>

## Summary
<3–5 plain sentences a shop owner could read: what broke, for whom, for how long, what fixed it.>

## Impact
| Measure | Value |
|---|---|
| Shops affected | <count; ids in the incident file> |
| Duration (T0 → resolved) | |
| Orders delayed / labels failed / sheets wrong / scans blocked | |
| Buyer data involved | yes / no; categories and count |
| Error budget used | <SLO and % of the 28-day budget> |
| Notices sent (by the owner) | Amazon <time or n/a>, shops <time>, partners <…> |

## Timeline (all times <TZ>)
| Time | Event |
|---|---|
| | Trigger (change, traffic, provider event) |
| | Detected (how: alert, shop, agent) |
| | Owner told |
| | Contained |
| | Resolved |

## Contributing causes (blameless)
Ask "what let this happen?" until you reach conditions we can change. Name systems, checks, docs and defaults, never people or agents.
1. <cause> — evidence: <file:line, log line, query>
2. …

## Detection and response
- How long until we knew? Why not sooner?
- What made diagnosis slow or fast (logs, traces, queries)?
- What went well?
- Where did we get lucky?

## Action items
| # | Action | Type (prevent / detect / mitigate / process) | Owner role | Card or backlog id | Due |
|---|---|---|---|---|---|

## Lessons
- Rows added to `team/lessons.md`: <dates and rules>
- Findings added to `security/v1-review.md`: <S-ids>
- Decisions recorded: <NNNN>
