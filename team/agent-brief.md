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
- **Tests:** own test DB per card (`TEST_DATABASE_URL=postgres://invai_app:invai@localhost:5432/<db>`, `TEST_MIGRATION_DATABASE_URL=postgres://invai:invai@localhost:5432/<db>`). Drop it at the end.
- **Shared links:** never re-link or edit a shared repo's `node_modules` (for example `@invai/contracts`), even briefly. To test other contracts, give your worktree its own `node_modules` directory.
- **Pinning contracts:** to test against other contract versions, give the worktree a real `node_modules` directory whose `@invai/contracts` points at your contracts worktree. Never change the shared repo's link. Every gate checks that all links point to `../../../invai-contracts`.
- **Worktrees:** next to the repos (`../<repo>-<card>`), never in `/tmp`. Symlink `node_modules` and run `node_modules/.bin/*` directly.
- **Long commands:** keep each under about 2 minutes. Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- **Cleanup:** kill only your own PIDs, drop your DBs, flush your Redis DB and remove your worktrees.
- **Code rules:** money is in cents; every tenant table has `company_id` and RLS; side effects are idempotent and run outside DB transactions; heavy work goes to jobs; all UI text is en and es, added by hand (never run `pnpm i18n`).

## Token budget (owner's standing rule: do the same job with the least usage)
- **Read** only your card, `wave.md` (your section plus the interfaces) and the files you change. Skip research docs unless your card cites them.
- **Screenshots:** builders take at most 6 key ones. Reviewers look at at most 3 of the builder's, and take their own only when something looks wrong.
- **E2E:** builders and reviewers run unit tests plus the specific flow they changed (curl, a script or one browser pass). Only the wave gate runs the full golden-path suites.
- **Reports:** the file holds the full detail. Your reply to the tech lead is at most 8 lines: status, SHAs, blockers and cross-card notes.
- **Writing:** make small edits rather than one huge file write, and don't paste large outputs; use `tail` and `grep`.
