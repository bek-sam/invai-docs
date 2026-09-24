# T-1-1: Backend builds, and production refuses to run on mocks

| Field | Value |
|---|---|
| Wave | 1 |
| Scope ref | always-in-scope: bug / security |
| Backlog | B-56, B-50, backend half of B-58 (mail env) |
| Owner | backend-foundation |
| Reviewer | reviewer |
| Co-reviewers | security-reviewer |
| Risk flags | auth, pii |
| Model | opus |

## Owned paths (edit)
- `invai-backend/package.json` (scripts and deps only), `invai-backend/tsup.config.*`
- `invai-backend/src/env.ts`, `invai-backend/src/api/app.ts`
- `invai-backend/src/integrations/vendors/mailer.ts` (config source only; keep the `sendMail` signature)
- `invai-backend/.env.example`, `invai-backend/README.md` (env section)
- tests next to these files

## Read-only paths
- everything else in `invai-backend`, and `invai-infra/**`

## Evidence
`build/audit-2026-09-24.md` §A-QA (tsup `--noExternal`) and §A-BE B-50.

## Acceptance criteria
1. `pnpm build` in invai-backend succeeds and produces runnable api and worker entries. `node dist/<api entry>` starts against the local stack and `/health` answers.
2. Given `NODE_ENV=production` and any of these keys missing: `EASYPOST_API_KEY`, `STRIPE_SECRET_KEY` (with `STRIPE_WEBHOOK_SECRET`), `ANTHROPIC_API_KEY`, `SHOPIFY_API_KEY` (with `SHOPIFY_API_SECRET`), `SMTP_URL`, `MAIL_FROM`. Then boot fails with one clear message that lists every missing key. The exception is `ALLOW_MOCKS=true`, meant for demo or staging stages, which boots and logs a loud warning on every start.
   - `SHOPIFY_API_KEY`/`SHOPIFY_API_SECRET` are platform app credentials (like the others above), so they belong in this list: without them `env.mocks.shopify` is silently true in production and a real shop's Shopify connection runs mocked.
   - `SS_ACTIVEWEAR_*` is deliberately **not** in this list: T-1-3 makes supplier credentials tenant-owned only, so there's no platform-wide "supplier mock" left to guard once that card lands.
3. `SMTP_URL` and `MAIL_FROM` are in the Zod env schema. The mailer reads them from `env`. The dev defaults (Mailpit on :1025) apply only outside production.
4. Public `/health` no longer returns which providers are mocked. That detail needs an authenticated admin, or stays in logs only.
5. `NODE_ENV=test` and development behave exactly as before: no new required keys locally.

## Verification
- `pnpm typecheck && pnpm lint && pnpm test && pnpm build` in invai-backend
- Run the built API. With `NODE_ENV=production` and no keys, show the refusal message. With `ALLOW_MOCKS=true`, show that it boots. Curl `/health` and show there's no `mocks` field.

## Out of scope
- AWS or SST changes (wave 10). The S&S per-tenant fallback (T-1-3).
