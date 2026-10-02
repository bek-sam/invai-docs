# Review of T-24-1 (round 2, finding S-45 only; card T-P8-1; `invai-infra` `0741b66` only, `3dbb899` was r1; read-only, no `aws`/`sst` run)

- Reviewer: security-reviewer on Fable 5.1
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-infra`: `pnpm typecheck` / `pnpm lint` (Node v24.21.0) | both exit 0 (`tsc --noEmit` silent; biome "Checked 4 files … No fixes applied") |
| `git show 0741b66 --stat` / `git diff --stat 490884d..0741b66` | `README.md` +6, `infra/execution-role.ts` +49 (new), `sst.config.ts` +28/-2; working tree clean |
| Read `.sst/platform/src/components/component.ts:34-49` (`transform()`) | an object transform is a shallow merge `{...args, ...transform}`: our `inlinePolicies` replaces SST's whole inline array; `assumeRolePolicy` and `managedPolicyArns` (AmazonECSTaskExecutionRolePolicy: ECR pull, logs) are untouched |
| Read `fargate.ts:1009-1066` (`createExecutionRole`) and `task.ts:336` | the `"*"` grant for `ssm:GetParameter*` + `secretsmanager:GetSecretValue` lives only in that inline policy; `sst.aws.Task` (Migrate) uses the same `createExecutionRole`, so the same transform applies |
| Read `fargate.ts:945-1000` (task role) | only `ssmmessages:*` on `*` (ECS Exec channel, not a parameter/secret read) plus the card-scoped `permissions` (KMS on one key ARN); no wildcard secret read on the task role |
| `grep -n "new sst.aws.Service\|new sst.aws.Task\|Function\|Cron" sst.config.ts` | exactly four compute resources (`Imaging`:324, `Api`:388, `Worker`:436, `Migrate`:455); all four pass `transform.executionRole` (one shared const, `sst.config.ts:305-320`) |
| `grep -n '"\*"' sst.config.ts infra/*` | 3 hits: `:180` S3 CORS `allowHeaders` (not IAM); `:300` and `execution-role.ts:5` are comments |
| `grep -n "secretsmanager\|environmentFiles\|keyId" sst.config.ts infra/*` | no Secrets Manager use, no `environmentFiles`, SSM params use the default `alias/aws/ssm` key (`toSsm()` `:234-241`, names `/invai/${stage}/${name}`), so dropping `secretsmanager:GetSecretValue` and SST's optional `ReadEnvironmentFiles` statement loses nothing |
| Local evaluation of the helper (temp `.mts` under `/private/tmp`, Node strip-types, deleted after) | `staging`/`production`/`demo`/`pr-123` each yield one statement on exactly `arn:aws:ssm:us-east-1:123456789012:parameter/invai/<stage>/*`, no `"*"`, no `secretsmanager`; refused: stage `*`, `prod/*`, `""`, `a?b`, `../production`, `x/*/y`; account `*` and 11 digits; region `*`, `us-east-1:*`; partition `*`, `aws:*`. Simulated SST merge: managed policy and assume-role kept, stock star statement gone |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | region = `aws.getRegionOutput().region`, account = `getCallerIdentityOutput().accountId`, partition = `getPartitionOutput().partition`, stage = `$app.stage` (`sst.config.ts:32,35,310-313`); helper rejects any `*`/`?`/`/`/`:` in every field, so no stage or account value can widen the ARN beyond one stage |
| 2 | yes | `secretsmanager:GetSecretValue` removed; grep confirms Secrets Manager is unused |
| 3 | yes | managed `AmazonECSTaskExecutionRolePolicy` kept by shallow merge; task role unchanged and had no wildcard secret read |
| 4 | yes | one `executionRole` const built from `infra/execution-role.ts`, shared by all four |
| 5 | yes | diff adds only the transform key on each resource (Migrate gains a `transform` block); no other T-24-1 setting changed |

## Blocking findings
none

## Checks
- [x] Only owned paths changed (`sst.config.ts`, `infra/**`, `README.md`)
- [x] Nothing outside scope (`.claude/**` untouched)
- [x] Tests exercise the behavior, none weakened: no test suite exists in infra; the helper was evaluated locally with hostile inputs (above)
- [x] Tenancy/PII: closes the cross-stage read path to production `MIGRATION_DATABASE_URL` (S-45); no code-path change for tenants. Decisions recorded (object vs function transform, in the report; infra-local)

## Optional notes (not blocking)
1. `biome.json` `includes` skip `infra/**` (`biome check infra/execution-role.ts` → "ignored"), so the helper is unlinted (author's follow-up); `ssm:GetParameterHistory` is not needed by ECS secret injection and could be dropped later.
2. Proof is by source reading and local evaluation only (nothing deployed). The first `sst diff` with the owner's credentials should show four `ExecutionRole` inline-policy changes and nothing else: S-45 stays "fixed, not deployed" until then.
