# Review of T-24-1 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: platform-sre on Opus 5.5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-infra`: `pnpm typecheck` | clean (`tsc --noEmit`, no output) |
| `invai-infra`: `pnpm lint` | `biome check .` — "Checked 4 files in 38ms. No fixes applied." |
| `invai-infra`: `.sst/platform/node_modules/.bin/esbuild sst.config.ts --bundle --platform=node --format=esm` | succeeds, 20.1kb — cross-repo `../invai-web/…/csp` and `../invai-floor/…/csp` imports resolve |
| `invai-web`: `pnpm typecheck` | clean |
| `invai-web`: `pnpm lint` | exit 0, "Checked 176 files… Found 1 warning" (pre-existing, `src/content/markdown.test.ts:106`, unrelated to this diff — confirmed by `git log` on that line) |
| `invai-web`: `pnpm test` | 19 files / 117 tests passed |
| `invai-web`: `VITE_API_URL=http://localhost:3000 pnpm build --outDir dist-review241` | built in 1.54s, no `VITE_S3_ORIGIN` set (no extra origin) — output deleted |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-infra origin/main` | no hits |
| `bash .claude/skills/independent-review/scan-test-weakening.sh invai-web origin/main` | no hits |
| Direct exercise of `uploadOrigin`/`connectSrc` via `node --experimental-strip-types` (bucket https origin, `https://*.amazonaws.com`, `http://evil.com`, `http://localhost:9000`, blank, undefined) | matches the report exactly: valid https/localhost origins pass through; wildcard and non-https/non-local throw `VITE_S3_ORIGIN must be one https origin…`; blank/undefined → no extra origin; `connectSrc(api, s3)` joins `'self'` + both, `connectSrc(api, "")` omits the empty one |
| `git -C invai-infra status --short` / `git -C invai-web status --short` | clean, nothing uncommitted |
| `git -C invai-infra diff --stat origin/main` / `git -C invai-web diff --stat origin/main` | infra: `README.md`, `infra/run-migrate.ts`, `package.json`, `sst.config.ts`; web: `src/lib/build/csp.ts`, `vite.config.ts` — matches owned paths + grant exactly |
| `grep -n "invai\.example\|AKIA\|sk_live\|sk_test\|-----BEGIN" sst.config.ts infra/run-migrate.ts README.md` | one hit, inside an error-message example string (`INVAI_DOMAIN=invai.example`), not a resource value — no real values hard-coded |
| Read `invai-infra/.sst/platform/src/components/aws/service.ts:2841` | confirms `imaging.url` (no `loadBalancer`) throws `VisibleError("Cannot access the URL because no public ports are exposed.")` — the fix (`imaging.service` / Cloud Map name) is a real bug fix, not busywork |
| Read `postgres.ts`, `bucket.ts`, `cluster.ts`, `task.ts`, `secret.ts`, `fargate.ts`, `@pulumi/aws/types/input.d.ts` (wafv2) against the diff | every non-obvious option used (`transform.instance`/`parameterGroup`, `transform.bucket`/`lifecycle`, `proxy.credentials`, `Cluster` vpc override shape incl. `containerSubnets`/`loadBalancerSubnets`/`cloudmapNamespace*`, `Task.dev: false`, `ssm`/`permissions` on `FargateBaseArgs`, `Secret(name, placeholder)` semantics, and the WAFv2 `notStatement.statements` array shape — which this provider version types as an array unlike raw Terraform's singular `statement`) matches the installed component/provider `.d.ts`, consistent with the clean `tsc` result |
| Read `invai-backend/src/env.ts` `PRODUCTION_KEYS` | 9 keys: `EASYPOST_API_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, ANTHROPIC_API_KEY, SHOPIFY_API_KEY, SHOPIFY_API_SECRET, SMTP_URL, MAIL_FROM, IMAGING_SHARED_SECRET` — all 9 covered: 8 as `sst.Secret` (7 `providerKey()` with a `demo`-only `" "` placeholder, plus `IMAGING_SHARED_SECRET` as `required()`), `MAIL_FROM` derived as a plain env value. `ALLOW_MOCKS: isDemo ? "true" : "false"` matches `env.ts`'s guard (`missingProductionKeys` + `ALLOW_MOCKS`) |
| Read `invai-backend/src/api/app.ts`, `src/api/health.test.ts` | `/readyz` exists already, so the ALB health check target is real |
| Read `invai-web/src/lib/build/csp.test.ts` | no test cases for `uploadOrigin` or the new `connectSrc(api, s3)` second argument (see Optional notes) |
| Read `invai-web/scripts/render-nginx-conf.ts` | confirms it still calls the old one-arg `connectSrc(origin)` with no S3 origin — matches the report's own disclosed gap, correctly named as outside this card's grant |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `imaging.service`/Cloud Map fix verified against `service.ts:2841`; `BETTER_AUTH_URL`/`WEB_ORIGIN`/`FLOOR_ORIGIN` in shared `backendEnvironment`; `INVAI_DOMAIN` regex-validated, throws without it; imaging S3 env (`S3_ENDPOINT/KEY/SECRET=""`, `S3_CREATE_BUCKET=false`); ACM + `443/https` with `80→443` redirect on the `Api` load balancer; `IMAGING_SHARED_SECRET` in `pick("IMAGING_SHARED_SECRET")` (imaging) and `backendSsm` (api/worker); `stopTimeout` 45s via `withStopTimeout` transform on every service; health on `/readyz`, confirmed to exist in the backend |
| 2 | Yes | `redis: { cluster: false, parameters: {"maxmemory-policy":"noeviction"} }`; RDS `transform.instance` sets `backupRetentionPeriod` 14/35, `deletionProtection`/`skipFinalSnapshot`/`finalSnapshotIdentifier` by stage, `transform.parameterGroup` sets `rds.force_ssl=1`; `pgUrl` uses `sslmode=verify-full`; S3 `versioning: true`, `cors` limited to `[webOrigin, floorOrigin]` GET/HEAD/PUT, lifecycle matches the real `{companyId}/…` key layout (no more dead `sheets/`/`raw/` prefixes); KMS key + alias + `kmsPermission` granted to api/worker/migrate only; WAF `ApiWaf` (REGIONAL, on the ALB) and `CdnWaf` (CLOUDFRONT, us-east-1 provider, on both `StaticSite`s) only when `isProd`; `S3Endpoint` gateway VPC endpoint on the private route tables; `architecture: "arm64"` on imaging/api/worker/migrate |
| 3 | Yes | All 9 `PRODUCTION_KEYS` accounted for (see evidence row above); `ALLOW_MOCKS` true only on `demo` |
| 4 | Yes | `Migrate` task command: `bootstrap-cli.js && migrate-cli.js && reference-seed-cli.js`, matching the wave's agreed interfaces exactly; `backendSsm` gives it both `DATABASE_URL` (app role, via proxy in prod) and `MIGRATION_DATABASE_URL` (owner role, direct) |
| 5 | Yes | `pnpm typecheck && pnpm lint` pass in `invai-infra` (re-run by me); esbuild bundles `sst.config.ts` cleanly (re-run by me); no `sst deploy`/`sst diff`/`aws`/secret-set command was run by the author or by me — `git status` in both repos is clean and no secret values appear in the diff |
| 6 | Yes | The owner-input table in the report and in `README.md`'s "Owner inputs" section list every secret/domain/region input against its `sst.Secret` name or env var; cross-checked against the `secret` object and `backendSsm`/`pick()` calls in `sst.config.ts` — consistent |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`git diff --stat`): infra `README.md`, `infra/run-migrate.ts`, `package.json` (scripts only, confirmed by diff), `sst.config.ts`; web `src/lib/build/csp.ts`, `vite.config.ts` (exactly the B-190 grant)
- [x] Nothing outside scope — no Dockerfile, backend entry-point or CI change (those are T-24-2/3/wave 25, correctly left alone)
- [x] Tests exercise the behavior, and none were weakened — `scan-test-weakening.sh` found no hits in either repo; existing suites (117 web tests) pass unchanged; the new `uploadOrigin`/`connectSrc` behavior has no *new* unit test (see Optional notes), but I exercised it directly myself with the adversarial cases (wildcard, non-https, localhost, blank) and it behaves exactly as documented
- [x] Tenancy / idempotency / money-in-cents / en-es text — not applicable to this card (infra config only, no app request path, no UI copy); N/A
- [x] Decisions recorded where needed — the report's "Decisions" section covers domain-as-env-var, SSM-over-link, private subnets, `verify-full`+`NODE_EXTRA_CA_CERTS`, bucket-wide lifecycle, each with a stated reason; no cross-cutting ADR was needed for an ops-only card, and the author correctly flagged "secrets via SSM only" as a candidate for a tech-lead-owned ops decision rather than deciding it unilaterally

## Optional notes (not blocking)
1. `invai-web/src/lib/build/csp.test.ts` has no unit test for the new `uploadOrigin()` or the second `connectSrc(api, s3)` argument — only `requireApiOrigin`/`connectSrc(api)` are covered. The grant text (`invai-web/vite.config.ts` and `src/lib/build/csp.ts`, prod `connect-src` only) doesn't name `csp.test.ts`, so I don't read this as scope creep the author should have taken; the author already flagged it explicitly to web-engineer with the exact cases needed, and I independently exercised those same cases live (see Evidence). Recommend web-engineer add the test before or alongside wiring `uploadOrigin` into `render-nginx-conf.ts`, so the security-relevant wildcard/non-https rejection has a permanent regression test.
2. The WAF rate limits (20,000/5min API, 5,000/5min CloudFront) and the never-verified Pulumi resource shapes (WAF nested statements, ECS environment `""` values, the `--target Migrate` dependency set) are honestly disclosed as untested against real SST/Pulumi in "Known gaps" — I independently checked the WAF `notStatement` shape against the installed `@pulumi/aws` `.d.ts` (it uses a `statements` array, which is what the diff uses) and it matches, so this looks lower-risk than the report frames it, but the owner's first `sst diff` remains the right place to catch anything I couldn't check offline.
3. The NAT-instance single point of failure and the `/internal` DLQ routes (no `read-only root filesystem`, ECS Exec on by default) are correctly deferred to wave 25 / security-reviewer per the report; nothing here weakens an existing control.
