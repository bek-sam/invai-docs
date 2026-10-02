# Wave P8 — infra unblock: S-45 IAM scope, one-form push check, guard script-write fix

**Dates:** 2026-10-01.

## What was built
- **T-P8-1** S-45: scope the ECS execution roles' SSM/Secrets Manager reads to the task's
  own stage (platform-sre) — round 2 of T-24-1; before this fix, every ECS task in
  `invai-infra`'s SST config could read *every stage's* secrets, not just its own.
- **T-P8-2** T-P7-4 round 3: a word after a redirect is a file, not a script to read
  (platform-sre) — a narrow guard-hook fix so the guard stops misreading shell redirect
  targets as scripts it needs to inspect.
- **T-P8-3** T-23-6 round 3: the push check allows exactly one push form instead of
  guessing which folder's push command it's looking at (platform-sre).

## Why
This small, three-card wave exists for one reason: `invai-infra` had **five held
commits** that couldn't be pushed because of exactly these three gaps — a real IAM
over-scoping finding (S-45), and two guard-hook issues (OI-22, OI-23) that had each
already failed two prior review rounds. Unblocking infra matters because until it's
pushed, dispatch-only E2E workflows in CI can't find the scripts they depend on.

## What went wrong
- Each of these three fixes was itself a **third review round** on a problem the team had
  already tried to fix twice — S-45 was round 2 of T-24-1, T-P8-2 was round 3 of T-P7-4,
  and T-P8-3 was round 3 of T-23-6. This wave is a good data point on how long a genuinely
  tricky security/infra finding can take to close properly: not every fix lands clean on
  the first or even second attempt, and the project's review process is built to keep
  sending a card back rather than approve a partial fix.

## What the team learned
- A security or guard-hook finding that survives two review rounds isn't a sign the
  process is broken — holding firm through round 3 (rather than approving "good enough")
  is what the independent-review system is supposed to do when the underlying issue is
  genuinely subtle (an IAM policy that looks locked-down but still over-reaches by stage,
  a guard that correctly blocks dangerous input but also catches a legitimate case).
- Infra commits sitting unpushed for multiple waves (S-45's chain traces back through
  wave 23b's handoff notes) is a real cost — not of the fix being wrong, but of the
  review cycle taking three rounds to converge — worth factoring into how a wave plans
  time for security-flagged infra cards.

## Files to look at
- `invai-infra/.sst/platform/src/components/aws/*.ts` (or the SST stack config for ECS
  task roles) — the IAM scope fix (T-P8-1).
- `invai-docs/team/hooks/guard-bash.py` — the redirect-target fix (T-P8-2) and the
  one-push-form fix (T-P8-3).
- `invai-docs/owner-inbox.md` (OI-22, OI-23) — the two escalations this wave finally closes.
- `invai-docs/waves/23b/wave.md` — the original handoff that first flagged these as holds.
