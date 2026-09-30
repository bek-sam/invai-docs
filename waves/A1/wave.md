# Wave A1: analytics v2, the data and read services (B-168..B-172)

- Dates: not started. Runs next, before waves 24/25 (paused until the owner starts AWS, decision 0019) and before the rest of 23b (T-23-3, T-23-4), as the PM ranks them.
- Goal (user outcome): a shop owner can get, from InvAI's API, true unit economics, losing orders, leakage, shipping margin, operations waits and inventory health on 18 months of realistic seed history. Screens come in A2.
- Spec: `specs/business-analytics-v2.md` (Tracks A–C). Scope check: `waves/analytics-scope-check.md` (PM, 2026-09-28: fits scope items 5–8, 13, 14, 17).
- Plan reviewed by: not yet (PM for scope, architect for design).

## Cards (proposed; to be carded by the A1 tech lead)
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-A1 Analytics-ready seed (B-168, absorbs B-130) | backend-foundation (+ qa-engineer tests) | sonnet | reviewer (opus) | golden path | planned |
| T-A2 `analytics.*` contract (B-169) | architect | fable | reviewer (opus) | contract | planned |
| T-A3 Finance analytics service + `fixed_monthly_cents` migration (B-170) | backend-engineer (finance) | opus | reviewer (opus) + backend-foundation (migration), security-reviewer (tenancy) | tenancy, migration, money | planned |
| T-A4 Operations and shipping analytics + `shipments.dest_zone` (B-171) | backend-engineer (production, shipping) | opus | reviewer (opus) + backend-foundation (migration), security-reviewer (tenancy, pii) | tenancy, migration, pii | planned |
| T-A5 Inventory and design analytics (B-172) | backend-engineer (inventory) | sonnet | reviewer (opus) | tenancy | planned |

Co-reviewers follow decision 0019; data-analyst checks definitions at the gate, not as a co-reviewer.

## Handoff from wave 23b (2026-09-30, tech lead)
- **State:** everything from wave 23 and 23b step 1 is pushed after a full `pnpm gate` pass (`invai-infra/.gate/run-20260930T045101Z.log`): contracts `7ee15b6`, ui `952c174`, backend `61c6396`, web `eb1e86b`, floor `7900d0a`, imaging `58b67ee`. The dev DB is freshly seeded by that gate (now with a digest and market demand data).
- **Held, don't push:** infra `3dbb899` (T-24-1, needs S-45), `b62ad92`/`3215fc6` (T-23-6, OI-22), `9fe0c55`/`490884d` (T-23-7, sit on top). Don't touch T-23-6 until OI-22 is answered. The push hook needs a fresh `pnpm gate` stamp on the exact SHAs you push; run pushes as plain `git -C /abs/repo push origin main` (no redirect, loop or `cd`: the hook refuses them).
- **Before carding:** the spec is still `draft`. The PM must log the product-designer, qa-engineer and customer-success reviews in it and set it `ready` (`waves/analytics-scope-check.md` lines 53–57). No card starts before that.
- **Sequence:** T-A2 contract first (architect commits the procedure stubs and names), with T-A1 seed in parallel (it has no contract dependency). Then T-A3, T-A4, T-A5. At most 3 agents at once, reviewers included.
- **Ownership conflicts to fix in the cards:**
  - T-A3, T-A4 and T-A5 all write under the new `src/modules/analytics/**`. Give each an exact file set (for example `finance*.ts`, `operations*.ts`, `inventory*.ts`), and have T-A3 own the router and shared helpers with a stub committed first.
  - T-A3 and T-A4 both add migrations. Run them one after the other, or the later one regenerates the drizzle journal (`CLAUDE.md`).
  - T-A1 and any seed work share `src/db/seed/**`. Only one seed card may be open at a time.
- **T-A1 must keep:** golden-path counts and Today queues unchanged, and the T-23-8 digest and T-23-10 market-demand seed steps. The seed already takes 15–20 minutes, so budget its runtime and say what 18 months adds.
- **Fences:** B-178..B-181 (Track D) stay out; OI-18 is not approved. No buyer PII in analytics: T-A4 stores the zone number only (AC-A4). OI-17 is not approved either.
- **Owed from 23b:** look at the floor screens at 1280×800 in en and es (T-23-2) at the A1 gate. No one has looked at them yet.
- **Environment traps (in `team/agent-brief.md`):** pin `REDIS_URL` to your own DB on every backend command, `db:reset` included (B-219). The web dev CSP allows only API :3000 (B-220). The market tests leak cache rows between files (B-221, Medium): if the gate's backend suite fails in `src/modules/market`, that's the cause. Card B-221 early.
- **Unknown processes, leave alone:** :3142 (PID 98947), vite :5183 (PID 73962), PIDs 11838 and 72215.
- **Owner:** OI-20 (disk; 13 GB free on 2026-09-30), OI-21 (CI read token), OI-22 (T-23-6 round 3). OI-17 and OI-18 are not approved.

## Integration gate
- [ ] `pnpm gate` passes on a fresh seed, with the SHAs stamped
- [ ] Key screens looked at, including the owed floor screens at 1280×800 in en and es
- [ ] Pushed to `main`

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
