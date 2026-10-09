# T-<wave>-<k>: <title>

| Field | Value |
|---|---|
| Wave | <n> |
| Scope ref | `product/scope.md#<anchor>`, or `always-in-scope: bug / security / incident / compliance` |
| Spec | `specs/<slug>.md` |
| Owner | <role> (area: <module, if backend-engineer>) |
| Reviewer | <`reviewer` for code; for other authors, see "Who reviews whom" in team/operating-system.md> |
| Co-reviewers | <from the risk flags; see team/operating-system.md> |
| Risk flags | tenancy, pii, auth, payments, webhooks, files, migration, marketplace-policy, ai, floor-correctness, ui |
| Model | <fable, opus or sonnet> |

## Owned paths (edit)
- `<repo>/<path>/**`

## Read-only paths
- `<repo>/<path>/**`

## Depends on
- <card or interface>

## Interfaces promised
- `<name>(args) -> result`

## Acceptance criteria
1. Given …, when …, then …
2. Edge cases: …

## Verification
- `pnpm typecheck && pnpm lint && pnpm test` in: <repos>
- Exercise for real: <curl script, role to sign in as, expected result, screenshots>
- E2E: <suites, if a golden-path area>
- New table without `company_id`: `src/db/rls-coverage.test.ts` (`GLOBAL_TABLES`, security-reviewer's file) fails until the table is listed; grant that one line on the card or plan it with the security co-review (lesson 2026-10-09)
- Scratch DB or seed work: pin `REDIS_URL` to the card's own Valkey DB and `SEED_OUTPUT_FILE` to `/tmp/...` before any `db:reset`, migrate or seed (lessons 2026-09-29 T-23-9, 2026-10-01 P5; fix B-219)

## Out of scope
- …

## Budget
- Escalate to the tech lead if blocked for more than about 30 minutes of work, or if the card turns out bigger than planned.
