# T-P8-1: S-45, scope the ECS execution roles' secret reads to the task's own stage (T-24-1 round 2)

| Field | Value |
|---|---|
| Wave | P8 |
| Scope ref | `always-in-scope: security` (S-45, Medium, `invai-docs/security/v1-review.md:56`) |
| Owner | platform-sre |
| Reviewer | security-reviewer (fable) for round 2; the `reviewer` approved T-24-1 r1 and re-checks the new commit |
| Risk flags | security (IAM) |
| Model | opus |

## Read first
- `.claude/agents/platform-sre.md`; card `invai-docs/waves/24/T-24-1.md`; finding S-45 (`security/v1-review.md:56`); review `waves/24/reviews/T-24-1-security-reviewer-r1.md`.
- Installed SST source: `invai-infra/.sst/platform/src/components/aws/fargate.ts` (~L1040-1050, the default execution role policy) and the `transform.executionRole` type in the same component. Don't guess the API.

## Owned paths (edit)
- `invai-infra/sst.config.ts`, `invai-infra/infra/**` (if you split a helper out), `invai-infra/README.md` (a line on the IAM scope)

## Read-only
- Every other path. `.claude/hooks/**` is being edited by T-P8-2/T-P8-3 at the same time: don't touch it.

## Acceptance criteria
1. `Api`, `Worker`, `Imaging` and `Migrate` each set `transform.executionRole` so the execution role's `ssm:GetParameters`/`ssm:GetParameter`/`ssm:GetParameterHistory` resources are exactly `arn:aws:ssm:<region>:<accountId>:parameter/invai/<stage>/*` (region, account and stage from SST/Pulumi values, never hard-coded). No `"*"` resource is left on any statement that reads SSM or Secrets Manager.
2. `secretsmanager:GetSecretValue` is removed if no Secrets Manager secret is used (grep the config and say so), or scoped the same way.
3. Other execution-role permissions SST needs (ECR pull, logs) still work: keep the stock statements, only narrow the secret-read ones. The task role is unchanged unless it also had a wildcard secret read (check and say).
4. A single shared helper builds the policy so the four services can't drift.
5. No other behavior of T-24-1 changes.

## Verification
- `cd invai-infra && pnpm typecheck 2>&1 | tail -n 20 && pnpm lint 2>&1 | tail -n 20` exit 0.
- Show the resulting policy JSON without AWS: either a small local evaluation of your helper with sample region/account/stage (via `node`/`tsx` against the helper only), or quote the code path and the `fargate.ts` lines it overrides. `aws`, `sst deploy`, `sst diff` against a real account are forbidden (guarded); `sst` commands that need credentials are out.
- `grep -n '"\*"' sst.config.ts infra/** 2>/dev/null` and explain every remaining hit.

## Commit
- One commit in `invai-infra` on `main`, only your paths (`git -C /Users/bekbolsun/invai/invai-infra add <paths>`), message ends with the attribution line. Don't push; only the tech lead pushes after the gate.

## Out of scope
- Any other T-24-1 item, the KMS key's use, deploy steps, `.claude/**`.

## Report
- `invai-docs/waves/P8/reports/T-P8-1.md`, `verify-and-report` format, at most 60 lines. Record every PID you start (there should be none).
