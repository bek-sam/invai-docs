# Review of T-1-1 (round 2)

- Reviewer: security-reviewer on Opus 5.5 (Sonnet 5 session)
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Same clean-worktree setup at `293047b` as the primary reviewer, own test DB `invai_test_r11`, dropped after use. Focus: re-threat-model and re-prove the round-1 finding is actually closed, not just narrowed.

| Command | Result |
|---|---|
| `tsc --noEmit`, `vitest run` (35 files / 187 tests), `tsup` build | all pass/succeed |
| **Whitespace bypass, re-probed exactly as round 1**: all 7 non-URL `PRODUCTION_KEYS` = `" "`, `SMTP_URL` real | Refused, all 7 listed by name, exit 1 — the guard fires correctly now |
| `SMTP_URL` = whitespace alone (round 1's secondary gap — this used to crash the process with an unformatted Zod error instead of the intended message) | Now produces the same clear `Refusing to start in production: missing SMTP_URL. …` message. Closed as a side effect of routing `SMTP_URL` through the same `secret()` preprocessor before the `z.url()` check runs. |
| All 8 keys whitespace + `ALLOW_MOCKS=true` | Boots, warn line names all 8, `env.mocks.*` all `true` (correctly recognized as absent-and-mocked, not "false" the way round 1 wrongly reported) |
| `curl /health` in every boot mode above | Still `{"ok":true,"db":true,"redis":true,"imaging":false,"s3":true,"version":"dev"}` — no `mocks` field, unaffected by this diff (round-1 fix, not re-touched) |
| Padded-real-value probe (leading/trailing spaces on every key) | Boots; values come out trimmed (`"smtp":"smtp://mail:25"` not `" smtp://mail:25 "`); `mocks` all `false` — confirms consumers (mailer, integrations) now receive clean values, not just that the guard sees them |
| Log capture from every boot above, grepped for `secret\|password\|api_key\|token` | Only key **names** appear (in the `missing` array and in test-only literals I passed as fixture values like `real-stripe_secret_key`, which are my own synthetic values, not real secrets) — no leakage introduced by this change |
| `git diff --stat 34ed022 293047b` | `src/env.ts` (33 lines), `src/env.test.ts` (35 lines) only — within `src/env.ts`, explicitly the security-relevant owned path |

## Threat model re-check
- **Entry point (unchanged from round 1): process boot.** The round-1 gap meant a *config-rendering artifact* (a secret manager or template emitting `" "` instead of `""` for an unset value) could put production into a state where it silently believed it held real Stripe/EasyPost/Anthropic/Shopify/SMTP credentials, with **no warning at all** — worse than the `ALLOW_MOCKS=true` path, which at least logs loudly. That gap is closed: the `secret()` preprocessor (`z.preprocess((v) => typeof v === "string" ? v.trim() || undefined : v, schema.optional())`) is applied uniformly to all eight `PRODUCTION_KEYS` fields plus `SS_ACTIVEWEAR_ACCOUNT`/`SS_ACTIVEWEAR_API_KEY`, so there is now exactly one place blank-vs-present is decided, and every consumer (the guard, `env.mocks.*`, the mailer, future integrations reading `env.*`) reads the same post-trim value — no way for one code path to see "present" and another to see "absent" for the same raw input.
- **`missingProductionKeys()` also trims independently** (`!values[key]?.trim()`) — reasonable defense in depth for the exported pure function, in case it's ever called with untrimmed input from somewhere other than `raw`.
- No new entry points, no tenancy/auth/PII surface touched by this diff. `/health`'s public shape is unchanged from round 1 (still no `mocks` field) — re-confirmed, not regressed.
- No new logging of secret values anywhere in the diff; the `missing` array logs key names only, as before.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 2 | **Yes** (was the round-1 block) | Whitespace-only values across all guarded keys, including `SMTP_URL`, are now correctly treated as missing, with the exact clear-message behavior AC2 requires, and no bypass path found in re-testing. |
| 1, 3, 4, 5 | Yes, re-confirmed not regressed | Build, mail defaults, `/health` shape, dev/test-without-keys all still correct. |

## Blocking findings
None. Round 1's Low-severity finding (`invai-backend/src/env.ts:50-64,94-96`, whitespace bypassing the production key guard) is closed: reproduced the exact failing scenario from round 1 against `293047b` and it now refuses correctly, with the fix applied consistently (trim-and-treat-blank-as-unset) rather than special-cased to just the keys I'd tested.

## Checks
- [x] Only owned paths changed (`src/env.ts`, `src/env.test.ts`)
- [x] Nothing outside scope
- [x] Tests exercise the behavior, none weakened — 3 new tests all fail against pre-fix (`34ed022`) code when run in isolation; the one changed assertion in `env.test.ts` is additive only (accommodates a newly-printed field), the values it checks are unchanged
- [x] No PII/secrets in logs — re-confirmed, key names only
- [x] Tenancy — n/a, no `company_id`/RLS surface in this diff
- [x] Decisions recorded — round-2 report section is clear on what changed and why; no new risk accepted, nothing needs a `v1-review.md` entry since the gap is fixed rather than accepted

## Optional notes (not blocking)
- Worth a light follow-up (not blocking, not this card): `missingProductionKeys()`'s own trim is currently redundant with `secret()`'s trim for every real caller (`raw` is always pre-trimmed by the schema), so it's pure defense in depth rather than closing a live gap — fine to leave as is, flagging only so a future refactor doesn't mistake it for dead code.
