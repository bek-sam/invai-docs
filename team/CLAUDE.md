# InvAI workspace — team handbook for every agent

InvAI is one platform for DTF t-shirt shops that sell on Etsy, Amazon, Shopify, TikTok Shop and Walmart: marketplace orders → order-labeled gang sheets → scan-checked production floor → labels and tracking → true profit, plus AI listings with a trademark check.

v1 was built on Sep 23–24, 2026 and passes its end-to-end golden path. You are extending a working product, not starting one: read what exists before changing it.

## Read first (in this order)
1. `invai-docs/team/operating-system.md`: the owner's rules, the 20 roles and what each owns, the wave process, who reviews whom, and when to escalate.
2. Your task card in `invai-docs/waves/<n>/`, your role file in `.claude/agents/`, and the playbooks (skills) it preloads.
3. `invai-docs/product/scope.md` (what's in and out) and `invai-docs/decisions/` (accepted decisions). Don't reopen a decision without new evidence.
4. `invai-docs/build/architecture-as-built.md` (how the system really works) and `invai-docs/build/runbook.md` (setup, env vars, mock → real switches). The backlog is `invai-docs/waves/backlog.md`.
5. The research rulebooks for your area: `invai-docs/research/10-marketplace-engineering-rules.md`, `11-platform-scale-playbook.md`, `12-security-quality-playbook.md`.
6. The README of each repo you touch.

## The owner's rules (non-negotiable)
1. The tech lead plans and decides; it doesn't write feature code.
2. Every task has an owner, the files it owns and a definition of done (a task card).
3. Nothing is pushed without passing tests **and** an independent review by a different agent.
4. Decisions go in `invai-docs/decisions/`.
5. Waves have at most 5 tasks, with 3–4 agents at once, and a review before the next wave.
6. Scope lives in `invai-docs/product/scope.md`, owned by the PM. Nothing outside it gets built.
7. Tenant tables have `company_id` and RLS.
8. Webhooks, payments, labels, tracking pushes and scans are idempotent.
9. Heavy work goes to the job queue.

Anything outbound, irreversible, costly or risky goes to `invai-docs/owner-inbox.md` first. A guard hook (`.claude/hooks/guard-bash.py`) blocks force-pushes, tag pushes, deploys, `aws` commands and secret changes. It also asks the owner before any MCP tool that sends or publishes.

**Start Claude from this `invai/` folder.** The team (agents, skills, hook) loads only there. Started inside one repo, none of it applies.

## Environment (macOS, this machine)
Start every shell command that uses node or pnpm with:
```
export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"
```
That gives Node 24 and pnpm 12.6. The system `/usr/local/bin/node` is Node 22 and must not be used.

- **Docker** runs through OrbStack. If `docker` commands or local ports hang, run `orb stop && orb start`, then `cd invai-infra/local && docker compose up -d`. Data volumes survive.
- **Local services** (`invai-infra/local`, compose project `local`):
  - Postgres 17 with pgvector on :5432 (owner `invai`/`invai`, app role `invai_app`/`invai`, test DB `invai_test`)
  - Valkey on :6379
  - MinIO on :9000 (`invai`/`invai-secret`, bucket `invai-local`). The image comes from `quay.io/minio/minio`, because Docker Hub's `minio/minio` is gone.
  - Mailpit: SMTP on :1025, UI on :8025
- **Everything at once:** `cd invai-infra && pnpm dev:all` (infra, migrate, seed, then api, worker, imaging, web and floor with prefixed logs).
- **Ports:** api 3000, imaging 8000, web 5173, floor 5174. When several agents run the API at the same time, each uses its own port (`PORT=31xx pnpm dev:api`). Port 54322 belongs to another project; leave it alone.
- **Python:** `uv` (imaging: `uv sync --all-groups`, `uv run pytest`, `uv run ruff check .`).
- **Demo data:** `cd invai-backend && pnpm db:reset && pnpm db:migrate && pnpm db:seed`. Imaging must be running for the seed to render real art.
  - Logins: `owner@desertbloom.test` / `demo1234!` (also `admin@`, `office@`, `designer@`, `presser@`, `packer@` and `receiver@desertbloom.test`, plus `vendor@suncitydtf.test`).
  - PINs 1111–1188. The station token is in `invai-backend/seed-output.json`.
- **No real API keys exist.** Every integration has a mock provider, chosen automatically when its key is missing, so the platform works end to end locally. Never remove a mock.

## Repos, branches, ownership
- 8 separate git repos side by side (not a monorepo). **All work happens on `main`:** no feature branches, no pull requests, no merging or pulling steps.
- **Pushing (the owner's standing rule, `decisions/0004`):** push straight to `main` with `git push origin main`, but only after the definition of done passes **and** the review approves it. When several agents work in a wave, owners commit their own paths and the tech lead pushes after the integration gate. An agent working alone pushes only after its review passes.
- Never force-push, never rewrite pushed history, never change remotes. Commit only your own paths (`git add <paths>`, never `git add -A` in a shared repo). End messages with the attribution line in your instructions.
- Work only in the paths your task card assigns (owned paths per role are in `team/operating-system.md`). If something outside blocks you, work around it locally and report it; don't silently edit another owner's files.
- Change order for a feature: `invai-contracts` → `invai-backend` → `invai-web` / `invai-floor`. A breaking contract change must be fixed in every consumer the same day.
- **Migrations:** edit your module's schema file, then `pnpm db:generate --name <module>_<change>` and commit the migration at once. If two agents collide on the drizzle journal, the later one regenerates. Never hand-edit an applied migration.
- **Shared dev database:** don't `db:reset` it while other agents are running. Tests use `invai_test` through `src/test/fixtures.ts`.

## Conventions
- TypeScript strict, ESM, Zod v4, oRPC contract-first, Biome, Vitest, Playwright for E2E.
- Money is integer cents in USD; percents are `*Pct` numbers (6.5); ratios are 0..1; sizes are inches (numeric, never rounded). API timestamps are ISO strings; the DB uses `timestamptz`. IDs are UUIDs.
- **One order item = one physical unit.** Quantity 3 becomes 3 items, each with its own state, transfer and scan.
- **Multi-tenancy:** every tenant table has `company_id` and an RLS policy. Request code uses `withTenant(companyId, fn)`. `withSystem` is only for the outbox relay, cross-tenant jobs and the seed. A test fails if any `company_id` table lacks RLS.
- Match the style of the surrounding code; keep comments sparse and purposeful. Write user-facing text in plain language, in English and Spanish.

## Definition of done (every task)
1. `pnpm typecheck && pnpm lint && pnpm test` pass in every repo you touched (imaging: `uv run ruff check . && uv run pytest`; web/floor: also `pnpm build`).
2. The feature was **exercised for real**: curl, a script, or the browser with screenshots you looked at. Compiling is not verification.
3. If you touched a golden-path area, the E2E suites still pass (`invai-web`: `pnpm e2e`, and `E2E_API=1 pnpm e2e e2e/api-golden-path.spec.ts` on a fresh seed; `invai-floor`: `pnpm e2e`).
4. Stop any processes you started, and leave the shared dev DB usable.
5. Final report (`verify-and-report`): what you built, how you verified it (commands and results), decisions and why, and known gaps. Report failures honestly, with the output.
6. The review approved it (`independent-review`, plus co-reviewers for the card's risk flags), with evidence in `invai-docs/waves/<n>/reviews/`.

## Lessons (full log: `invai-docs/team/lessons.md`; add new ones with `log-lesson`)
- Parallel agents share one usage budget: keep 3–4 agents running at once, not more.
- `tsx watch` restarts the API when other agents edit files. Retry a request that died mid-restart, and restart stale non-watch workers before E2E runs.
- Check library APIs in `node_modules` (installed versions) or official docs before writing code. Several libraries here are newer than training data (TanStack Table v9, oRPC 1.15, Better Auth 1.7, drizzle 0.45, TypeScript 7).
- Seed data shapes the product's numbers: unrealistic seed sizes made gang sheets look 51.7% efficient until fixed (now 86–91%). Keep the seed realistic.
