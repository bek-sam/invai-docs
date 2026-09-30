# AWS cost estimate: staging and a small production

Read-only exercise: no `aws` or `sst` command was run, nothing was deployed. Priced from the config as it
exists on disk, and every price is a current public list price with its source and fetch date. Actual bills
will differ (usage assumptions are stated; AWS's own calculator/Cost Explorer is the source of truth once
something is deployed). All monthly figures use 730 hours/month and current on-demand, no-commitment pricing.

## 0. What was priced

- **Config version:** `invai-infra` local `HEAD` (`490884d`), which is **5 commits ahead of `origin/main`
  (`148df7d`) — unpushed.** That range includes `3dbb899` "SST config fixes for a first staging deploy, no
  deploy (T-24-1)", which is the commit that added most of the priced resources (VPC, RDS, Valkey, ECS
  services, S3, KMS, WAF, CloudFront, WAF). `sst.config.ts` at `HEAD` already contains all of T-24-1; there is
  no separate "before/after T-24-1" price difference to show because nothing was deployed before it and
  nothing after it changes the resource shapes in a way this estimate needs to distinguish. If `main` is
  pushed and re-read later, diff `sst.config.ts` at the new SHA against `3dbb899..490884d` before re-pricing.
- **Region:** not set in `sst.config.ts` (`aws.getRegionOutput()` reads the deploy-time `AWS_REGION`/profile).
  Priced as **us-east-1**, per the task's instruction when a region isn't pinned in config.
- **Stages priced:** `staging` and `production` as SST defines them in `sst.config.ts` (`isProd = stage ===
  "production"`; everything else, including a hypothetical small-pilot stage, behaves like staging unless it's
  literally named `demo`).
- Every price below is a **list price**, fetched 2026-09-30. No committed-use discount, Savings Plan, Reserved
  Instance or negotiated AWS/Anthropic discount is assumed.

## 1. Inventory — every billable resource in `sst.config.ts`

| Resource | Staging | Production | Always-on? | Source line |
|---|---|---|---|---|
| VPC, 2 AZs (default `az`) | 2 AZs | 2 AZs | n/a (free) | `new sst.aws.Vpc("Vpc", { nat: "ec2" })` |
| NAT: EC2 `t4g.nano`, one per AZ | 2 instances | 2 instances | Yes | `nat: "ec2"` → component default `t4g.nano` |
| S3 gateway VPC endpoint | free | free | — | `VpcEndpoint("S3Endpoint", ... Gateway)` |
| RDS PostgreSQL 17, Single-AZ (no `multiAz`) | `db.t4g.small`, 20 GB gp3 | `db.t4g.medium`, 100 GB gp3 | Yes | `new sst.aws.Postgres("Db", ...)` |
| RDS Proxy | none (`proxy: false`) | 1 proxy, min 2 vCPU | prod only | `proxy: isProd ? {...} : false` |
| RDS backups | 14 days | 35 days | n/a | `backupRetentionPeriod` |
| RDS deletion protection / final snapshot | off | on | n/a | `deletionProtection: isProd` |
| ElastiCache Valkey, single node, cluster mode off | `cache.t4g.micro` | `cache.t4g.small` | Yes | `new sst.aws.Redis("Redis", ...)` |
| ECS cluster (Fargate, not Spot) | 1 | 1 | — | `new sst.aws.Cluster("Cluster", ...)` |
| Fargate: **Imaging** (arm64, Cloud Map only, no ALB) | 2 vCPU / 8 GB, 1 task | 2 vCPU / 8 GB, 1–3 tasks | Yes (min) | `sst.aws.Service("Imaging", ...)` |
| Fargate: **Api** (arm64, behind ALB) | 0.5 vCPU / 1 GB, 1 task | 0.5 vCPU / 1 GB, 2–6 tasks | Yes (min) | `sst.aws.Service("Api", ...)` |
| Fargate: **Worker** (arm64, no ALB) | 1 vCPU / 2 GB, 1 task | 1 vCPU / 2 GB, 1 task | Yes | `sst.aws.Service("Worker", ...)` |
| Fargate one-off **Migrate** task | 0.5 vCPU / 1 GB, per release | same | No (per release) | `sst.aws.Task("Migrate", ...)` |
| ALB | 1, HTTPS 443 + HTTP redirect | 1 | Yes | `api.loadBalancer` |
| WAF: 2 Web ACLs (ALB regional + CloudFront), 4 rules each | **none** (`if (isProd)`) | 2 ACLs | prod only | `wafAcl(...)` |
| CloudFront distributions (Web, Floor) | 2 | 2 | Yes | `sst.aws.StaticSite("Web"/"Floor", ...)` |
| S3 bucket (`Files`), versioned, 7-day noncurrent expiry | 1 | 1 | — | `sst.aws.Bucket("Files", ...)` |
| KMS customer-managed key (field encryption), rotation on | 1 | 1 | Yes | `aws.kms.Key("FieldEncryptionKey", ...)` |
| SES sending domain (sandbox until owner requests production access) | 1 | 1 | — | `sst.aws.Email("Email", ...)` |
| SSM Parameter Store, SecureString, standard tier | ~18 params | ~18 params | — | `toSsm(...)` (not Secrets Manager) |
| CloudWatch Logs, one log group per container, 30-day retention | 4 groups (api, worker, imaging, migrate) | 4 groups | — | component default `retention: "1 month"`, not overridden |
| ECR (shared SST "bootstrap" asset repo, one per account/region) | shared | shared | — | `fargate.ts` `bootstrapData.assetEcrUrl`, not a per-service repo |
| Data transfer out (ALB/CloudFront/NAT to internet) | usage | usage | — | implicit |

Notable facts this inventory turned up:
- **No AWS Secrets Manager anywhere** — every secret goes through SSM `SecureString` (`toSsm`), which is free
  at the standard tier. Good for cost; worth confirming it stays that way.
- **No Multi-AZ** on RDS or Valkey in either stage (`multiAz` is never set, so it defaults to `false`). This
  is not a P0 violation (P0 requires retention and `noeviction`/cluster-off, both met) but it is a real
  availability gap for "production" worth a separate ops conversation, not a cost line.
- Redis/Valkey is **ElastiCache**, not a self-managed EC2 box — `cluster: false` and `maxmemory-policy:
  noeviction` are both set, matching the P0 requirement.
- WAF and Multi-AZ RDS Proxy exist **only in production** (`if (isProd)` / `isProd ? {...} : false`) — staging
  carries neither cost nor that protection.
- The `Migrate` one-off Fargate task only runs when `pnpm release:migrate` is invoked (once per release), so
  its cost is a handful of task-minutes per release, not a monthly recurring line.

## 2. Prices used (list price, us-east-1, fetched 2026-09-30)

| Item | Price | Source |
|---|---|---|
| Fargate ARM (Graviton), vCPU-hour | $0.032380 | [aws.amazon.com/fargate/pricing](https://aws.amazon.com/fargate/pricing/) |
| Fargate ARM, GB-hour | $0.003560 | same |
| EC2 `t4g.nano` on-demand | $0.0042/hr | [instances.vantage.sh/aws/ec2/t4g.nano](https://instances.vantage.sh/aws/ec2/t4g.nano) |
| RDS `db.t4g.micro` PostgreSQL, Single-AZ | $0.016/hr | [instances.vantage.sh/aws/rds/db.t4g.micro](https://instances.vantage.sh/aws/rds/db.t4g.micro) |
| RDS `db.t4g.small` PostgreSQL, Single-AZ | $0.032/hr | [instances.vantage.sh/aws/rds/db.t4g.small](https://instances.vantage.sh/aws/rds/db.t4g.small), cross-checked [economize.cloud](https://www.economize.cloud/resources/aws/pricing/rds/db.t4g.small/) |
| RDS `db.t4g.medium` PostgreSQL, Single-AZ | $0.065/hr | [instances.vantage.sh/aws/rds/db.t4g.medium](https://instances.vantage.sh/aws/rds/db.t4g.medium) |
| RDS gp3 storage | $0.115/GB-mo | [bytebase.com RDS pricing guide](https://www.bytebase.com/blog/understanding-aws-rds-pricing/) (June 2026), matches AWS's published gp3 rate |
| RDS backup storage beyond the free (=provisioned-storage) allowance | $0.095/GB-mo | same |
| RDS Proxy | $0.015/vCPU-hr, 2 vCPU minimum | [usage.ai RDS Proxy cost guide](https://www.usage.ai/blogs/aws/reserved-instances/rds/proxy-cost/) |
| ElastiCache `cache.t4g.micro`, Valkey | $0.0128/hr | AWS's own figure, quoted verbatim in the installed SST component's doc comment (`.sst/platform/src/components/aws/redis.ts:313`) and independently confirmed via [economize.cloud](https://www.economize.cloud/resources/aws/pricing/elasticache/cache.t4g.micro/) |
| ElastiCache `cache.t4g.small`, Valkey | $0.0205/hr | [economize.cloud](https://www.economize.cloud/resources/aws/pricing/elasticache/cache.t4g.small/) |
| Application Load Balancer | $0.0225/hr + $0.008/LCU-hr | [aws.amazon.com/elasticloadbalancing/pricing](https://aws.amazon.com/elasticloadbalancing/pricing/) |
| WAF | $5/web ACL/mo + $1/rule/mo + $0.60/M requests | [wafpricing.com/aws-waf-pricing](https://wafpricing.com/aws-waf-pricing) |
| CloudFront (all-edge-locations, US/EU) | $0.085/GB + $0.0100/10K HTTPS requests; **1 TB + 10M requests/mo always free** | [CloudFront pay-as-you-go summary via blazingcdn.com](https://blog.blazingcdn.com/en-us/understanding-cloudfront-request-and-data-transfer-costs) |
| S3 Standard storage | $0.023/GB-mo | [devzero.io S3 pricing 2026](https://www.devzero.io/blog/aws-s3-pricing) |
| S3 PUT/COPY/POST/LIST | $0.005/1,000 | same |
| S3 GET and other | $0.0004/1,000 | same |
| CloudWatch Logs ingestion (Standard class) | $0.50/GB, first 5 GB/mo free | [cloudzero.com CloudWatch pricing](https://www.cloudzero.com/blog/cloudwatch-pricing/) |
| CloudWatch Logs storage | $0.03/GB-mo | same |
| KMS customer-managed key | $1.00/key/mo + $0.03/10K symmetric requests beyond 20K free/mo | [repost.aws / AWS KMS pricing](https://repost.aws/questions/QU-iUNxZ-LQbGPhX0TQvGadA/kms-usage-cost-per-service) |
| SES sending | $0.10/1,000 emails | [saaspricepulse.com Amazon SES pricing 2026](https://www.saaspricepulse.com/blog/amazon-ses-pricing-per-1000-emails-2026) |
| SSM Parameter Store, standard `SecureString` | $0 (free, ≤10,000 params, standard throughput) | [AWS Systems Manager pricing](https://aws.amazon.com/systems-manager/pricing/) |
| ECR private storage | $0.10/GB-mo | [cloudburn.io Amazon ECR pricing](https://cloudburn.io/blog/amazon-ecr-pricing) |
| VPC interface endpoint | $0.01/hr per AZ + $0.01/GB processed | [oreateai.com VPC interface endpoint pricing](https://www.oreateai.com/blog/demystifying-aws-vpc-interface-endpoint-pricing-what-you-need-to-know/642fe9fb9d821f9d6ae7947312910867) |
| Data transfer out to internet | first 100 GB/mo free (aggregated), then $0.09/GB to 10 TB | [egresscost.com AWS us-east-1 egress 2026](https://egresscost.com/aws/us-east-1/) |
| Anthropic Claude Opus 5 | $5 / $25 per MTok in/out (list) | [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing), confirmed against `invai-backend/src/ai/models.ts` `MODEL_PRICES` |
| Anthropic Claude Haiku 4.5 | $1 / $5 per MTok in/out (list) | same |
| GitHub Actions, Linux 2-core (x64), private repo | $0.006/min; Pro/Team plans include 3,000 free min/mo | [GitHub Actions billing docs](https://docs.github.com/en/billing/concepts/product-billing/github-actions) |
| AWS new-account credit (2026 model) | $100 immediately + up to $100 more for 5 onboarding tasks; valid 6 months or until spent, expires 12 months after account creation — **not** the old "12 months always-free" tier | [AWS Free Tier explainer, Sep 2026](https://spot.rackspace.com/blog/aws-free-tier) |
| CloudFront "Always Free" tier | 1 TB out + 10M requests/mo, perpetual, separate from the account credit above | same CloudFront source as above |

## 3. Scenario (a): staging as configured today

Always-on resources, 730 hrs/mo. ALB/CloudFront traffic assumed low (internal QA + agent testing), so LCU and
CloudFront usage are small estimates, flagged.

| Line | Calculation | Monthly |
|---|---|---|
| NAT EC2 ×2 (`t4g.nano`) | 2 × 730 × $0.0042 | $6.13 |
| NAT data processing (assumption: ~20 GB/mo dev/CI egress) | 20 × $0.09 | $1.80 |
| RDS `db.t4g.small` | 730 × $0.032 | $23.36 |
| RDS gp3 storage, 20 GB | 20 × $0.115 | $2.30 |
| RDS backup storage | within the free (=20 GB) allowance | $0.00 |
| ElastiCache `cache.t4g.micro` | 730 × $0.0128 | $9.34 |
| Fargate Api, 0.5 vCPU/1 GB ×1 | 730 × (0.5×0.03238 + 1×0.00356) | $14.41 |
| Fargate Worker, 1 vCPU/2 GB ×1 | 730 × (1×0.03238 + 2×0.00356) | $28.84 |
| Fargate Imaging, 2 vCPU/8 GB ×1 | 730 × (2×0.03238 + 8×0.00356) | $68.06 |
| Migrate task (per release, ~5 min × a few releases/mo) | negligible | $0.10 |
| ALB hourly | 730 × $0.0225 | $16.43 |
| ALB LCU (assumption: ~1 LCU avg) | 730 × $0.008 | $5.84 |
| WAF | not created in staging | $0.00 |
| CloudFront ×2 sites (assumption: under the 1 TB/10M free tier) | — | $0.00 |
| S3 (assumption: ~5 GB stored, light request volume) | 5×$0.023 + requests | $0.50 |
| CloudWatch Logs ×4 groups (assumption: ~3 GB/mo, under 5 GB free) | — | $0.30 |
| KMS key | $1.00 + negligible requests | $1.00 |
| SES (assumption: ~200 dev/QA emails/mo) | 0.2×$0.10 | $0.02 |
| ECR (shared bootstrap repo, this stage's share) | assumption | $1.00 |
| Data transfer out, other (assumption: under the 100 GB free pool) | — | $0.00 |
| **AWS subtotal** | | **≈ $179/mo** |
| Anthropic (staging must use a real key — `providerKey` has no default outside `demo`; assumption: light dev/QA smoke calls only) | | $2–6/mo |
| GitHub Actions overage (see §6) | | ≈ $52/mo |
| **Scenario (a) total** | | **≈ $235–240/mo** |

## 4. Scenario (b): staging with realistic cost cuts

Exact config changes for each cut, all inside `invai-infra/sst.config.ts`:

| Cut | Config change | Effect |
|---|---|---|
| Single AZ | `new sst.aws.Vpc("Vpc", { nat: "ec2", az: 1 })` | 1 NAT instance instead of 2; loses AZ redundancy for the ALB/ECS placement in staging (acceptable for a non-prod stage) |
| Smallest RDS class | `instance: isProd ? "t4g.medium" : "t4g.micro"` | `db.t4g.micro` is the smallest Graviton burstable RDS class |
| Database stopped outside testing hours | **Not expressible in `sst.config.ts` today** — RDS `stop`/`start` needs a new EventBridge Scheduler rule + a small Lambda (or the AWS "Instance Scheduler" sample app) with `rds:StopDBInstance`/`StartDBInstance`, which this file doesn't create yet. Needs a new task, not a one-line change. | Compute (not storage) charges drop while stopped; assumed 8 h/day, 5 days/week ≈ 30% uptime |
| "No NAT" | `new sst.aws.Vpc("Vpc", { az: 1 })` (drop `nat` entirely) | **See the finding below — this cut does not actually save money in this architecture.** |

**Finding on "no NAT":** removing NAT doesn't just cut off outbound calls to Anthropic/EasyPost/marketplaces —
Fargate's own container agent needs a network path to pull the image from ECR and to resolve the `ssm:` secrets
in the task definition (SST delivers every backend secret via SSM `SecureString`, not as plaintext). Without
NAT, that path has to come from VPC interface endpoints: `ecr.api`, `ecr.dkr`, `logs`, and `ssm` at minimum —
4 endpoints × $0.01/hr × 1 AZ × 730 h = **$29.20/mo**, before any data-processing charge. That's more than the
$3.07–6.13/mo the NAT EC2 instance(s) cost in the first place. **Recommendation: keep `nat: "ec2"` (already
the cheapest NAT option SST offers) and take the single-AZ cut instead** — it gets almost the same saving
($3.07/mo vs. two instances' $6.13/mo) without breaking task startup or outbound provider calls.

| Line | Calculation | Monthly |
|---|---|---|
| NAT EC2 ×1 (single AZ) | 730 × $0.0042 | $3.07 |
| NAT data processing (lower dev-only traffic) | ~10 GB × $0.09 | $0.90 |
| RDS `db.t4g.micro`, stopped ~70% of the time | 0.30 × 730 × $0.016 | $3.50 |
| RDS gp3 storage, 20 GB (bills 24/7 regardless of stop/start) | 20 × $0.115 | $2.30 |
| Scheduler Lambda + EventBridge rule | within free tier | $0.00 |
| ElastiCache `cache.t4g.micro` (already smallest; ElastiCache has no stop/start) | 730 × $0.0128 | $9.34 |
| Fargate Api, unchanged (already the smallest reasonable size) | | $14.41 |
| Fargate Worker, unchanged | | $28.84 |
| Fargate Imaging, unchanged | | $68.06 |
| ALB + CloudFront + S3 + Logs + KMS + SES + ECR + transfer | same assumptions as §3 | $19.16 |
| **AWS subtotal (single-AZ + micro RDS + scheduled stop only)** | | **≈ $150/mo** |
| Anthropic + GitHub Actions | same as §3 | ≈ $54–58/mo |
| **Scenario (b) total, safe cuts only** | | **≈ $205–210/mo** |

**Optional further cut (needs sign-off, not mine alone to make):** downsizing Worker to 0.5 vCPU/1 GB
(`backend-foundation` should confirm BullMQ throughput is still acceptable) saves **$14.43/mo**, and downsizing
Imaging to 1 vCPU/4 GB for staging only (`imaging-engineer` must confirm this still meets the peak-RSS/render
budget in `imaging-change-with-budget`) saves **$34.03/mo**. With both: AWS subtotal ≈ **$102/mo**, scenario
total ≈ **$156–161/mo**. I did not apply these myself — they cross into other roles' owned budgets.

## 5. Scenario (c): small production (1–3 pilot shops)

Baseline = the minimum always-on footprint (`scaling.min`), not the autoscaled ceiling. A real pilot launch
could scale Api up to 6 tasks and Imaging up to 3 under load; this is the floor, not the ceiling.

| Line | Calculation | Monthly |
|---|---|---|
| NAT EC2 ×2 | 2 × 730 × $0.0042 | $6.13 |
| NAT data processing (assumption: ~15 GB/mo real provider calls for 1–3 shops) | 15×$0.09 | $1.35 |
| RDS `db.t4g.medium` | 730 × $0.065 | $47.45 |
| RDS gp3 storage, 100 GB | 100 × $0.115 | $11.50 |
| RDS backup storage | within the free (=100 GB) allowance, assumption | $0.00 |
| RDS Proxy, 2 vCPU | 2 × 730 × $0.015 | $21.90 |
| ElastiCache `cache.t4g.small` | 730 × $0.0205 | $14.97 |
| Fargate Api, 0.5 vCPU/1 GB ×2 (min) | 2 × 730 × 0.01975 | $28.82 |
| Fargate Worker, 1 vCPU/2 GB ×1 | | $28.84 |
| Fargate Imaging, 2 vCPU/8 GB ×1 (min) | | $68.06 |
| Migrate task (per release) | | $0.10 |
| ALB hourly | 730 × $0.0225 | $16.43 |
| ALB LCU (assumption: ~2 LCU avg for 1–3 shops) | 730 × 2 × $0.008 | $11.68 |
| WAF ×2 ACLs (ALB + CloudFront), 4 rules each | 2 × ($5 + 4×$1) | $18.00 |
| WAF requests (assumption: ~2M req/mo) | 2×$0.60 | $1.20 |
| CloudFront ×2 sites (assumption: under the 1 TB/10M free tier at this scale) | | $0.00 |
| S3 (assumption: ~30 GB stored — order files, gang sheets, labels — growing over time) | 30×$0.023 + requests | $1.50 |
| CloudWatch Logs ×4 groups (assumption: ~15 GB/mo real traffic, 10 GB over the free 5 GB) | 10×$0.50 + 15×$0.03 | $5.45 |
| KMS key | $1.00 + ~$0.09 requests | $1.09 |
| SES (assumption: ~3,000 order/notification emails/mo across 1–3 shops) | 3×$0.10 | $0.30 |
| ECR (shared bootstrap repo, this stage's share) | assumption | $1.00 |
| Data transfer out, other (assumption: under the 100 GB free pool) | | $0.00 |
| **AWS subtotal** | | **≈ $286/mo** |
| Anthropic (see §6 for the token math) | typical case | ≈ $10–38/mo |
| **Scenario (c) total** | | **≈ $296–324/mo (call it ≈ $310/mo)** |

No GitHub Actions line here: `deploy.yml` only fires on a manual dispatch or a `v*` tag push (a few times a
month at most), not on every commit, so it doesn't scale with production traffic the way `ci.yml` does.

## 6. Usage-based items, with assumptions shown

### Anthropic tokens (source: `invai-backend/src/ai/models.ts` `ROUTES` + `MODEL_PRICES`, cross-checked against
Anthropic's own pricing page in §2)

All routes but `market_niche` run on Claude Opus 5 ($5/$25 per MTok in/out); `market_niche` runs on Haiku 4.5
($1/$5 per MTok). The Starter plan (`invai-backend/src/modules/billing/service.ts` `PLAN_CATALOG`) allows
**500 AI credits/shop/month**, 1 credit = 1,000 billable tokens (cache reads count at 10%). For 1–3 pilot
shops on Starter, that's up to 500–1,500 credits/mo if they use the full allowance:
- **Low** (mostly cached/input-heavy calls): ≈ $10/mo for 3 shops at full allowance.
- **Typical** (a ~25/65/10 input/output/cache-read split, which is roughly what a listing draft + a few
  assistant turns looks like): ≈ $25–30/mo for 3 shops at full allowance.
- **High** (worst case, all Opus 5 output tokens, no caching): 1,500 credits × 1,000 tokens × $25/MTok ≈
  $37.50/mo.
- The weekly digest route (`digest_narrative`) is separately capped at `DIGEST_MAX_CENTS_PER_WEEK` (10¢/shop/
  week by default, per the code comment in `models.ts`) ≈ $0.43/shop/mo, already inside the above range.
- Staging must run on a **real** Anthropic key too — `providerKey()` in `sst.config.ts` only defaults the
  provider secrets to a placeholder space on the `demo` stage; staging and production both fail to deploy with
  an unset key. Staging usage is assumed to be light manual/QA smoke-testing, not pilot-shop volume: $2–6/mo.

### SES emails
$0.10/1,000. Staging: ~200 dev/QA emails/mo ≈ $0.02. Production: ~3,000/mo across 1–3 shops (order
confirmations, receiving alerts, the weekly digest) ≈ $0.30. SES starts in the sandbox (recipient allow-list
only) until the owner requests production access — a policy step, not a cost.

### S3 GB
Already folded into each scenario's S3 line (§3–§5) with its own stated GB assumption; repeated here per the
task's checklist for visibility, not double-counted.

### GitHub Actions minutes
`ci.yml` runs on every push to `main` in 6 of the 8 repos (backend, web, floor, contracts, ui, imaging);
`invai-infra` has no `ci.yml` at all, and every `e2e.yml` is `workflow_dispatch`-only (manual), not a
per-push cost. Commits to `origin/main` over the last 6 full days (2026-09-24 through 2026-09-29, the
`git log` this was computed from) as a proxy for pushes per day:

| Repo | commits/day (6-day avg) | est. min/run | min/day |
|---|---|---|---|
| backend | 33.3 | 7 (Postgres/Valkey services, role setup, MinIO, full test suite) | 233 |
| web | 14.7 | 6 (sibling checkouts, build) | 88 |
| floor | 4.0 | 6 | 24 |
| contracts | 7.7 | 3 | 23 |
| ui | 1.5 | 3 | 5 |
| imaging | 3.7 | 4 (`uv sync`, ruff, pytest) | 15 |
| **Total** | | | **≈ 388 min/day ≈ 11,620 min/mo** |

At $0.006/min (Linux 2-core, current GitHub rate) minus a Team plan's 3,000 free min/mo: (11,620 − 3,000) ×
$0.006 ≈ **$52/mo**. Caveat: commits aren't 1:1 with pushes (the wave process can push several commits in one
`git push`), and this rate reflects the last week's intense multi-agent build activity (v1 build + waves 23–24),
not necessarily a calmer steady state — treat this as an upper-bound proxy, not a measured push count.

## 7. Free tier / new-account credits

- **AWS:** the pre-2026 "12 months always free" EC2/RDS/S3 tier is gone for new accounts. The current model
  (per the Sep 2026 sources in §2) gives a new account **$100 immediately, up to $100 more for 5 onboarding
  tasks**, valid for 6 months or until spent (whichever comes first), expiring 12 months after account
  creation. At scenario (a)'s ≈$235/mo, a $100–200 credit covers roughly **2–3 weeks to just over 3 weeks** of
  staging, not months — plan the pilot's AWS spend assuming the credit runs out well before go-live, not as a
  durable discount.
- **CloudFront** keeps its own separate, perpetual "Always Free" allowance (1 TB data transfer out + 10M
  requests/mo) regardless of account age — this is why both Web and Floor CloudFront lines are $0 in every
  scenario above at this traffic level.
- **Anthropic:** no ongoing free tier beyond a small one-time credit for new API accounts (per Anthropic's own
  pricing FAQ, §2 source); not modeled as a discount here since it's one-time and small.
- **GitHub Actions:** the included monthly minutes (3,000/mo on Pro/Team) are already subtracted in §6, not an
  extra credit on top.

## 8. Biggest cost drivers and recommended cuts

1. **Fargate Imaging (2 vCPU/8 GB) — $68/mo in every scenario.** It's the single largest line everywhere
   because it's sized for gang-sheet compose peak RSS, not for idle. Cutting it needs `imaging-engineer`
   sign-off against the render budget (`imaging-change-with-budget`); I did not cut it myself.
2. **RDS (instance + Proxy + storage) — $23–81/mo depending on stage.** Production's $80.85/mo (`db.t4g.
   medium` + Proxy + 100 GB) is the second-biggest line; staging's is cut most effectively by the single-AZ +
   `t4g.micro` + scheduled-stop combination in §4 ($25.66/mo → $5.80/mo compute+storage).
3. **ALB + WAF — $16–46/mo, WAF production-only.** Fixed hourly costs that don't scale down with low traffic;
   the $0.60/M-request WAF charge and LCU charges are the only usage-sensitive parts.
4. **GitHub Actions overage — ≈$52/mo**, driven almost entirely by `invai-backend`'s CI (Postgres/Valkey
   services, full test suite, ~233 min/day at the current push rate) — the single biggest lever here is
   reducing backend CI runtime or push frequency, not an AWS change.

**Recommended cuts, in order of size-to-risk:**
- Staging: single-AZ NAT + `db.t4g.micro` + scheduled RDS stop/start (all in `platform-sre`'s own paths,
  ≈$24/mo saved, no cross-role sign-off needed).
- Staging (optional, needs sign-off): Worker and Imaging downsizing, ≈$48/mo more, pending
  `backend-foundation`/`imaging-engineer` confirmation.
- Do **not** remove NAT entirely — it costs more in required VPC interface endpoints than it saves (§4).
- Production: nothing here is a "cut" without accepting a P0 or reliability trade-off (Multi-AZ isn't even
  turned on yet, so there's no redundancy to give up for savings); the actionable lever for production cost is
  watching AI token spend per shop (§6) as pilot usage ramps, via `cost-review`.

## 9. Caveats

- This is a **model**, not a bill. Every "assumption" line is exactly that; once anything is deployed, replace
  it with AWS Cost Explorer / Anthropic Console numbers via the monthly `cost-review`.
- No committed-use discounts (Reserved Instances, Savings Plans, Anthropic volume pricing) are assumed.
- RDS storage growth, S3 growth and log volume all compound over time; these are month-1-of-a-pilot numbers,
  not a steady-state year-2 number.
- GitHub Actions minutes are a push-rate proxy from one week of intense wave activity — re-measure from actual
  `gh run list` billing data once a calmer cadence is established.
