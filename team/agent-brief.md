# Agent brief (read this instead of the long docs)

These are the working rules for every build, review or gate agent. Open other docs only when your card points to them.

## Environment
- Start every node/pnpm command with `export PATH="$HOME/.local/share/pnpm/bin:$HOME/.local/share/pnpm:$PATH"` (Node 24, pnpm 12.6).
- Local services run in Docker (`invai-infra/local`): Postgres :5432 (`invai`/`invai`, app role `invai_app`/`invai`), Valkey :6379 (DBs 0–15 only), MinIO :9000, Mailpit :8025.
- Seed logins: `owner@desertbloom.test` / `demo1234!`, plus admin@, office@, designer@, presser@, packer@, receiver@. Floor PINs are 1111–1188.
- `createdb` isn't on the host. Use `docker exec local-postgres-1 createdb -U invai -T invai <copy>`, then run `pnpm db:migrate` against the copy.
- The worker needs `MOCK_CARRIER_TRANSIT_HOURS=0.001` for E2E-style runs.
- Seed with imaging up and the worker stopped.
- macOS has no `timeout` command; use `perl -e 'alarm 120; exec @ARGV' <cmd>`.

## Hard rules
- **Ownership:** edit only the paths your card owns or grants. If you need someone else's lines, ask the tech lead for a grant.
- **Commits:** stage only your own hunks (`git apply --cached` or `git add -p`), check `git diff --cached`, then commit. Commit messages end with the co-author line given in your prompt.
- **Never:**
  - `pnpm install`, `pkill`/`killall`, `git stash`/`reset`/`checkout --` in a shared tree
  - `db:reset` of the shared dev DB (only the gate may)
  - push
  - write `seed-output.json`
- **Blocked actions:** if a permission check blocks a command, stop and report it. Don't route around it.
- **Tests:** own test DB per card (`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/<db>`, `TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/<db>`) and own Redis DB (`REDIS_URL=redis://localhost:6379/<n>`, n from 1 to 14). Since T-23-0 (B-205), a plain `pnpm test` goes to DB 15 instead of DB 0, but every plain run shares DB 15, so parallel agents still pin their own DB. Since T-23-0 AC6, every `pnpm test` also truncates its test DB at start, so two plain runs on the shared `invai_test` wipe each other. Always pin your own DB, and its name must contain `_test` (for example `invai_t231_test`); the dev DB `invai` is always refused. Drop your DB and flush only your Redis DB at the end.
- **Scratch seed stacks:** `pnpm db:reset` also clears the job queues in whatever `REDIS_URL` points to (default: the shared dev DB 0; B-219), so pin `REDIS_URL=redis://localhost:6379/<n>` on every backend command, `db:reset` included. The web dev server's CSP allows only API :3000 (B-220): for a browser run on a scratch stack, use API :3000 if `lsof` shows it free, or ask the tech lead for a slot.
- **Long commands:** anything that may take over 3 minutes (seed, full suites, E2E, dev:all, waiting for health) runs with `run_in_background` and is polled with short `tail`s. Never make a single foreground wait longer than 5 minutes: the runtime kills an agent after 10 minutes with no output (lesson 2026-09-29).
- **Shared links:** never re-link or edit a shared repo's `node_modules` (for example `@invai/contracts`), even briefly. To test other contracts, give your worktree its own `node_modules` directory.
- **Pinning contracts:** to test against other contract versions, give the worktree a real `node_modules` directory whose `@invai/contracts` points at your contracts worktree. Never change the shared repo's link. Every gate checks that all links point to `../../../invai-contracts`.
- **Worktrees:** next to the repos (`../<repo>-<card>`), never in `/tmp`. Symlink `node_modules` and run `node_modules/.bin/*` directly.
- **Long commands:** keep each under about 2 minutes. Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- **Cleanup:** kill only your own PIDs, drop your DBs, flush your Redis DB and remove your worktrees.
- **Code rules:** money is in cents; every tenant table has `company_id` and RLS; side effects are idempotent and run outside DB transactions; heavy work goes to jobs; all UI text is en and es, added by hand (never run `pnpm i18n`).

## Memory
- Your role's memory is `.claude/agent-memory/<role>/MEMORY.md`. Claude Code loads its first 200 lines into every run of your role, so read it: it holds the lessons that apply to you.
- Before your final reply, save 0–3 one-line entries (date, card, what you learned). No PII or secrets. Fix or delete entries that turned out wrong. `verify-and-report` and `independent-review` say the same.

## Token budget (owner's standing rule: do the same job with the least usage)
- **Read** only your card, `wave.md` (your section plus the interfaces) and the files you change. Skip research docs unless your card cites them.
- **Screenshots:** builders take at most 6 key ones. Reviewers look at at most 3 of the builder's, and take their own only when something looks wrong.
- **E2E:** builders and reviewers run unit tests plus the specific flow they changed (curl, a script or one browser pass). Only the wave gate runs the full golden-path suites.
- **Reports:** the file holds the full detail. Your reply to the tech lead is at most 8 lines: status, SHAs, blockers and cross-card notes.
- **Writing:** make small edits rather than one huge file write, and don't paste large outputs; use `tail` and `grep`.
