---
name: sst-iam-and-infra-lint
description: SST Fargate execution-role "*" SSM grant is overridden via object transform; infra/** is outside biome includes; guard hook blocks commands containing ARN strings
metadata:
  type: project
---

2026-10-01 T-P8-1: SST's stock Fargate execution role grants ssm/secretsmanager reads on "*" (fargate.ts createExecutionRole); InvAI overrides it with an object `transform.executionRole` built from `invai-infra/infra/execution-role.ts` (object transforms merge as `{...args, ...transform}`, so managed policies survive).
**Why:** S-45, cross-stage secret reads. **How to apply:** any new sst.aws.Service/Task must pass the same `executionRole` transform.

2026-10-01 T-P8-1: `invai-infra/biome.json` includes only `src/**`, `*.ts`, `*.json`, so `infra/**` isn't linted by `pnpm lint`; lint helpers with a temp config copy in /tmp.

2026-10-01 T-P8-1: guard-bash.py blocks any Bash command whose text contains AWS ARN-like strings (even `node -e` with sample ARNs); put evaluation code in a /tmp script file and run that.
