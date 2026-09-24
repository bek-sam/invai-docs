# Review of T-1-1 (round 1)

- Reviewer: reviewer on Opus 5.5 (Sonnet 5 session)
- Author: backend-foundation on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
All commands run against commit `34ed022` in a clean `git worktree` (`/tmp/review-t11-backend`, node_modules symlinked from `invai-backend`), so other cards' uncommitted WIP in the shared working tree never entered the result. Own test DB: `invai_test_r11` (`postgres://invai_app:invai@localhost:5432/invai_test_r11` / `postgres://invai:invai@localhost:5432/invai_test_r11`), created and dropped by me.

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit` (worktree at 34ed022) | exit 0, no errors |
| `./node_modules/.bin/biome check` on this commit's 7 lintable files | `Checked 7 files in 44ms. No fixes applied.` |
| `./node_modules/.bin/vitest run` (TEST_DATABASE_URL=…r11) | `Test Files 32 passed (32)`, `Tests 156 passed (156)` |
| `./node_modules/.bin/tsup` (`pnpm build` equivalent) | `dist/server.js 66.77 KB`, `dist/index.js 3.45 KB`, `⚡️ Build success` |
| `NODE_ENV=production PORT=3191 node dist/server.js`, no keys | exit 1, `Error: Refusing to start in production: missing EASYPOST_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, SMTP_URL, MAIL_FROM. …` |
| `NODE_ENV=production ALLOW_MOCKS=true PORT=3191 node dist/server.js` | boots; warn log lists all 8 missing keys; `curl /health` → 200, `{"ok":true,"db":true,"redis":true,"imaging":false,"s3":true,"version":"dev"}` — no `mocks` field |
| `PORT=3191 node dist/server.js` (dev, no keys) | boots normally, `/health` 200, same clean body |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 29afd65` | hits reported, all traced to other cards' uncommitted files (`etsy/index.ts`, `suppliers/index.ts`, `webhooks.test.ts`, `invites.test.ts`) — none in this commit's diff. Only in-scope hit: `expect(...).toBeTruthy()` in the new `env.test.ts`, on a wholly new file — not a weakening. |
| New tests run against pre-commit base (`git archive 29afd65`) | `env.test.ts` throws (`PRODUCTION_KEYS` undefined), `health.test.ts` fails (`mocks` key present) — both new tests correctly fail without the change |
| Whitespace-value bypass probe: `EASYPOST_API_KEY=" " STRIPE_SECRET_KEY=" " STRIPE_WEBHOOK_SECRET=" " ANTHROPIC_API_KEY=" " SHOPIFY_API_KEY=" " SHOPIFY_API_SECRET=" " MAIL_FROM=" " SMTP_URL="smtp://x:1" NODE_ENV=production` | **Boots with no warning at all**; `mocks:{ai:false,carrier:false,shopify:false,billing:false,mail:false}` — the guard is fully defeated |
| `ALLOW_MOCKS` loose-value probe (`True`, `TRUE`, `1`, `yes`, `" true"`, `"true "`, `"false "`) | all fail closed with a Zod parse error (exit 1) — **not** a bypass, the enum is strict |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `pnpm build`-equivalent succeeds, `dist/server.js`/`dist/index.js` match `Dockerfile`'s `COPY --from=build .../dist` and `CMD ["node","dist/server.js"]`. Built API's `/health` answers 200 against the local stack. |
| 2 | **No** (see blocking finding) | The literal "key missing" case is correctly refused and lists all 8 keys, and `ALLOW_MOCKS=true` correctly boots-with-warning. But a whitespace-only value for any of `EASYPOST_API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `ANTHROPIC_API_KEY`, `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `MAIL_FROM` is accepted as "present": production boots silently, with no refusal and no `ALLOW_MOCKS` warning, and `env.mocks.*` reports `false` for providers that have no usable credential. |
| 3 | Yes | `SMTP_URL`/`MAIL_FROM` in the Zod schema, mailer reads from `env`, Mailpit default only outside production (`env.test.ts` "development needs no provider keys and defaults mail to Mailpit"). |
| 4 | Yes | `/health` body key set is exactly `db, imaging, ok, redis, s3, version` — no `mocks`. `health.test.ts` asserts the exact key set and no `/mock/i` substring anywhere in the body. |
| 5 | Yes | `NODE_ENV=test` and dev both boot and pass with zero provider keys set; `pnpm test` is green under `invai_test_r11` with no keys in the environment. |

## Blocking findings
1. `invai-backend/src/env.ts:50-64` (the `ANTHROPIC_API_KEY`/`EASYPOST_API_KEY`/`SHOPIFY_API_KEY`/`SHOPIFY_API_SECRET`/`STRIPE_SECRET_KEY`/`STRIPE_WEBHOOK_SECRET`/`MAIL_FROM` fields) and `src/env.ts:94-96` (`missingProductionKeys`) — a whitespace-only value (e.g. `" "`) for any of these keys is not caught. `emptyStringAsUndefined: true` only normalizes the exact empty string; `z.string().optional()` accepts `" "` as a valid, present value, and `!raw.KEY` is `false` for a non-empty string, so `missingProductionKeys` doesn't list it. Failure scenario: an operator's secrets-manager template renders an unset secret as a single space instead of an empty string (common with some templating engines and Kubernetes `envFrom` defaults) — production boots with **no refusal and no `ALLOW_MOCKS` warning at all**, `env.mocks.shopify`/`.billing`/`.ai`/`.carrier` report `false` (not mocked), and the app proceeds to call Stripe/EasyPost/Anthropic/Shopify with a garbage key. This is exactly the "provider silently runs on its mock in production" failure the card exists to prevent, just inverted (it silently runs on a broken real credential with no loud warning at boot, instead of failing fast with the clear message AC2 requires). Fix: `.trim()` the values before the presence check (e.g. `z.string().trim().min(1).optional()` or trim inside `missingProductionKeys`).

## Checks
- [x] Only owned paths changed (`git diff --stat 29afd65 34ed022`: `.env.example`, `README.md`, `package.json`, `src/api/app.ts`, `src/api/health.test.ts`, `src/env.test.ts`, `src/env.ts`, `src/integrations/vendors/mailer.ts`, `tsup.config.ts` — all within the card's owned paths and "tests next to these files")
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened (`env.test.ts`, `health.test.ts` are wholly new files; both fail against pre-commit code; scan script's other hits belong to other cards' uncommitted files, not this commit)
- [x] Tenancy — n/a (no tenant tables/RLS touched); money/i18n — n/a (no money or user-facing strings changed)
- [x] Decisions recorded where needed — none required beyond the report's stated decisions, which are reasonable (guard at `env.ts` load time so api/worker/scripts all refuse; error thrown not `process.exit`; `/health` drops `mocks` entirely)

## Optional notes (not blocking)
- The report's "known gaps" section already flags that `invai-infra` doesn't yet pass the new required secrets — correctly called out as a follow-up for the platform-sre/deploy card, not this one.
- `log.warn("mail NOT sent: SMTP_URL is not set (ALLOW_MOCKS)", { subject: mail.subject })` (`mailer.ts`) logs the mail subject but not the recipient or body — reasonable, no PII leak found in any log line I captured (grepped for `secret|password|api_key|token`: only key *names* appear, never values).
