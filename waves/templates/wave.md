# Wave <n>: <goal in one line>

- Dates: <start> → <end>
- Goal (user outcome): <for example "a pilot shop runs a real day of orders">
- Plan reviewed by: product-manager (<date, verdict>), architect (<date, verdict>)

## Cards
| Card | Owner | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|
| T-<n>-1 | | reviewer + | | planned |

## Agreed interfaces (stubs committed first)
- `<function or procedure>`: provider <role>, consumers <roles>

## Integration gate
- [ ] Fresh reset, migrate, seed
- [ ] `run-golden-path` passes (API, browser, floor)
- [ ] Key screens looked at by the tech lead
- [ ] Pushed to `main` (commits: …)

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|

## Retro
- What slipped:
- Lessons added (links to `team/lessons.md`):
