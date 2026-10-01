# Wave 24: deployable without an AWS account (roadmap wave 10, agent part)

> **PAUSED (decision 0019) until the owner starts the AWS setup. Do not run T-24-1..4.** The polish hand-off at the end of this file was planned and runs as wave **P1** (`waves/P1/wave.md`), not as wave 24.

- Status: **paused** (decision 0019). Dates: planned; can start in parallel with wave 22/23 cards that don't touch `invai-infra` or the backend build (at most 3 builders at once overall)
- Goal (user outcome): the owner's first staging deploy is a short checklist. `sst.config.ts` synthesizes with no known deploy-time failure, every image builds and runs as non-root, migrations and reference data run as a one-off task as the right DB users, and every secret, domain and account step the owner must do is an exact OI checklist.
- **Hard fence:** no `sst deploy`, no `aws`, no secrets set, no accounts, no spend. The guard blocks these. Checks are `tsc`, `sst` config type checks without credentials if possible, `docker build`, local `docker run`, and compose.
- Sources (backlog): B-01, B-02, B-03, B-23 (KMS part: provider interface, local fallback), B-57, B-58, B-59, B-73, B-74, B-77, B-163 (if not done in wave 22), B-107 (AWS parts: WAF, S3 gateway endpoint, ARM), wave 9 deferrals (`IMAGING_SHARED_SECRET` to all services, ECS `stopTimeout` ≥ 35 s, compose `full` profile flags).
- Plan reviewed by: product-manager (2026-09-28, approve), architect (2026-09-28, approve with change A1: entry points named above). Security co-reviews every platform-sre card.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-24-1 SST config fixes: imaging service URL, worker env, stage URLs, one domain + ACM, HTTPS listener, Valkey `noeviction` cluster-off, RDS production settings, S3 lifecycle/CORS/versioning, secrets list, KMS key, WAF, S3 gateway endpoint, ARM, `stopTimeout` (B-02, B-03 HTTPS, B-57, B-73, B-74, B-77, B-107) | platform-sre | opus | reviewer (sonnet) + security-reviewer | security | planned |
| T-24-2 Backend production build: compiled migrate + bootstrap (`invai_app`, proxy secret) + reference-seed entry points, `drizzle/` in the image, SMTP/SES env schema, KMS field-encryption provider behind an interface (B-01, B-58 env, B-59, B-23 KMS) | backend-foundation | fable | reviewer (opus) + security-reviewer | auth, pii, migration | planned |
| T-24-3 Dockerfiles and compose: multi-stage, non-root, pinned by digest, HEALTHCHECK, root `.dockerignore`, compose `full` profile that runs the built images end to end locally (B-21 images, B-76 compose) | platform-sre | sonnet | reviewer (opus) + security-reviewer | security | planned |
| T-24-4 Deploy runbook and the owner's go-live checklists (OI entries with exact steps: AWS account and SSO, GitHub OIDC role, region, domain + Route 53, `sst secret set` per stage, SES production access + DKIM/SPF/DMARC, first staging deploy, smoke test, rollback) | docs-writer | sonnet | platform-sre (domain) + security-reviewer | — | planned |

## Agreed interfaces (architect A1)
- Built entry points in the backend image (T-24-2 provides, T-24-1 and T-24-3 consume): `node dist/db/bootstrap-cli.js` (creates/updates `invai_app` and its password from a secret; idempotent), `node dist/db/migrate-cli.js` (advisory-locked migrations only), `node dist/db/reference-seed-cli.js` (plans, trademark marks; idempotent), `node dist/api/server.js`, `node dist/worker/index.js`. `drizzle/` is copied to `/app/drizzle`. The one-off ECS task runs the three CLIs in that order.

## Order
- T-24-2 and T-24-3 first (images), T-24-1 in parallel (config only), T-24-4 last (it documents what the others built).

## Integration gate
- [ ] `docker build` of api/worker, imaging, web, floor images; `docker compose --profile full up` runs the golden path against the built images (`E2E_API_URL`, `E2E_WEB_URL`)
- [ ] Fresh reset, migrate (through the compiled migrate entry), seed; `run-golden-path` on the dev stack
- [ ] `sst` config type-checks; no secret values anywhere in git (`gitleaks`-style scan)
- [ ] Pushed to `main`

## Build log
- 2026-09-29 Cards written (T-24-1..4). Grant T-24-1: `invai-web/vite.config.ts` and `src/lib/build/csp.ts`, prod `connect-src` only (B-190), web-engineer co-reviews. T-24-1 started (runs beside wave 22's T-22-2 and T-22-3; 3 builders).
- 2026-09-29 T-24-1 built: infra `3dbb899`, web `c1d53a8` (B-190 prod connect-src). In review (reviewer, security).
- 2026-09-29 Paused by the owner (decision 0019) until the AWS setup starts; analytics A1/A2 go first. T-24-1 state is unchanged: reviewer-approved; security and web co-reviews missing; the web build needs VITE_API_URL.
- 2026-09-30 T-24-1 web-engineer co-review r1 approve (the grant is respected, the dev CSP is byte-identical, CI sets VITE_API_URL). Missing CSP unit cases go to B-218. Security co-review running.
- 2026-09-30 T-24-1 security co-review r1 changes-required: S-45 (Medium, platform-sre). The ECS tasks inherit SST's default execution role with `ssm:GetParameter*`/`secretsmanager:GetSecretValue` on `*`, so a lower stage could read production's `MIGRATION_DATABASE_URL`. Fix: `transform.executionRole` scoped to `/invai/${stage}/*` on Api, Worker, Imaging and Migrate. The web half (`c1d53a8`, B-190 CSP) is clean per security, the reviewer and web-engineer. Tech lead ruling: `c1d53a8` is pushed with wave 23's web commits; infra `3dbb899` stays unpushed until the S-45 round 2 is approved (when the owner restarts wave 24).

## Handoff from wave A2 (2026-09-30, A2 tech lead): the next agent wave
The deploy cards above (T-24-1..4) stay paused until the owner starts the AWS setup (decision 0019). The next wave the team can run now takes the leftovers below. A fresh tech lead plans it from here; at most 5 cards and 3 agents at once, decisions 0018 and 0019.

- **State:** A2 is done (see `waves/A2/wave.md`): contract 0.10.0 (D9–D13, six action kinds, `today.actions`, `today.recordActionClick`), backend (assistant tools v6 with prompt v6, digest D9–D13, the D2 bridge mover, Today actions in the `today_action_sets`/`today_actions`/`today_action_clicks` tables, migration 0038), web (Profit v2, Operations, Inventory health, Designs lifecycle, the Today actions panel). The gate stamp and pushed SHAs are in A2's build log. The dev DB is freshly seeded by that gate.
- **Candidates (PM ranks; at most 5 cards):**
  1. **B-228, first card** (backend-foundation, sonnet): a per-run test DB (`invai_test_<pid>`) and a free Redis DB picked in `src/test/global-setup.ts` unless set explicitly. Parallel agents collided on `invai_test` for the third time in A2 (lesson 2026-09-30). This retires the "pin your own DB" rule in `team/agent-brief.md` and absorbs B-215.
  2. **B-229** (Medium, blocks gates): two load flakes from A2 gate run 1: the `market/http.test.ts` retry timeout (use fake timers), and the `publish.acceptance` concurrent test comparing signed URLs (compare object keys). Owners: backend-foundation or backend-engineer (market) and ai-engineer. Small; it can ride with B-228 if the PM agrees, but split it by owner.
  3. **T-23-3 imaging polish** (`waves/23/T-23-3.md`, imaging-engineer, sonnet; reviewer opus; architect only if a contract change is needed). The card is written and was never started.
  4. **T-23-4 AI and market polish** (`waves/23/T-23-4.md`, ai-engineer, sonnet). The PM's B-131 spec prerequisite is done (`specs/market-signals.md` Step 3a). The card grants `src/modules/market/signals.ts`/`compute.ts` for B-131 only.
  5. **B-209** (Medium): design and order-item thumbnails never render (`designs.list` returns `previewKey: null`; 40/40 designs show the placeholder). backend-engineer (catalog) first, then a web check. Root-cause it first (`root-cause-bug`): the seed or the catalog service.
  6. **B-222** (Medium, floor-engineer): the Spanish QC result banner shows "APROBAR" (the button key) above "Aprobado: pedido …"; use a past-tense result key (`invai-floor/src/stations/QcStation.tsx:145`). Small; floor only.
  7. **B-227** (Low, platform-sre): the `db:reset` 40P01 deadlock seen once in the A1 gate. It didn't recur in A2's two gate runs. Investigate only if it recurs, or fold it into B-228, since both concern DB lifecycle.
  - Seven candidates exceed the cap. Suggested: B-228 plus B-229 (by owner), T-23-3, T-23-4, and B-209 with B-222 as a floor slot if one frees. B-227 goes to the backlog.
- **Small follow-ups from A2 reviews (backlog or fold-ins, not cards on their own):**
  - `analytics.losingOrders` shows Units 0 / Revenue $0 on every seeded losing order (T-A6 reviews). backend-engineer (finance) should verify it (B-230).
  - The Today actions build job keeps its jobId after 3 failed attempts, so that day can't re-queue and the panel stays hidden (T-A9 reviewer). A future forced rebuild must keep clicks.
  - A D2 mover with key "unmapped" shows the backend's label, which may be English under es (T-A7 r2).
  - None of D9–D13 fires on the demo seed (thresholds not met; D13 has no fixed costs). QA or the seed could add a fixture shop with fixed costs so D13 can be seen.
  - invai-ui follow-ups owned by product-designer: `PageHeader` actions clip at 390 px (a repeat: Profit and Operations), StatCard neutral state, KpiTile label truncation, visual priority for the top Today action, Spanish 4-digit money without a group separator (CLDR `minimumGroupingDigits`).
  - Low bugs still open: B-223 (raw English timeline string), B-224 (Today alert bodies English under es).
  - The real-model eval of prompt v6 (as-042, including injection) needs the owner's key. Keep it on the owner list; don't make it a card.
- **Environment:** name the repos for `pnpm gate` (infra holds T-23-6, T-23-7 and T-24-1 commits; OI-22 is unanswered). The gate took about 9 minutes per run. Disk is about 12 GB free (OI-20). An unknown API on :3142 keeps restarting under new PIDs; leave it alone. Report files in `waves/A2/reports/` are committed with the wave docs.
- **Fences:** Track D (B-178..B-181) stays out; OI-17 and OI-18 are not approved. No buyer PII in analytics, screens or AI prompts.
