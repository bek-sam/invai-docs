# Review of T-17-1 (round 1)

- Reviewer: reviewer on claude-sonnet-5
- Author: architect on claude-opus-5.5 (Sonnet 5 per card)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show 8713a63 --stat` | 4 files changed: `CHANGELOG.md`, `package.json`, `src/compat.ts`, `src/schemas/ai.ts` — all inside owned paths |
| `git -C invai-contracts status --short` | clean, nothing uncommitted |
| `pnpm typecheck` (invai-contracts) | `$ tsc --noEmit` — clean |
| `pnpm lint` (invai-contracts) | `Checked 49 files in 36ms. No fixes applied.` |
| `pnpm test` (invai-contracts) | `Test Files 5 passed (5)`, `Tests 36 passed (36)` |
| `pnpm typecheck` (invai-backend, linked via existing `node_modules/@invai/contracts -> ../../../invai-contracts`) | `$ tsc --noEmit` — clean |
| `pnpm typecheck` (invai-web, same symlink) | `$ tsc --noEmit` — clean |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-contracts HEAD~1` | `Result: no hits` (no skips, no removed assertions, no loosened config) |
| `grep -n "0.x" invai-contracts/README.md` | `A breaking change here is a breaking change everywhere. Bump the minor version on 0.x` — confirms the report's cited semver rule is real |
| `grep -n "assistant.tool\." invai-web/src/routes/_app/assistant.tsx` | line 86: `t(\`assistant.tool.${ev.name}\`, ev.name.replace(/_/g, " "))` — confirms the graceful-fallback claim (no exhaustive switch to break) |
| `sed -n '1165,1190p' invai-backend/src/modules/ai/service.ts` | confirms the stale workaround comment/guard for `get_production_status` still exists at the reported line, outside this card's owned paths |
| `git -C invai-backend status --short`, `git -C invai-web status --short` | both show unrelated in-progress edits from sibling wave-17 cards (T-17-2/3/4), not touched by this commit — confirmed out of scope for T-17-1 |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1. `tool_call.name` accepts all ten names | Yes | `src/schemas/ai.ts` diff adds the five new values at the end of the existing five; `pnpm test` round-trips all in `schemas.test.ts` |
| 2. Minor vs patch decided and recorded | Yes | `CHANGELOG.md` 0.5.0 entry states the decision and reasoning; matches the repo's own README rule (verified above) and standard semver (additive enum = feature, not fix) |
| 3. Backend and web still typecheck | Yes | both `pnpm typecheck` clean, re-run independently |
| 4. Remove backend workaround comment only if in owned paths, else note for T-17-3 | Yes | comment confirmed still present at `invai-backend/src/modules/ai/service.ts:1176-1177`, correctly out of this card's read-only-only scope; flagged for T-17-3 in the report's "Blocked by other owners" |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat` shows only `CHANGELOG.md`, `package.json`, `src/compat.ts`, `src/schemas/ai.ts` in invai-contracts)
- [x] Nothing outside scope (backend/web untouched by this commit; the enum addition is purely additive)
- [x] Tests exercise the behavior, and none were weakened (scan script: no hits; `compat.test.ts` still asserts `CONTRACT_VERSION === package.json` version and `FLOOR_COMPAT_BASELINE <= CONTRACT_VERSION`)
- [x] Tenancy / idempotency / money / en-es — n/a, this card is a schema-only enum addition with no request path, tenancy, money or i18n surface
- [x] Decisions recorded where needed — version-bump reasoning recorded in `CHANGELOG.md`; not cross-cutting enough for a new ADR (ordinary additive-enum case already covered by `add-contract-procedure`), agreed

## Optional notes (not blocking)
- The new enum values carry an inline comment explaining why `get_production_status` is listed first among the new entries; this is helpful and worth keeping as the pattern for future additive enum PRs.
- `FLOOR_COMPAT_BASELINE` correctly stays untouched since `AssistantEvent` has no floor consumer (decision 0012's additive-change rule applies: new enum values the floor never sends need no compat window).
