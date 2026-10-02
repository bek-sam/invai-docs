# Wave P8: infra unblock (S-45 IAM scope, one-form push check, guard script-write fix)

- Status: **paused** (2026-10-01): T-P8-1 and T-P8-2 approved; T-P8-3 waits on OI-24; gate and infra push held (owner port hold + OI-24)
- Goal: `invai-infra`'s five held commits become pushable: the SST config no longer gives every ECS task read access to every stage's secrets (S-45); the push check accepts exactly one push form instead of guessing folders (OI-22); the guard stops refusing harmless commands that only create a script file (OI-23).
- Scope refs: all `always-in-scope: security` (S-45 in `security/v1-review.md`; B-115/B-189 guard gaps; T-23-6 push check, owner-approved 2026-09-29).
- Started by the owner in chat (2026-10-01), who named the three cards and answered OI-22 (A) and OI-23 (A); also: push `invai-infra`'s held commits once fixed. This overrides P7's "last wave" note and decision 0019's pause for T-24-1's S-45 fix only (config, no deploy).
- Plan review: skipped. The owner chose the cards and their limits; each is a narrow security fix with a security co-review. Recorded here as a deviation from the wave process.
- Fences: no `aws`, no `sst deploy`, no outbound. No control or test weakened. At most 2 agents at once (a mentor agent also runs; its `invai-docs/learn/**` files are not ours to commit). Gate under `caffeinate -i`.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P8-1](T-P8-1-s45-iam-scope.md) S-45: scope the ECS execution roles' SSM/Secrets Manager reads to the task's own stage (T-24-1 round 2) | platform-sre | opus | security-reviewer (fable); reviewer r1 already approved T-24-1, re-checks the new commit | security (IAM) | **approved** (infra 0741b66; security r2 approve, S-45 fixed, not deployed) |
| [T-P8-2](T-P8-2-guard-script-write.md) T-P7-4 round 3: a word after a redirect is a file, not a script to read | platform-sre | opus | security-reviewer (fable) | auth (team controls) | **approved** (docs 5add5cf, installed; security r3 approve, reviewer r1 approve) |
| [T-P8-3](T-P8-3-push-one-form.md) T-23-6 round 3: the push check allows exactly one push form | platform-sre | opus | reviewer (fable) + security-reviewer (fable) | security (hook) | built (docs d8568aa, installed; infra 1644dd4 README), reviewer r3 + security r2 running |

Order: T-P8-1 and T-P8-2 at once (2 agents). T-P8-3 starts after T-P8-2 is installed (both edit `.claude/hooks/guard-bash.py`; never two owners on one file). Reviews: one security-reviewer agent covers T-P8-1 + T-P8-2, then T-P8-3 with the reviewer.

Gate: `caffeinate -i pnpm gate invai-infra` (infra only: typecheck + lint; no DB reset). Then push `invai-infra` with the new one form, and commit and push the docs.

## Log
- 2026-10-01 22:28 CDT OI-22 and OI-23 answered (A, A) in `owner-inbox.md`. Wave and cards written. Disk 7.1 GB free; Docker healthy.
- 2026-10-01 22:35 CDT T-P8-1 and T-P8-2 started (platform-sre, opus, 2 agents). Gate ports :3000/:8000/:5173/:5174 free. The r2 optional guard notes are already B-264.
- T-P8-1 built: infra 0741b66 (`infra/execution-role.ts`, SSM read scoped to `/invai/<stage>/*`, Secrets Manager read dropped). Security r2 started (review file `waves/24/reviews/T-24-1-security-reviewer-r2.md`). Follow-up noted: `biome.json` doesn't lint `infra/**`.
- T-P8-2 built: docs 5add5cf, installed live (112 hook tests, was 109). It keeps a shell reading a script on stdin as a run, on purpose (reviewer to judge). The guard still reads heredoc bodies as commands: my own wave-log append quoting that form was refused (known gap, B-264 family). T-P8-3 started from the installed guard.
- T-P8-1 security r2 approve (`waves/24/reviews/T-24-1-security-reviewer-r2.md`): no blocking findings; S-45 marked fixed (infra 0741b66, not deployed). Optional: biome skips `infra/**`; `ssm:GetParameterHistory` could go; confirm four execution-role updates at the owner's first `sst diff`. T-P8-2 security r3 started on the committed copy (5add5cf).
- T-P8-2 security r3 approve (`waves/P7/reviews/T-P7-4-security-reviewer-r3.md`): six write forms now allowed, write-then-run still denied, stdin-run kept (accepted). Optional notes to B-268: a leading redirect still hides a script run (allowed before and after).
- Coordinator (owner request): hold `pnpm gate`, `db:reset` and anything on :3000/:5173/:5174/:8000 until told clear (owner screenshots, 30-60 min). The infra-only gate is held; card and review work continues.
- T-P8-3 built: docs d8568aa (guard + tests, installed live), infra 1644dd4 (README). Code-repo pushes: only the bare `git -C /Users/bekbolsun/invai/<repo> push origin main|<sha>:main` plus a matching stamp; docs push must use the absolute `-C` path (a trailing `| tail` is fine). `--all`/`--branches` now denied. Tests 112 to 110 methods (cases moved into subTests). CLAUDE.md push line to update after approval (tech lead's path). Reviewer r3 and security r2 started.
- T-P8-3 security r2 changes-required (`waves/23/reviews/T-23-6-security-reviewer-r2.md`): S-42 fixed, but new S-47 (Medium): the docs-push allowance doesn't check the push's arguments, so a docs-folder push can target a code repo's remote with no stamp. Also logged S-46 (Medium, pre-existing: launcher/alias forms bypass push detection) and S-48 (Low: git config remote writes). A further round needs the owner (OI-24).
- T-P8-3 reviewer r3 escalate (`waves/23/reviews/T-23-6-reviewer-r3.md`): same blocking gap as S-47, found independently; everything else holds. Third failed round on T-23-6, so OI-24 asks the owner for a round 4 limited to that one rule. Infra push waits on OI-24 and the port hold (T-23-6 commits sit under the S-45 fix in infra history).
