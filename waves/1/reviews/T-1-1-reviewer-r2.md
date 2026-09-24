# Review of T-1-1 (round 2)

- Reviewer: reviewer on Opus 5.5 (Sonnet 5 session)
- Author: backend-foundation on Opus 5.5
- Verdict: approve

## Evidence I re-ran
Round 1's blocking finding: a whitespace-only value (`" "`) passed the production guard for 7 of 8 `PRODUCTION_KEYS`. Commit `293047b` claims to fix it. Re-verified against a clean `git worktree` at `293047b` (`/tmp/review-t11-r2`, node_modules symlinked), so nothing from other cards' history or uncommitted WIP entered the result. Own test DB `invai_test_r11`, dropped after use.

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` (worktree at 293047b) | exit 0 |
| `./node_modules/.bin/biome check src/env.ts src/env.test.ts` (only this commit's 2 files) | `Checked 2 files in 55ms. No fixes applied.` |
| `./node_modules/.bin/vitest run` (full suite, TEST_DATABASE_URL=…r11) | `Test Files 35 passed (35)`, `Tests 187 passed (187)` (this worktree's history also includes T-1-2's already-merged webhook work, hence more than the 159 the author reports for their isolated diff — no failures either way) |
| `./node_modules/.bin/tsup` | `dist/server.js 67.01 KB`, `dist/index.js 3.45 KB`, `⚡️ Build success` |
| **Round-1 whitespace probe, re-run verbatim**: `NODE_ENV=production EASYPOST_API_KEY=" " STRIPE_SECRET_KEY=" " STRIPE_WEBHOOK_SECRET=" " ANTHROPIC_API_KEY=" " SHOPIFY_API_KEY=" " SHOPIFY_API_SECRET=" " MAIL_FROM=" " SMTP_URL="smtp://x:1"` | **Fixed.** exit 1, `Error: Refusing to start in production: missing EASYPOST_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, MAIL_FROM. …` — round 1 booted silently here |
| `SMTP_URL="   "` alone (whitespace), all other keys real | Now gets the clean `missing SMTP_URL` refusal (round 1 crashed with a raw Zod URL-format error) |
| All 8 keys `" "` + `ALLOW_MOCKS=true` | Boots; warn line lists all 8; `mocks:{ai:true,carrier:true,shopify:true,supplier:true,billing:true,mail:true}`; `/health` → 200, no `mocks` field |
| Padded real values (`" real-anthropic "` etc., `SMTP_URL=" smtp://mail:25 "`) | Boots; `mocks` all `false` (correctly recognized as real, trimmed) |
| `NODE_ENV=production`, no keys at all | Still refuses, all 8 keys listed |
| Dev mode, no keys | Still boots clean, `/health` unaffected |
| `ALLOW_MOCKS` loose-value sanity (`True`, `1`, `yes`) | Still fail closed (Zod enum rejects, exit 1) — unaffected by this diff, as expected |
| `git diff --stat 34ed022 293047b` | Only `src/env.ts` (33 lines) and `src/env.test.ts` (35 lines) — matches the card's owned paths exactly, and matches the author's stated scope |
| New/changed tests run against pre-fix code (`git archive 34ed022` + the new `env.test.ts`) | The 3 new tests fail on the unfixed code (2 with wrong-error/no-refusal, 1 with untrimmed padding in the boot output); the pre-existing narrowed assertion (`'{"smtp":null,"from":null}'` → `'{"smtp":null,"from":null,'`) is not a weakening — it only accommodates the newly-printed `mocks` field appended after it, the checked values (`smtp`/`from` both null) are identical |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 2 (the one round 1 blocked on) | **Yes** | Whitespace-only values on any `PRODUCTION_KEYS` entry are now trimmed and treated as unset by a single `secret()` helper (`z.preprocess` trim-or-undefined) applied uniformly to every provider key, `SMTP_URL` and `MAIL_FROM`. The guard, `missingProductionKeys()` (defense in depth, also trims), `env.mocks.*`, and every consumer of these env values now see the same trimmed-or-absent value. Verified live with the exact round-1 reproduction. |
| 1, 3, 4, 5 | Yes (unaffected by this diff, re-confirmed not regressed) | Build still succeeds with matching dist entries; mail/health/dev/test behavior all re-verified clean above. |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat 34ed022 293047b`: `src/env.ts`, `src/env.test.ts` only — both explicitly owned by the card)
- [x] Nothing outside scope — the commit does exactly what it says: fixes the round-1 finding, nothing more
- [x] Tests exercise the behavior, and none were weakened — 3 new tests, all provably fail pre-fix; the one changed assertion is additive (extra field), not loosened
- [x] Tenancy / idempotency / money / i18n — n/a, no such surfaces touched
- [x] Decisions recorded — the report's round-2 section explains the `secret()` helper, the defense-in-depth trim in `missingProductionKeys`, and the process note about a shared-worktree staged-deletion mishap (correctly resolved with `git commit -- <paths>`, not `git add -A`)

## Optional notes (not blocking)
- The author's process note (accidentally almost committing another agent's staged deletion of `src/db/seed/trademarks.ts`, caught and unwound cleanly with `git reset --soft` + pathspec commit) is a good catch and a fair lesson to log; it did not affect this commit's contents, which I verified touches only the two files above.
