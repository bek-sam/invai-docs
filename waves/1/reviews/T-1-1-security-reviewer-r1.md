# Review of T-1-1 (round 1)

- Reviewer: security-reviewer on Opus 5.5 (Sonnet 5 session)
- Author: backend-foundation on Opus 5.5
- Verdict: changes-required

## Evidence I re-ran
Same clean-worktree setup as the primary reviewer (commit `34ed022` only, via `git worktree add /tmp/review-t11-backend 34ed022`, so the other cards' uncommitted WIP in the shared tree is excluded). Own test DB `invai_test_r11`, dropped after use. Threat-modeled per `threat-model-change`: entry points are process boot (api, worker, any prod script) and the public, unauthenticated `/health` route.

| Command | Result |
|---|---|
| `./node_modules/.bin/tsc --noEmit`, `vitest run`, `tsup` | all pass/succeed (see reviewer's file for full output) |
| `NODE_ENV=production` boot, no keys | refuses, one `Error:` line listing all 8 `PRODUCTION_KEYS` — matches the card's "one clear message that lists every missing key" |
| `NODE_ENV=production ALLOW_MOCKS=true` boot, port 3191 | boots; `console.error` warn line lists all 8 missing key **names** only, never values; `curl -s http://localhost:3191/health` → `{"ok":true,"db":true,"redis":true,"imaging":false,"s3":true,"version":"dev"}` — confirmed no `mocks` field, no key names, no secret material |
| `grep -iE "secret|password|api_key|token"` over both captured startup logs | only matches the literal key **names** inside the `missing` array (`EASYPOST_API_KEY`, `STRIPE_SECRET_KEY`, …) — no values, no secrets |
| Whitespace-value probe (all 7 non-URL `PRODUCTION_KEYS` set to `" "`, `SMTP_URL` set to a valid URL) | **boots in production with zero output** — no refusal, no `ALLOW_MOCKS` warning, `env.mocks.*` reports `false` for every affected provider |
| `ALLOW_MOCKS` loose-value probe (`True`, `TRUE`, `1`, `yes`, `" true"`, `"true "`, `"false "`) | all rejected by the Zod `z.enum(["true","false"])` — process exits 1 with a schema validation error before the guard even runs. Confirmed **not** exploitable: there is no loose/case-insensitive coercion of `ALLOW_MOCKS`. |
| `SMTP_URL=" "` (whitespace) alone | rejected — `z.url()` format validation fails and the whole process crashes at env-load (fail-closed, not a bypass; different failure mode than the intended message, but not an issue) |
| Dockerfile / build-output cross-check | `dist/server.js`, `dist/index.js` — exact match to `Dockerfile`'s `COPY --from=build /build/invai-backend/dist ./dist` and `CMD ["node","dist/server.js"]`. Nothing the Dockerfile expects is missing from the build output. |

## Threat model summary
- **Entry point 1: process boot** (api `server.ts`, worker `index.ts`, any script importing `env.ts`). Not session-scoped; the "caller" is whoever controls the deploy environment. Worst outcome of a bypassed guard: a real shop's orders/PII flow through a provider (Stripe, Shopify, Anthropic) that is either mocked or holds a non-functional credential, without the operator being warned. Control: `missingProductionKeys()` + throw, unless `ALLOW_MOCKS=true` (which itself requires an exact, loudly-logged opt-in).
- **Entry point 2: `GET /health`**, public, unauthenticated. Before this change it returned `env.mocks`, i.e. which providers are mocked — reconnaissance value for an external attacker (knows which integrations are faked, e.g. that Stripe billing is unenforced). After this change the route returns only dependency booleans (`db`, `redis`, `imaging`, `s3`) — verified via `health.test.ts` (exact key-set assertion, `not.toMatch(/mock/i)`) and my own curl. This closes the intended information-disclosure gap. No PII, no secret material, no mock-status is exposed publicly.
- **Data touched:** none directly (no PII fields, no new tables). The mailer change touches `MAIL_FROM`/`SMTP_URL` (config, not PII) and logs only `subject`, never `to` or body, on the "mail NOT sent" path.
- **No new `withSystem` usage, no new tables, no RLS surface, no new webhook or auth code** in this diff — tenancy and auth controls are unaffected by this card's scope.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | Build output matches Dockerfile expectations exactly; built API boots and answers `/health`. |
| 2 | **No** (blocking) | Guard correctly refuses on literal-missing keys and correctly boots-with-warning on `ALLOW_MOCKS=true`. It is silently defeated by a whitespace-only value on 7 of the 8 keys — see finding below. |
| 3 | Yes | `SMTP_URL`/`MAIL_FROM` in the Zod schema; dev defaults to Mailpit only outside production. |
| 4 | Yes | `/health` returns no `mocks` field; confirmed both by test and by my own curl in all three boot modes (prod-no-keys refused before serving, prod+ALLOW_MOCKS, dev). |
| 5 | Yes | Dev and `NODE_ENV=test` need no keys; full suite green with none set. |

## Blocking findings
1. `invai-backend/src/env.ts:50-64, 94-96` — the production key guard treats any non-empty string as "present," including whitespace-only values, for `ANTHROPIC_API_KEY`, `EASYPOST_API_KEY`, `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, and `MAIL_FROM`. Failure scenario: a deploy pipeline or secrets-manager integration renders an unset secret as `" "` instead of `""` (this happens with several common templating/interpolation setups, and with some Kubernetes `envFrom`/default-value patterns). Production then boots **with no refusal and no `ALLOW_MOCKS` warning whatsoever** — the loudest signal the card designs for (a thrown error, or at minimum a warn log naming every missing key) never fires. `env.mocks.shopify`/`.billing`/`.ai`/`.carrier` all read `false`, so the code believes it holds real credentials. This is the same class of harm the card is written to close (S&S/Shopify/Stripe/Anthropic silently running without a working key in production) reached through a different door than the one already closed (empty string). Severity: **Low** on the security-reviewer scale (no cross-tenant access, no auth bypass, no PII leak — it is a config/operator-error hardening gap, not an externally exploitable one, since only someone with control over the production environment can set it). Still blocking under `independent-review`'s broader rule ("security" is a blocking category regardless of severity tier), and it sits squarely inside AC2's stated intent. Fix: trim before the presence check, e.g. `PRODUCTION_KEYS.filter((key) => !values[key]?.trim())`, or add `.trim()` to each `z.string().optional()` field.
   - Not filed as a numbered finding in `invai-docs/security/v1-review.md` yet — recommend the owner add it there (id, Low, area "env/config") once the round-1 fix lands, so it's tracked even though it's fixed at the source rather than accepted as a risk.

## Checks
- [x] Only owned paths changed
- [x] Nothing outside scope
- [x] Tests exercise the behavior, and none were weakened — scan script hits all traced to other cards' uncommitted files, not this commit; both new test files fail against pre-commit code
- [x] Tenancy — n/a, no `company_id` tables or RLS touched by this diff
- [x] No PII in logs — verified: mailer logs `subject` only on the unsent-mail path (pre-existing `to`/`subject`/`messageId` logging on the sent path is unchanged by this commit); startup/guard logs list only env-var **names**, never values
- [x] Decisions recorded where needed — the report's rationale for guarding at `env.ts` load time (so worker and scripts refuse too, not just the api) is sound and matches "fail closed by default" practice

## Optional notes (not blocking)
- `SMTP_URL` is protected from the whitespace gap by its own `z.url()` format check (a whitespace string fails URL parsing and crashes the whole process at env-load) — only the plain `z.string().optional()` fields are exposed. Worth folding into the same trim fix for consistency rather than relying on two different failure modes.
- `ALLOW_MOCKS` parsing was a specific concern raised for this review and is **not** a problem: the strict `z.enum(["true","false"])` rejects every loose/cased variant I tried (`True`, `TRUE`, `1`, `yes`, leading/trailing space) with a hard crash, never a silent pass-through.
