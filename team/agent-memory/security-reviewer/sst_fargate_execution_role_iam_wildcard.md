---
name: sst-fargate-execution-role-iam-wildcard
description: SST v4 Fargate execution roles get resources:["*"] for ssm:GetParameter*/secretsmanager:GetSecretValue by default; check transform.executionRole on every infra review that adds SSM secrets
metadata:
  type: project
---

`.sst/platform/src/components/aws/fargate.ts` `createExecutionRole()` grants every `sst.aws.Service`/`sst.aws.Task`
execution role `ssm:GetParameters`, `ssm:GetParameter`, `ssm:GetParameterHistory` and
`secretsmanager:GetSecretValue` on `resources: ["*"]`, unconditionally — not scoped to the task's own `ssm` prop
keys or its own stage. Found in T-24-1 (2026-09-29, S-45, Medium): moving secrets from `link` (plaintext
`SST_RESOURCE_*` env) to SSM SecureString is the right fix for plaintext-in-task-definition exposure, but without
`transform.executionRole` narrowing `resources` to `arn:aws:ssm:${region}:${account}:parameter/invai/${stage}/*`,
every task in every stage sharing the AWS account (including `demo`/`staging`) can read every other stage's
secrets, including `production`'s owner-role `MIGRATION_DATABASE_URL` — a compromise path to full RLS-bypassing
DB access, i.e. cross-tenant PII exposure, gated behind an initial task compromise.

**Why:** this is an SST-version-specific default (research 11 §7.1 "SST defaults bite"), not something obvious
from `sst.config.ts` alone — you have to read the installed component source under `.sst/platform/src/components`
to see it, same as `imaging.url` throwing for a no-public-port service (T-24-1 primary review).

**How to apply:** on any infra review that adds or changes `ssm:` props on an `sst.aws.Service`/`sst.aws.Task`
(or any Fargate compute resource), grep `.sst/platform/src/components/aws/fargate.ts` for `createExecutionRole`
and check whether `transform.executionRole` scopes the SSM/Secrets Manager grant down to that stage's own
parameter path. If not, that's a real, reproducible finding (cite the fargate.ts line numbers as proof; no AWS
credentials needed). Also check whether SecureString params set a customer `keyId` — if not, the default
`alias/aws/ssm` key means `ssm:GetParameter` alone decrypts, no extra KMS gate.
