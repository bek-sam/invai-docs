# Wave 24 plan review — architect

**Verdict: approve with changes**

Only `wave.md` exists for wave 24 (no individual `T-24-*.md` cards yet). Reviewed at the wave-plan
level, against `invai-infra/sst.config.ts`, the four repos' `Dockerfile`s, and
`invai-backend/src/db/migrate.ts`.

## Checked
- Hard fence held: nothing in the wave asks for `sst deploy`, `aws`, secrets or accounts; checks are
  `tsc`/`sst` type-check/`docker build`/compose, matching the guard hook.
- `sst.config.ts` today is genuinely placeholder-stage (`api.invai.example`, `RDS Proxy is optional`,
  no ACM/HTTPS listener, no WAF/S3 gateway endpoint, no `stopTimeout`) — T-24-1's scope matches what's
  actually missing.
- `invai-backend/src/db/migrate.ts`'s `runMigrations` today calls `ensureReferenceData` inline as
  part of the same run; T-24-2 splitting this into separate "migrate" and "reference-seed" entry
  points for production use (vs. the dev/test path that still wants both) is a reasonable design; no
  conflict with T-22-2 (wave 22, same owner role) which only touches the advisory-lock/timeout
  portion of the same file — sequential waves, same role, no overlap risk.

## Required changes
1. **The migrate/bootstrap entry point is an interface three concurrently-running cards depend on,
   and nothing names it.** T-24-2 (backend-foundation) builds "compiled migrate + bootstrap
   (`invai_app`, proxy secret) + reference-seed entry points." T-24-3 (platform-sre)'s Dockerfile
   needs to know the exact compiled command/path to put in its image (`CMD`/entrypoint or a
   documented `docker run` invocation for the one-off task). T-24-1 (platform-sre)'s SST config
   needs the same command to define the AWS one-off migrate task. The plan's "Order" section lists
   T-24-2 and T-24-3 as running "first" together, with T-24-1 "in parallel" — i.e. up to three cards
   at once, each needing an interface none of them owns alone. Add an explicit interface line to the
   wave plan before cards are written: the exact compiled entry-point paths/commands T-24-2 will
   produce (e.g. `dist/db/migrate-cli.js` and `dist/db/bootstrap-cli.js`, run as `node
   dist/db/migrate-cli.js`), so T-24-1 and T-24-3 aren't each guessing or inventing their own name
   for it. This is the same class of gap `task-intake`'s "Interfaces promised" step exists to catch.

## Notes (non-blocking)
- PM's note about stale `waves/backlog.md` wave-number labels (B-01/02/57/58/59/73/74/77) doesn't
  affect contract or architecture ownership; no action needed from me.
