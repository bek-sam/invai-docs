# Review of T-<wave>-<k> (round <1 or 2>)

- Reviewer: <role> on <model>
- Author: <role> on <model>
- Verdict: approve / changes-required / escalate

## Evidence I re-ran
| Command | Result |
|---|---|
| | |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|

## Blocking findings
1. <file:line> — <what is wrong, and a concrete failure scenario>

## Checks
- [ ] Only owned paths changed (`git diff --stat`)
- [ ] Nothing outside scope
- [ ] Tests exercise the behavior, and none were weakened (no `.skip`, loosened assertions, mocks of the unit under test, rewritten snapshots)
- [ ] Tenancy (`withTenant`, RLS on new tables), idempotency, money in cents, en/es text
- [ ] Decisions recorded where needed

## Optional notes (not blocking)
