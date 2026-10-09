# 0029: The seeded demo shop follows the real two-step sign-in rule

- Status: accepted (2026-10-09)
- Type: product

## Context
Decision 0025 requires two-step sign-in for owners and admins of real shops and excludes sample workspaces. Wave 28 wrote the exclusion as `companies.demo = true`, but the codebase's test for a sample workspace is `isSampleRow` (`demoOwnerUserId` or `settings.demoRetiredAt`, `modules/tenancy/demo-flag.ts`). The seeded Desert Bloom has `demo = true` and is not a sample workspace, so its owner and admin were never asked for two-step sign-in. That is the login the owner uses to test the feature. Links: backlog B-299, card T-29-2, wave 28 retro. Decided by product-manager.

## Decision
1. Exempt from the two-step rule = a sample workspace by `isSampleRow`, nothing else. `companies.demo` alone never exempts.
2. The seeded Desert Bloom follows the real rule. `owner@` and `admin@` see the banner during the 7-day grace and get `MFA_REQUIRED` after it. Office, designer, presser, packer, receiver and vendor logins stay unaffected.
3. No seed bypass and no environment switch to turn the rule off for the seeded shop. A dev DB older than 7 days is fixed by enrolling the seeded owner or by `db:reset` + seed (fresh grace). The runbook and demo guide say so (docs-writer).
4. Fresh-seed test suites and the golden path must not need the seeded owner to be enrolled (the deadline is 7 days out).

## Consequences
- The owner sees the real behavior on the demo shop; sample workspaces (try-it-first) stay frictionless.
- A stale local DB blocks `owner@` after 7 days until enrolled or reset: a known, documented cost.
- T-29-2 switches `src/lib/mfa.ts` to `isSampleRow`; decision 0028 records the technical side and links this one.
