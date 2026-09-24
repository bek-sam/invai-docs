# Report: T-1-1 Backend builds, and production refuses to run on mocks
Author: backend-foundation on Opus 5.5

```
Card: T-1-1  Owner: backend-foundation  Scope ref: always-in-scope: bug / security (B-56, B-50, B-58 backend half)
Owned (edit): invai-backend/{package.json (scripts), tsup.config.*, src/env.ts, src/api/app.ts,
  src/integrations/vendors/mailer.ts (config source), .env.example, README.md (env section)} + tests next to them
Read-only: rest of invai-backend, invai-infra/**
Risk flags → co-reviewers: auth, pii → security-reviewer
```

Commit (invai-backend, `main`, **not pushed**): `34ed022` "Backend builds again; production refuses to run on mock providers (T-1-1)"

## Built
- `pnpm build` works again: the tsup 8.5 CLI rejects `--noExternal`, so the options moved into `tsup.config.ts`. Named entries keep the paths the Dockerfile, compose `full` and SST already use: `dist/server.js` (api) and `dist/index.js` (worker). `@invai/contracts` (TS source) is bundled; every other dep stays external in `node_modules`. (files: invai-backend/tsup.config.ts, invai-backend/package.json)
- Production key guard in `src/env.ts`: with `NODE_ENV=production`, loading env throws one error that lists every missing key in `PRODUCTION_KEYS` = `EASYPOST_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, SMTP_URL, MAIL_FROM`. Because the guard runs when env loads, the api, the worker and any prod script all refuse. `ALLOW_MOCKS=true` boots anyway and writes a JSON `warn` line with the missing keys on every start. The new exports are `env.allowMocks`, `env.mocks.mail`, `PRODUCTION_KEYS` and `missingProductionKeys()`. `SS_ACTIVEWEAR_*` is not in the list, as the card says. (file: src/env.ts)
- `STRIPE_WEBHOOK_SECRET`, `SMTP_URL`, `MAIL_FROM` and `ALLOW_MOCKS` are now in the Zod schema. `env.SMTP_URL`/`env.MAIL_FROM` default to Mailpit (`smtp://localhost:1025`, `InvAI <sheets@invai.local>`) only outside production.
- The mailer reads `env.SMTP_URL`/`env.MAIL_FROM`, and the `sendMail` signature is unchanged. In production without SMTP, which is only possible with ALLOW_MOCKS, it uses nodemailer `jsonTransport` and logs `mail NOT sent`, so nothing goes out and nothing hangs on a missing Mailpit. (file: src/integrations/vendors/mailer.ts)
- Public `/health` no longer returns `mocks`. The mock flags stay only in the existing startup log line in `server.ts`. (file: src/api/app.ts)
- Docs: `.env.example` has the new keys and the production rule. The README has a new "Production build and required keys" section.
- Tests: `src/env.test.ts` (7 tests, 5 of them load `src/env.ts` in a fresh child process the way boot does) and `src/api/health.test.ts`.

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `pnpm build` → `dist/server.js`, `dist/index.js`. `node dist/server.js` (dev, port 3110) → `/health` 200 and owner sign-in 200. `node dist/index.js` (isolated DB and Redis) → "outbox relay started", "worker started" with all 18 jobs, jobs ran |
| 2 | Yes | `NODE_ENV=production node dist/server.js` → exit 1, `Error: Refusing to start in production: missing EASYPOST_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, SMTP_URL, MAIL_FROM. …`. With `ALLOW_MOCKS=true` → boots, warn line, `/health` 200. The one-key-missing case is covered by env.test.ts |
| 3 | Yes | Zod schema has SMTP_URL/MAIL_FROM. Dev `sendMail` → Mailpit got 1 message from `InvAI <sheets@invai.local>`. Prod+ALLOW_MOCKS → `mail NOT sent` warning, 0 Mailpit hits |
| 4 | Yes | `/health` body is `{"ok":true,"db":true,"redis":true,"imaging":false,"s3":true,"version":"dev"}`. health.test.ts asserts the exact key set and no "mock" substring |
| 5 | Yes | Full test suite (NODE_ENV=test) passes with no provider keys. Dev boot needs no new keys (env.test.ts "development needs no provider keys" + real dev boot of dist/server.js) |

## Checks I ran
All run in invai-backend with `TEST_DATABASE_URL`/`TEST_MIGRATION_DATABASE_URL` pointing at `invai_test_t11`.

| Repo | Command | Result (last lines) |
|---|---|---|
| invai-backend | `pnpm typecheck` | `tsc --noEmit`, exit 0 |
| invai-backend | `pnpm lint` | `Checked 187 files in 80ms. No fixes applied.` (before other cards' WIP landed; see gaps) |
| invai-backend | `pnpm test` | `Test Files 32 passed (32)`, `Tests 156 passed (156)` |
| invai-backend | `pnpm build` | `dist/server.js 66.77 KB`, `dist/index.js 3.45 KB`, `⚡️ Build success` |
| invai-backend | `pnpm exec biome check <my 9 files>` (after commit prep) | `Checked 7 files … No fixes applied.` |

## Exercised for real
- `NODE_ENV=production PORT=3110 node dist/server.js` (with the .env infra vars and no provider keys) → exit=1. The only error is the single "Refusing to start in production: missing …" message listing all 8 keys.
- `NODE_ENV=production ALLOW_MOCKS=true PORT=3110 node dist/server.js` → the log shows `{"level":"warn","scope":"env","msg":"ALLOW_MOCKS=true: running production on MOCK providers. Not for real shops.","missing":[…8 keys]}` and then `invai api listening on :3110`. `curl /health` → `HTTP/1.1 200`, `{"ok":true,"db":true,"redis":true,"imaging":false,"s3":true,"version":"dev"}`, with no `mocks` field.
- `PORT=3110 node dist/server.js` (development, .env) → `/health` 200 with no mocks, `POST /api/auth/sign-in/email` as owner@desertbloom.test → 200.
- `node dist/index.js` with `DATABASE_URL`/`MIGRATION_DATABASE_URL` = `invai_test_t11` and `REDIS_URL=redis://localhost:6379/11`, so it couldn't take shared jobs or outbox rows → the relay and workers started and processed jobs. It was stopped after 4 s and Redis db 11 was flushed.
- Mailer in dev → Mailpit search shows 1 message, From `InvAI <sheets@invai.local>`. In prod+ALLOW_MOCKS → `mail NOT sent: SMTP_URL is not set (ALLOW_MOCKS)` and 0 Mailpit hits.
- Refused case: production without keys → boot refused (above). No permissioned procedure was added.

## Decisions
- **The guard lives in `env.ts`, at load time, not in `server.ts`.** That way the api, the worker and any production script all refuse; the worker would otherwise push mock tracking too. Side effect: a production `db:migrate` also needs the keys, or ALLOW_MOCKS. Local tooling isn't affected.
- **The error is thrown, not `process.exit`.** The message is on the `Error:` line and the pure part (`missingProductionKeys`) is unit-testable. The boot behavior is tested in child processes.
- **`/health` drops the mock flags entirely** instead of adding an admin variant. The card allows "logs only", and `server.ts` already logs `mocks` at startup. Nothing in web or floor read `health.mocks` (grep).
- **`env.mocks.mail` was added** (true when `SMTP_URL` is unset; in dev that means Mailpit), so the startup log shows mail too. This is additive, and no consumer iterates `mocks`.
- `env.mocks.billing` still keys off `STRIPE_SECRET_KEY` only. The webhook secret is required in prod by the guard, but mock or live selection is T-1-3's area.
- New tests are in new files (`env.test.ts`, `api/health.test.ts`) rather than `api/app.test.ts`, to avoid colliding with T-1-4 if it touches that file.

## Known gaps and follow-ups
- **Infra doesn't pass the new required keys yet (cross-card, platform-sre / wave 10).** `invai-infra/sst.config.ts` defines no secrets for `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SMTP_URL` or `MAIL_FROM`, and it defaults Anthropic, EasyPost and Shopify to `""`. A real SST deploy will now refuse to boot until those secrets are added, or until `ALLOW_MOCKS=true` is set for a demo stage. This is intended, but the deploy card must know about it. The same applies to compose `full`, which runs `NODE_ENV=production` if it sets that.
- The runbook (`invai-docs/build/runbook.md` line ~72, owned by docs-writer or the tech lead) still lists `env.mocks.{ai,carrier,shopify,supplier,billing}` and doesn't mention `ALLOW_MOCKS`, `SMTP_URL`, `MAIL_FROM` or `STRIPE_WEBHOOK_SECRET`. It needs a docs update.
- `src/modules/README.md` needs no change: the mock-selection pattern is unchanged.
- `SS_ACTIVEWEAR_*` isn't guarded, by design, because T-1-3 removes the platform-wide supplier fallback. If T-1-3 slips, `env.mocks.supplier` stays a silent prod mock (architect's note).
- **`pnpm lint` in invai-backend is currently red because of other cards' uncommitted WIP, not T-1-1:** `src/db/schema/webhooks.ts:1` (organizeImports, T-1-2) and `src/modules/tenancy/service.ts:241` (unused variable, formatting; T-1-4). My files check clean.
- The E2E golden path wasn't run: this card changes no golden-path behavior in dev or test. The integration gate covers it.

## Blocked by other owners
- none

## Processes and data
- Stopped: the built API on 3110 (3 runs, all killed; port free) and the built worker (killed after 4 s). Redis db 11 flushed.
- Shared dev DB: untouched apart from reads by `/health` and one owner sign-in, which created a session. Test DB used: `invai_test_t11` (created by the test run). One test mail is left in Mailpit (subject "T-1-1 mailer env check").

## Round 2

Commit (invai-backend, `main`, **not pushed**, a new commit, not an amend): **`293047b`** "Production key guard: blank or whitespace-only keys count as missing (T-1-1 r2)". It touches only `src/env.ts` and `src/env.test.ts`.

### Finding addressed
Both reviews found the same bug: a whitespace-only value (`" "`) counted as present for 7 of the 8 `PRODUCTION_KEYS` (`src/env.ts:50-64, 94-96`). The guard passed, and `env.mocks.*` read false.

### Fix
- In `src/env.ts`, a new `secret(schema)` helper, `z.preprocess(v => typeof v === "string" ? v.trim() || undefined : v, schema.optional())`, wraps every provider key: `ANTHROPIC_API_KEY`, `EASYPOST_API_KEY`, `SHOPIFY_API_KEY/SECRET`, `SS_ACTIVEWEAR_ACCOUNT/API_KEY`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, plus `SMTP_URL` (still `z.url()`) and `MAIL_FROM`. Values are trimmed and blank counts as unset, all in one place. So the guard, every `env.mocks.*` flag and every consumer apply the same rule, and consumers receive trimmed keys.
- `missingProductionKeys()` also trims its input (`!values[key]?.trim()`), as defense in depth for the exported pure function.
- Side benefit (the security-reviewer's optional note): a whitespace-only `SMTP_URL` now gets the clear "missing SMTP_URL" refusal instead of a Zod URL crash.

### New tests (`src/env.test.ts`, 3 added, 1 assertion narrowed)
- `counts blank or whitespace-only values as missing`: the pure function, with `"  "` and `"\t\n "`.
- `refuses to boot when keys are whitespace-only, and ALLOW_MOCKS then runs them as mocks`: a child-process boot. With every key set to `"  "`, boot is refused and all 8 keys are listed. With `ALLOW_MOCKS=true`, the process boots and `mocks` is all true.
- `trims real values instead of treating padding as part of the key`: padded values boot, come out trimmed (`"smtp":"smtp://mail:25"`), and `ai:false`.
- The child boot now also prints `env.mocks`. Because of that, the existing ALLOW_MOCKS test's substring check changed from `'{"smtp":null,"from":null}'` to `'{"smtp":null,"from":null,'`. What it asserts is the same (smtp and from are null); only the closing brace moved.

### Checks
These ran in a clean worktree at HEAD plus my two files, so other cards' uncommitted work was excluded. The binaries were called directly because pnpm refuses a symlinked node_modules. The test DB was `invai_test_t11`.

| Command | Result |
|---|---|
| `tsc --noEmit` | exit 0 |
| `biome check .` | `Checked 186 files in 90ms. No fixes applied.` |
| `vitest run` | `Test Files 32 passed (32)`, `Tests 159 passed (159)` (156 before, +3) |
| `tsup` (`pnpm build`) | `⚡️ Build success` |

### Exercised for real: the reviewers' exact probe against the built `dist/server.js`
- `EASYPOST_API_KEY=" " STRIPE_SECRET_KEY=" " STRIPE_WEBHOOK_SECRET=" " ANTHROPIC_API_KEY=" " SHOPIFY_API_KEY=" " SHOPIFY_API_SECRET=" " MAIL_FROM=" " SMTP_URL="smtp://x:1" NODE_ENV=production` gives exit=1 and `Error: Refusing to start in production: missing EASYPOST_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, MAIL_FROM. …`. In round 1 this booted silently.
- The same values with `ALLOW_MOCKS=true` boot. The warn line lists those 7 keys, the startup log shows `"mocks":{"ai":true,"carrier":true,"shopify":true,"supplier":true,"billing":true,"mail":false}` (mail is false because SMTP_URL was real), and `/health` returns `{"ok":true,"db":true,"redis":true,"imaging":false,"s3":true,"version":"dev"}`.
- `SMTP_URL="  "` alone gets the clear refusal listing all 8 keys, where round 1 crashed with a Zod error.

### Process note
My first attempt at this commit (`7e2422d`, never pushed, now unreferenced) swept in a staged deletion of `src/db/seed/trademarks.ts`. That deletion belongs to another agent, likely T-1-5, and was sitting in the shared index. I undid only my own commit with `git reset --soft HEAD~1`, which kept T-1-2's `90657ac` and left their staged deletion exactly as it was. I then re-committed with an explicit pathspec (`git commit -- src/env.ts src/env.test.ts`). The deletion is still staged, uncommitted, for its owner. Lesson worth logging: in a shared working tree, commit with a pathspec, because `git add <paths>` alone doesn't protect against other agents' staged changes.

### Processes and data
The built API on 3110 was stopped (port free), and the temporary worktree `/tmp/t11-r2` was removed. The shared dev DB was only read by `/health`.
