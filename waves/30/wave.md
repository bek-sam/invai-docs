# Wave 30: print files and old renders follow the buyer-text clocks; built images that run end to end; guard false positives

- Dates: 2026-10-09 →
- Goal (user outcome): no gang-sheet print file and no leftover render keeps a buyer's personalization text past the 30-day clock, and a reused buyer photo is not lost at the first unit's clock (narrows the gaps behind Amazon's "30 days after delivery" row; it stays Partial until B-302 (audit_log flags) and B-303 (manual uploads) are closed); the backend ships compiled bootstrap, migrate and reference-seed commands, and every app image builds, runs as non-root and passes the API golden path from a local `docker compose --profile full` stack, so the owner's first staging deploy has no unknown build step; agents stop losing turns to guard false positives.
- Owner order 2026-10-09: "push everything to 100%, go". This lifts the pause on the AWS-free prep parts of waves 24–25 (decision 0019 still holds for anything that needs AWS). This tech lead runs only wave 30.
- Scope ref: always in scope (compliance Amazon DPP and security S-59: B-300, B-301, B-304; reliability and security prep for deploy: B-01, B-03 migrate step, B-59, B-58 code side, B-21 images, B-76 compose `full`; team tooling reliability: B-298).
- Plan reviewed by: product-manager (2026-10-09, approve with 2 wording edits; decision 0032 accepted: sheet files may go once a unit is purged, the screens must say why, B-308 for wave 31; `reviews/plan-pm.md`, docs 4cc6c26) and architect (opus, 2026-10-09, changes-required, 9 blocking card-text edits applied as written: sheet/preview orphans and the full reference-column list, join through `transfers.order_item_id`, bootstrap grants only CONNECT/USAGE so REVOKEs hold, RDS master user `invai` (one-line sst.config.ts grant to T-30-3), CLI bundling traps, RDS CA bundle in the image, `MIGRATION_DATABASE_URL` and seed output for `invai_full`, guard sinks that run implicitly, 3-agent slot rule; `reviews/plan-architect.md`, docs ebfb572). All edits were card text; no second plan round.
- Fences: no deploys, no `sst`, no `aws`, no accounts, no real keys, no outbound sends; gates run with AI keys blanked. Owner-pending items not touched: OI-3, 8, 13, 15, 17, 21, 25–32. At most 3 agents at once, reviewers included. No canary planted (OI-15 still open).
- Carried from wave 24: T-24-2 and T-24-3 were written but never run; T-30-2 and T-30-3 replace them (same agreed entry points, architect A1, already used by `invai-infra/sst.config.ts`). B-23 (KMS field encryption) is left for wave 31.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-30-1](T-30-1-print-files-and-orphan-renders.md) Gang-sheet print files, orphan renders and shared buyer photos follow the buyer-text clocks (B-300, B-301, B-304/S-59) | backend-engineer (privacy) | opus | reviewer (fable) + security-reviewer (opus) + compliance-officer (sonnet) | pii, files, tenancy, data deletion, floor-correctness | planned |
| [T-30-2](T-30-2-compiled-release-commands.md) Compiled entry points: api, worker, bootstrap, migrate, reference seed; `drizzle/` path; SMTP env proven against Mailpit (B-01, B-03 migrate, B-59, B-58) | backend-foundation | opus | reviewer (fable) + security-reviewer (opus) | auth, migration | planned |
| [T-30-3](T-30-3-images-and-compose-full.md) Multi-stage non-root images pinned by digest; compose `full` profile on its own DB runs the API golden path (B-21 images, B-76 compose) | platform-sre | sonnet | reviewer (opus) + security-reviewer (sonnet) | security (images, secrets in layers) | planned |
| [T-30-4](T-30-4-guard-heredoc-and-scratchpad.md) Guard: heredoc data bodies on an allowlist are not scanned as scripts; session scratchpad writable (B-298) | platform-sre | sonnet | reviewer (opus) + security-reviewer (opus) | security control | planned |

## Order and slots (3 agents at once)
1. Plan review: product-manager and architect (opus), in parallel.
2. Slot A: T-30-1, T-30-2, T-30-4 build in parallel (no shared files). T-30-3 starts at the first free slot after T-30-2 has committed its build config **and** bootstrap-cli (tech lead gives both SHAs). If T-30-2's review changes bootstrap, T-30-3 re-runs its AC7 proof.
3. Reviews take slots as each card finishes; T-30-3's compose run and the gate both need :3000, :5173, :5174 and :8000, so they never overlap.
- Ports and Valkey DBs: T-30-1 none (tests on `invai_test`; any scratch run uses Valkey DB 12); T-30-2 a throwaway Postgres container on :5440 and API on :3132 (Valkey DB 13); T-30-3 the :3000/:5173/:5174/:8000 slot, DB `invai_full`, Valkey DB 9; T-30-4 none.

## Agreed interfaces
- T-30-2 provides (architect A1, wave 24; already referenced by `invai-infra/sst.config.ts` lines 392, 440, 462): `node dist/api/server.js`, `node dist/worker/index.js`, `node dist/db/bootstrap-cli.js`, `node dist/db/migrate-cli.js`, `node dist/db/reference-seed-cli.js`; migrations read from `<app>/drizzle` (sibling of `dist/`). Bootstrap connects as the owner through `MIGRATION_DATABASE_URL` and takes the app role's name and password from `DATABASE_URL` (password also as `APP_DB_PASSWORD`), as the SST comments say.
- T-30-3 consumes these names in the Dockerfile and compose; `package.json` `start:*` scripts and the backend README move to the new paths in T-30-2.
- T-30-1: one nightly entry, `purgeBuyerPiiJob`, keeps its name; new counts in its result (`sheetFilesPurged`, `sheetsWaiting`, `orphanRendersDeleted`, `sharedPhotosKept`).

## Process notes
- QA acceptance tests first are skipped again (decision 0018 budget): T-30-1 has a security co-review that proves issues with failing tests, T-30-3's own proof is the API golden path on built images, and the gate runs every suite. Recorded as a deviation.

## Integration gate
- [ ] Fresh reset, migrate, seed, AI keys blanked (`OPENAI_API_KEY= ANTHROPIC_API_KEY= caffeinate -i pnpm gate <repos>`)
- [ ] `run-golden-path` passes: API, browser, floor; all checks in touched repos
- [ ] T-30-3's compose `full` API golden path result attached (card evidence, not rerun at the gate)
- [ ] Pushed to `main` in the exact allowed form

## Team metrics
| First-pass approvals | Canary caught? | Escaped defects | Reopened | Avg cycle time | Tokens per card |
|---|---|---|---|---|---|
| | none planted (OI-15 open) | | | | |

## Log
- 2026-10-09 Fresh tech lead (memory read from the absolute path). State: all repos clean and pushed (contracts 0f666f1, backend 32113d7, web 8d134d7, floor 9304da1, ui 52af2b8, imaging f2d2eda (untracked `.DS_Store`), infra 1644dd4, docs 6985c18); nothing listening on 3000–3199; Docker healthy; 29 GB free. Cards written; plan review next.
- 2026-10-09 Plan reviews: PM approve (0032, B-308 added), architect changes-required (9 edits applied). Slot A starts: T-30-1, T-30-2, T-30-4.

## Retro
