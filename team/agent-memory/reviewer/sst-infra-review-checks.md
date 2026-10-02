---
name: sst-infra-review-checks
description: How to verify an SST/Pulumi infra config card without deploying (T-24-1 style, no-AWS-credentials cards)
metadata:
  type: feedback
---

When reviewing an `invai-infra/sst.config.ts` card under the "no `sst deploy`/no `aws`" hard fence:

- Verify component APIs against `invai-infra/.sst/platform/src/components/aws/*.ts` (the installed SST
  version's real source), not docs. A `Service`'s `.url` getter throws `VisibleError` when no `loadBalancer`
  is set — that's the real bug behind "imaging reachable by an internal URL"; confirm by reading the getter,
  not by trusting the report's line-number citation blindly (re-read it yourself).
- `pnpm typecheck` passing is strong evidence for correctness of Pulumi resource-argument shapes (object
  literals get excess-property-checked against the real `.d.ts`), even for deeply nested types like WAFv2 rule
  statements — but spot-check anything you can't fully explain: I found this provider version types
  `notStatement` as `{ statements: [...] }` (a plural array), unlike raw Terraform's singular `statement`; grep
  `node_modules/@pulumi/aws/types/input.d.ts` for the exact interface name to confirm rather than assuming a
  mismatch.
- Re-run the offline-only checks: `tsc --noEmit`, `biome check .`, and an `esbuild --bundle` of `sst.config.ts`
  (via `.sst/platform/node_modules/.bin/esbuild`) to prove cross-repo imports (e.g. importing another repo's
  `csp.ts` helpers for a shared CloudFront CSP) actually resolve — this is the card's own substitute for
  `sst diff` when there are no AWS credentials.
- Cross-check the secrets list against `invai-backend/src/env.ts`'s `PRODUCTION_KEYS` export directly (grep for
  the array), not the report's paraphrase — count that every key is either an `sst.Secret` or an explicitly
  derived plain env value (e.g. `MAIL_FROM` built from the domain).
- New build-time validation functions (e.g. a CSP `uploadOrigin()` that rejects wildcards) with no new unit
  test are not automatically blocking if the grant is scoped to the implementation file only (not its test
  file) and the author exercised it live with the adversarial cases — but exercise it yourself too
  (`node --experimental-strip-types -e 'import(...)...'` works for quick real execution of a `.ts` helper
  module) rather than trusting the report's transcript.
