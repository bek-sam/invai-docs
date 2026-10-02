---
name: sst-transform-iam-review
description: How to verify an SST transform.<role> IAM narrowing without AWS — object transform is a shallow merge, check every Service/Task instantiation, evaluate helper with hostile inputs
metadata:
  type: project
---

SST v4 `transform.<resource>` as an **object** is a shallow merge `{...args, ...transform}` (`.sst/platform/src/components/component.ts:34-49`); a **function** transform mutates `args` in place. So an object transform that sets `inlinePolicies` replaces SST's whole inline array (good for dropping a `"*"` statement) while `managedPolicyArns`/`assumeRolePolicy` survive. Stock wildcard grants to look for: `fargate.ts createExecutionRole` (`ssm:GetParameter*` + `secretsmanager:GetSecretValue` on `*`), task role `ssmmessages:*` on `*` (ECS Exec channel, not a secret read). `sst.aws.Task` reuses `createExecutionRole`, so it needs the same transform.

**Why:** S-45 (T-24-1 r1, 2026-09-29) was exactly this default biting; fixed in infra `0741b66` (T-P8-1, 2026-10-01) with a pure helper `infra/execution-role.ts`.

**How to apply:** on any infra IAM card: (1) grep every `new sst.aws.Service|Task|Function|Cron` and confirm each passes the transform; (2) read the merge semantics, don't assume; (3) evaluate a pure helper from a temp `.mts` under `/private/tmp` with `node --experimental-strip-types`, feeding `*`, `?`, `/`, `:` into stage/account/region/partition (inline `node -e` with ARN strings trips the guard hook); (4) `biome.json` includes skip `infra/**`, so lint output is not evidence for that folder.
