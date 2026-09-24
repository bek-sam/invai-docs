# InvAI hosting cost comparison (prices checked 2026-09-23)

## Summary
- **Recommendation: build on AWS from the start**, defined in SST v3. Use ECS Fargate on ARM, RDS Postgres, ElastiCache Valkey nodes, S3 and a CloudFront flat-rate plan. Estimated cost: **pilot about $265/mo, growth about $810/mo, scale about $2,140/mo** before discounts, and about **$1.8k/mo at scale** with a 1-year Savings Plan and a reserved database.
- **Why AWS from the start:** buyer shipping addresses are restricted PII under Amazon's Data Protection Policy (DPP). If the pilot prints Amazon labels, the pilot is already in audit scope. AWS covers most DPP controls natively: KMS, CloudTrail, VPC isolation, WAF and Inspector. Moving hosts later would cost a solo developer more time than the $75–150/mo saved on a cheaper host now.
- **Cheapest options, and their catch:**
  - Railway is cheapest at every stage, but Postgres there is a container you run yourself and compliance features need an Enterprise contract.
  - Hetzner + Coolify is cheap at growth and scale, but you run everything yourself and handle compliance yourself. Its June 2026 price rise made dedicated-CPU servers 2.2–2.7x more expensive.
  - Fly.io is cheap, but its own docs say Managed Postgres "security patches and version upgrades" are "not there yet". That is a red flag for an audit.
- **Best PaaS fallback:** Render. It has SOC 2 Type II and ISO 27001, AWS PrivateLink, and HIPAA workspaces on its $499 Scale plan.
- **Don't use Aurora Serverless v2** for a database that is busy all the time. It costs about 2x RDS at growth and scale (see §2).
- **Don't use Vercel for the web app.** It saves no money, WebSockets still need your own backend, and it adds another vendor that sees PII.

**Standard assumptions** (730 h/month, US East or the equivalent region; "unverified" marks any number I couldn't check against a live price page):

| | Pilot | Growth | Scale |
|---|---|---|---|
| web+api (always on) | 2 vCPU / 4 GB | 4 vCPU / 8 GB | 8 vCPU / 16 GB |
| workers (always on) | 1 vCPU / 2 GB | 3 vCPU / 6 GB | 6 vCPU / 12 GB |
| imaging 2 vCPU / 8 GB burst | 60 h/mo (2 h/day) | 240 h/mo (8 h/day) | 600 h/mo (20 h/day) |
| Postgres | 10 GB, ~2 vCPU / 4 GB, no HA | 80 GB (100 provisioned), 2 vCPU / 8 GB, HA | 400 GB (500 provisioned), 4 vCPU / 32 GB, HA |
| Redis (BullMQ) | ≤0.5–1 GB | 1 GB + replica | ~5 GB + replica |
| Objects / egress | 50 GB / ~100 GB | 1 TB / ~500 GB | 5 TB / 2 TB |
| Object requests / mo (my assumption) | 1M PUT, 3M GET | 3M PUT, 10M GET | 15M PUT, 50M GET |

---

## What the SP-API security review requires
Source: the Amazon Data Protection Policy, fetched from sellercentral.amazon.com/mws/static/policy?documentType=DPP.
- **Encryption:** PII at rest with AES-128 or RSA-2048 or stronger. TLS 1.2+ in transit.
- **Key management:** a documented key-management system covering key generation, storage, rotation and revocation. Credentials rotated at least once a year.
- **Logs:** security logs kept **12 months** and reviewed at least every 2 weeks. No PII inside the logs.
- **Network:** firewall, network segmentation, IDS/IPS, and a **WAF on anything facing the internet**.
- **Vulnerabilities:** scans **every 30 days**, a **pen test every 365 days**, critical issues fixed within 7 days and high-risk within 30.
- **Incidents:** notify Amazon within **24 hours**.
- **Retention:** keep PII no longer than **30 days after delivery**. This means labels and packing slips stored in object storage need automatic deletion rules.
- **Hosting:** there is no rule requiring AWS. What matters is how much of the list above each host gives you ready-made versus what you build yourself.

---

## 1. Full-stack hosting options

### Price basis (all fetched on 2026-09-23 unless marked unverified)
- **Fargate** (pulled from AWS's pricing data; aws.amazon.com/fargate/pricing):
  - ARM: $0.03238 per vCPU-h and $0.00356 per GB-h, which is **$23.64 per vCPU-month and $2.60 per GB-month**.
  - x86: $0.04048 per vCPU-h and $0.004445 per GB-h.
  - Imaging on ARM costs 2×0.03238 + 8×0.00356 = **$0.0932 per hour**.
  - Fargate Spot is "up to 70% off".
- **NAT gateway** (aws.amazon.com/vpc/pricing): **$0.045/h ($32.85/mo) plus $0.045 per GB processed**. A public IPv4 address is $0.005/h ($3.65/mo).
- **Load balancer:** $0.0225/h ($16.43/mo) plus $0.008 per capacity-unit-hour. The AWS data file labels the $0.0225 row "Network", so the Application Load Balancer hourly rate needs a final check.
- **Internet egress:** $0.09/GB for the first 10 TB, with 100 GB/mo free.
- **CloudFront flat-rate plans** (aws.amazon.com/cloudfront/pricing), no overage charges:
  - Free $0: 1M requests, 100 GB.
  - Pro **$15**: 10M requests, 50 TB, 50 GB S3 credit.
  - Business $200: 125M requests, 1 TB S3 credit, private VPC origins, SLA.
  - Every plan includes WAF, DDoS protection, Route 53 DNS and a TLS certificate.
- **KMS:** $1 per key per month plus $0.03 per 10k requests.
- **CloudWatch Logs:** $0.50/GB ingested and $0.03 per GB-month stored.
- **RDS, ElastiCache, S3:** listed in §2–§4.

### Line-item math per option

**(1) AWS: ECS Fargate (ARM) + RDS + ElastiCache Valkey + S3 + CloudFront**

| Item | Pilot | Growth | Scale |
|---|---|---|---|
| Fargate | 2×23.64+4×2.60 + 23.64+2×2.60 + 60×0.0932 = **92** | 94.55+20.8 + 70.9+15.6 + 22.4 = **224** | 189.1+41.6 + 141.8+31.2 + 55.9 = **460** |
| RDS | t4g.medium single-AZ 47.45 + 20 GB×0.115 = **50** | m7g.large Multi-AZ 246 + 100 GB×0.23 = **269** | r7g.xlarge Multi-AZ 698 + 500×0.23 + ~19 backup = **832** |
| Valkey | t4g.micro **9** | 2× t4g.small **37** | 2× m7g.large **185** |
| S3 + requests | **3** | **43** | **215** |
| NAT | 1 gateway 32.85 + ~50 GB×0.045 = **35** | 2 gateways 65.7 + 300 GB = **79** | 2 gateways + 1.5 TB = **135** |
| Load balancer | ~25 | ~30 | ~50 |
| CloudFront flat plan | Free **0** | Pro **15** | Pro **15** (Business **200** if over 10M requests) |
| KMS + Secrets Manager | 8 | 12 | 20 |
| Logs | 10 | 30 | 80 |
| Public IPv4 | 11 | 15 | 20 |
| ECR | 2 | 3 | 5 |
| Security tooling (GuardDuty, Config, Security Hub, Inspector) — rough estimate, unverified | 20 | 50 | 120 |
| **Total** | **≈ $265** | **≈ $810** | **≈ $2,140** |

Cost levers on AWS:
- Replace the NAT gateway with an EC2 NAT instance ("fck-nat"; SST supports it with `nat: "ec2"`). This costs about $3–6/mo, but the EC2 price is unverified.
- Add a free S3 gateway endpoint so S3 traffic skips the NAT.
- Run imaging on Fargate Spot, saving up to 70%: about $56 → $17 at scale.
- At scale, a 1-year Compute Savings Plan (about 20% on Fargate) and a reserved RDS instance (about 30–35%) bring the total to **about $1.8k**. Both discount percentages are unverified.

**(2) AWS with Aurora Serverless v2** (same stack, with Aurora in place of RDS; Aurora figures in §2)
- **Pilot:** 265 − 50 + 93 = **≈ $310**
- **Growth:** 810 − 269 + 594 = **≈ $1,135**
- **Scale:** 2,140 − 832 + 2,017 = **≈ $3,325**

**(3) GCP: Cloud Run + Cloud SQL + Memorystore + GCS**
- **Cloud Run price** (cloud.google.com/run/pricing, instance-based billing): $0.000018 per vCPU-second and $0.000002 per GiB-second. That is **$47.30 per vCPU-month and $5.26 per GiB-month**, and imaging costs $0.187/h.
  - Free tier: 240k vCPU-seconds plus 450k GiB-seconds, worth about $5.
  - A 1-year Cloud Run commitment gives 17% off.
  - Cloud Run is about **2x Fargate ARM per vCPU**.
- **Compute:** pilot 3×47.30 + 6×5.26 + 60×0.187 − 5 = **180**; growth **444**; scale **917**.
- **Cloud SQL** (Enterprise edition): $0.0413 per vCPU-h and $0.007 per GiB-h, doubled for HA. SSD is $0.17/GiB-month, or $0.34 with HA.
  - Pilot, 1 vCPU / 3.75 GB: 30.15 + 19.16 + 3.4 = **53**
  - Growth, 2 vCPU / 8 GB with HA: 202.4 + 34 + ~5 backups = **241**
  - Scale, 4 vCPU / 32 GB with HA: 568 + 170 + ~32 = **770**
- **Memorystore Valkey:** shared-core-nano is $0.0318/h. Pilot **23**; growth, 2 nodes, **46**; scale, 2× standard-small at $0.1425/h, **208**.
- **GCS:** $0.020/GiB. Pilot 3, growth 36, scale 182.
- **Egress:** Premium tier is $0.12/GiB for the first TiB, then $0.11. Pilot 12, growth 60, scale 1024×0.12 + 1024×0.11 = **236**.
- **Load balancer + Cloud Armor WAF:** about 30 / 40 / 60 (unverified).
- **Keys, logs and miscellaneous:** 10 / 30 / 80.
- **Total: pilot ≈ $310, growth ≈ $900, scale ≈ $2,450** (about $2,300 with the Cloud Run commitment).
- **Advantage over AWS:** Cloud Run reaches private IPs over the VPC without a NAT gateway.

**(4) Fly.io + Managed Postgres + Tigris**
- **Machines** (fly.io/pricing): performance-1x (2 GB) $31, performance-2x (4 GB) $62, performance-4x (8 GB) $124, performance-6x (12 GB) $186, performance-8x (16 GB) $248. Extra RAM is $5/GB. Egress is $0.02/GB in North America and Europe; a dedicated IPv4 is $2.
- **Imaging:** a performance-2x plus 4 GB extra is $82/mo if always on, or $0.112/h run on demand.
- **Managed Postgres** (docs.fly.io, mpg page): Starter (shared-2x, 2 GB) $72, Launch (performance-2x, 8 GB) $282, Scale (performance-4x, 32 GB) $962. Storage is $0.28/GB, the maximum is 1 TB, and HA is included.
- **Pilot:** compute 62+31+6.7 = 99.7; database 72+5.6 = 77.6; self-hosted Valkey machine 7; Tigris 4; egress 1; IPv4 2. **Total ≈ $191.**
- **Growth:** compute 124+93+27 = 244; database 282+28 = 310; Valkey 33; Tigris 38; egress 4; IPv4 2; Standard support 29. **Total ≈ $660.**
- **Scale:** compute 248+186+67 = 501; database 962+140 = 1,102; Valkey pair 84; Tigris 182; egress 10; IPv4 2; support 29. **Total ≈ $1,910.**
- **Discount:** reserved machine blocks give 40% off compute.

**(5) Railway** (railway.com/pricing)
- **Price basis:** CPU about $20 per vCPU-month; RAM about $10 per GB-month; volumes $0.15/GB; egress $0.05/GB; buckets $0.015/GB with free egress. Pro plan $20/mo, credited against usage.
- **How it bills:** Railway charges for resources **actually used**. I assumed always-on services average 35% CPU and 75% RAM.
- **Pilot:** 1.05 vCPU → $21; 4.5 GB → $45; imaging (120 vCPU-h × $0.0274 + 480 GB-h × $0.0137) → $9.9; Postgres container $24; Redis $5; bucket $0.75; egress $5. **Total ≈ $111.**
- **Growth:** 49 + 105 + 39.5 + Postgres 111 + Redis 15 + bucket 15.4 + egress 25. **Total ≈ $360.**
- **Scale:** 98 + 210 + 98.6 + Postgres with a self-built replica 918 + Redis 50 + bucket 76.8 + egress 25. **Total ≈ $1,480.** That excludes the Enterprise contract (custom price, unverified), which is where HIPAA BAAs and compliance features live.

**(6) Render** (render.com/pricing; full price table retrieved)
- **Price basis:**
  - Workspace plans: Pro $25; Scale $499 (HIPAA workspaces, 1 TB bandwidth included, organization audit logs).
  - Compute instances: 1c-2g $25, 2c-4g $85, 2c-8g $135, 4c-8g $175, 8c-16g $300.
  - Workflows: 2c-8g at $0.70/h.
  - Postgres: 1c-4g $55, 2c-8g $100, 4c-32g $350. Storage $0.30/GB. I assumed HA doubles the price (unverified).
  - Key Value: 256 MB $10, 1 GB $32, 5 GB $135.
  - Bandwidth: $0.15/GB over the plan's included amount.
- **Pilot:** 85 + 25 + imaging workflows 60 h×0.70 = 42 + Postgres 60.7 + Key Value 10 + R2 1 + bandwidth 75 GB×0.15 = 11 + Pro 25. **Total ≈ $260.**
- **Growth:** 175 + 110 + imaging always-on 2c-8g 135 (cheaper than workflows' $168) + Postgres HA 260 + Key Value 32 + R2 20 + bandwidth 26 + Pro 25. **Total ≈ $785.**
- **Scale:** 300 + 260 + 135 + Postgres HA (700 + 300 storage) = 1,000 + Key Value 135 + R2 137 + Scale plan 499. **Total ≈ $2,465**, or **≈ $2,065 on the Pro plan**.
- **Instance size limit:** services max out at 12 CPU / 96 GB, which is fine for imaging.

**(7) Vercel for the web app + another backend** (vercel.com/pricing)
- **Price basis:** Pro $20 per seat. Fluid compute is $0.128 per active CPU-hour and $0.0106 per GB-hour of memory.
- **My estimate for Vercel usage:** pilot $20, growth about $60, scale about $200.
- **Arithmetic:** remove about half of the web+api container from the backend, then add Vercel.
  - With Fly: 191 − 31 + 20 = **$180**; 660 − 62 + 60 = **$658**; 1,910 − 124 + 200 = **$1,986**.
  - With AWS: **≈ $256 / $812 / $2,225**.
- **Drawbacks:**
  - WebSockets still need your own backend.
  - Server-rendered pages would handle PII, so Vercel enters audit scope.
  - A static egress IP or private connection to AWS needs Enterprise "Secure Compute" (custom price, unverified).

**(8) Hetzner + Coolify** (self-managed)
- **Server prices after the 15 June 2026 increase** (docs.hetzner.com price-adjustment page), US Ashburn / Hillsboro per month:
  - CCX13 (2 dedicated vCPU / 8 GB): **$50.99**, up from $19.99
  - CCX23 (4 / 16): **$102.99**
  - CCX33 (8 / 32): **$165.99**
  - CCX43 (16 / 64): **$329.49**
  - EU-only: CAX41 (16 ARM / 32 GB) **$48.49**; CX43 **$18.49**
- **Other prices:**
  - Coolify: self-hosted free, or $5/mo on Coolify Cloud.
  - Hetzner Object Storage: about $7.41/TB, EU only (from getdeploying.com, unverified).
  - Load balancer: about $8.55 (unverified).
  - Backups: +20% of the server price (from memory, unverified).
- **Pilot:** CCX23 for the app, workers, Redis and imaging, $103; plus CCX13 for Postgres, $51; backups about 31; R2 2; Coolify 5. **Total ≈ $192.** In the EU on CAX servers it would be about $90.
- **Growth:** 2× CCX23 for the app, $206; CCX13 for imaging, $51; a primary + replica CCX23 pair for Postgres, $206; load balancer 9; backups 41; R2 20; Coolify 5. **Total ≈ $540.**
- **Scale:** 2× CCX33 for the app, $332; CCX23 for workers, $103; CCX23 for imaging, $103; 2× CCX43 for Postgres, $659; CCX13 for Redis, $51; load balancer 9; offsite backups 30; R2 137; Coolify 5. **Total ≈ $1,430**, plus about $30 for monitoring.

**(9) DigitalOcean App Platform + Managed DB**
- **App Platform** (docs.digitalocean.com):
  - Shared instances: 2 vCPU / 4 GB $50; 1 vCPU / 2 GB $25.
  - Dedicated instances: 2/4 $78, 2/8 $98, 4/8 $156, 4/16 $196, 8/32 $392.
  - Bandwidth overage $0.02/GB.
- **Managed Postgres** (basic tier): 2 GiB / 1 vCPU $30.45; 4 GiB / 2 vCPU $60.90; 8 GiB / 4 vCPU $122.10; 16 GiB / 6 vCPU $244.35. Extra storage $0.215/GiB. I priced a standby node at the same price as the primary (unverified).
- **Valkey:** 1 GiB $15, 2 GiB $30, 4 GiB $60.
- **Spaces:** $5/mo includes 250 GiB and 1 TiB of transfer; then $0.02/GiB stored and $0.01/GiB transferred.
- **Pilot:** 50 + 25 + imaging always-on 98 + Postgres 30.45 + Valkey 15 + Spaces 5. **Total ≈ $223.**
- **Growth:** 156 + 117 + 98 + Postgres with standby 244 + Valkey pair 60 + Spaces 20.5. **Total ≈ $696.**
- **Scale:** 2× 4/8 instances 312 + 234 + 98 + Postgres 16 GiB with standby plus extra storage 536 + Valkey 4 GiB pair 120 + Spaces 102 + transfer 10. **Total ≈ $1,412.**
- **Drawback:** imaging can't scale to zero here, so you pay for it all month.

### Summary table: full stack

"Ops" is the ongoing operations work for a solo developer, from 1 (least) to 5 (most).

| Option | Pilot | Growth | Scale | Pros | Cons | Compliance fit | Ops (1–5) |
|---|---|---|---|---|---|---|---|
| **AWS: Fargate + RDS + Valkey + S3 + CloudFront** | ~$265 | ~$810 | ~$2,140 (~$1.8k with commitments) | Everything the DPP needs is built in: KMS, CloudTrail (12-month logs), WAF, Inspector, private subnets. Graviton and Spot for imaging. Serves Amazon's own reviewers well. | NAT, load balancer and IPv4 fees ($60–200/mo). IAM and VPC complexity. | **Excellent** | 4 (3 with SST) |
| AWS + Aurora Serverless v2 | ~$310 | ~$1,135 | ~$3,325 | Fast failover, storage copied across 3 zones, can scale to zero in dev. | About 2x RDS when load is steady. Extra I/O charges. | Excellent | 3.5 |
| GCP: Cloud Run + Cloud SQL | ~$310 | ~$900 | ~$2,450 | No NAT needed for private traffic. Good WebSocket support. Cloud KMS keys and audit logs. | Compute about 2x Fargate ARM. $0.12/GB egress. | Very good | 3 |
| Fly.io + MPG + Tigris | ~$191 | ~$660 | ~$1,910 | Cheap, simple, $0.02/GB egress, machines per second, private networking. | Managed Postgres docs say patches and version upgrades are "not there yet"; 1 TB database cap. No customer-managed keys. Self-run Redis. | Fair | 2.5 |
| Railway | ~$111 | ~$360 | ~$1,480 (plus Enterprise) | Cheapest; pay only for what's used; buckets with free egress. | Postgres and Redis are containers you run yourself (no managed HA or PITR). Compliance needs Enterprise; audit logs are an Enterprise feature. | Weak (Pro) / Fair (Enterprise) | 1.5 (to start) → 3 (running a database) |
| **Render** | ~$260 | ~$785 | ~$2,065 (Pro) / ~$2,465 (Scale) | Managed Postgres with PITR and HA. SOC 2 Type II and ISO 27001. AWS PrivateLink ($30). Audit logs. HIPAA workspaces on Scale. | No object storage (bring R2 or S3). $0.15/GB bandwidth. No customer-managed keys. | Good | 1.5 |
| Vercel web + Fly/AWS backend | ~$180 / $256 | ~$660 / $812 | ~$1,990 / $2,225 | Best Next.js developer experience, edge cache. | No WebSockets. Another vendor in PII scope. Private link to AWS is Enterprise-only. | Fair | 2.5–4 |
| Hetzner + Coolify | ~$192 (EU ~$90) | ~$540 | ~$1,430 | Cheapest raw compute; lots of included traffic. | You run Postgres HA, backups, encryption, KMS, patching and a WAF yourself. No object storage in US regions. ISO 27001 only (SOC 2 availability unverified). June 2026 price rise. | Poor–Fair (do it yourself) | 5 |
| DigitalOcean App Platform + Managed DB | ~$223 | ~$696 | ~$1,412 | Flat, predictable pricing. Managed Postgres and Valkey with standby. Cheap Spaces. | Imaging can't scale to zero. No customer-managed KMS. Less mature than AWS. | Fair–Good | 2 |

---

## 2. Managed Postgres alone
Sizes are the standard ones above: pilot 10 GB small, growth 80 GB with HA, scale 400 GB with HA.

**Price basis:**
- RDS PostgreSQL on-demand, pulled from AWS's pricing data:
  - t4g.medium: $0.065/h single-AZ, $0.129/h Multi-AZ
  - m7g.large: $0.337/h Multi-AZ
  - r7g.xlarge: $0.956/h Multi-AZ
  - m7g.2xlarge: $1.348/h Multi-AZ
  - gp3 storage: $0.115/GB-month single-AZ, $0.23 Multi-AZ. Backup storage $0.095/GB.
- Aurora Serverless v2: **$0.12 per ACU-hour ($87.60/mo)** standard; $0.16 on the I/O-Optimized option. Storage $0.10/GB plus $0.20 per million I/Os, or $0.225/GB on I/O-Optimized.
- Neon: compute on the Launch plan $0.106 per compute-unit-hour and on the Scale plan $0.222; storage $0.35/GB-month; restore history $0.20/GB-month. One compute unit is about 4 GB RAM (from memory).
- Supabase (supabase.com/pricing and its docs): Pro $25; Team $599 (needed for SOC 2); compute Micro $10, Small $15, Medium $60, Large $111 (XL $210, 2XL $410, 4XL $960 are from memory, unverified); disk $0.125/GB after 8 GB; PITR add-on about $100 (unverified).
- Crunchy Bridge (docs.crunchybridge.com): Standard-8 $140, Standard-32 $560, Hobby-4 $70; storage $0.10/GB; HA doubles the price. Snowflake bought Crunchy in 2025, and I couldn't confirm whether it still takes new customers.
- DigitalOcean, Fly and Cloud SQL: prices as in §1.

| Option | Pilot | Growth | Scale | Pros | Cons | Compliance | Ops |
|---|---|---|---|---|---|---|---|
| **RDS PostgreSQL** | t4g.medium 47.45 + 2.30 = **$50** (Multi-AZ $99) | m7g.large Multi-AZ 246 + 23 = **$269** | r7g.xlarge Multi-AZ 698 + 115 + 19 = **$832** (about $560 with a reserved instance, unverified) | Mature; KMS encryption; PITR up to 35 days; IAM authentication; stays inside your VPC. | Multi-AZ doubles the price. | Excellent | 2 |
| Aurora Serverless v2 | ~1 ACU: 87.6 + 1 + ~4 I/O = **$93** | writer 4 ACU 350 + reader 2 ACU 175 + 8 + ~60 I/O = **$594** | writer 12 ACU 1,051 + reader 6 ACU 526 + 40 + ~400 I/O = **$2,017** (I/O-Optimized ≈ $2,190) | Storage copied 6 ways; failover under 30 s; scale to zero for dev. | Expensive under steady load; I/O charges hard to predict. | Excellent | 2 |
| Neon (Scale plan, needed for SOC 2) | 1 CU×730×0.222 = 162 + 3.5 = **$166** (Launch plan $81) | 2 CU = 324 + 28 + 16 = **$368** | 8 CU = 1,296 + 140 + 40 = **$1,476** | Branches for every PR; compute failover without paying for a standby. | Expensive storage ($0.35/GB); private link only on Scale ($0.01/GB); cold starts. | Good (SOC 2 and HIPAA at no extra cost on Scale) | 1 |
| Supabase | Pro 25 + Small 15 − 10 credit + 1.5 = **$31.5** | Pro: 25 + 101 + 11.5 + 100 PITR = **$238**; Team (for SOC 2) = **$811** | Team 599 + 2XL 400 + 61.5 + 100 = **$1,160** | Cheap at the start; extras like auth and storage. | SOC 2 needs Team ($599); HA standby is Enterprise-only (unverified). | Good (Team) | 1.5 |
| Crunchy Bridge | Standard-8 140 + 2 = **$142** (Hobby $72, not for production) | Standard-8 with HA = **$300** | Standard-32 with HA 1,120 + 100 = **$1,220** | Postgres specialists; runs in AWS. | Future uncertain after the Snowflake deal. | Good | 1.5 |
| DigitalOcean Managed | **$30–61** | 8 GiB + standby = **$244** | 16 GiB + standby + extra storage = **$536** | Cheapest managed HA option. | Smaller instance sizes; encryption at rest but no customer-managed keys. | Fair–Good | 1.5 |
| Fly MPG | **$78** | **$310** | **$1,102** | HA included. | Patches not yet supported; 1 TB cap. | Fair | 2 |
| Cloud SQL | **$53** | **$241** | **$770** | Customer-managed keys; about 10% cheaper than RDS. | GCP only. | Excellent | 2 |
| Render Postgres | **$61** | **$260** | **~$1,000** | Simple; PITR included. | Storage $0.30/GB. | Good | 1 |

**Recommendation: RDS PostgreSQL**, single-AZ for the pilot and Multi-AZ from growth onward. Use Neon only for per-PR preview branches if you want them.

---

## 3. Redis / Valkey alone

**Two BullMQ constraints matter here:**
- BullMQ needs `maxmemory-policy noeviction`.
- BullMQ sends a lot of commands (blocking pops, stalled-job checks). Services priced per command get expensive: Upstash pay-as-you-go at an estimated 30–90M commands/month would cost $60–180.

**Price basis:**
- ElastiCache Valkey nodes: t4g.micro $0.0128/h, t4g.small $0.0256/h, m7g.large $0.1264/h. Valkey Serverless: $0.084 per GB-hour plus $0.0023 per million ECPUs.
- Upstash: pay-as-you-go $0.2 per 100K commands; fixed 250 MB plan $10. The **"Prod Pack" is +$200/mo per database** and is required for encryption at rest, SOC 2 and multi-zone HA.
- Redis Cloud: Essentials from about $5/mo; Pro from about $200/mo minimum. Only Pro has private connectivity.
- Memorystore, DigitalOcean, Render and Railway: prices as in §1.

| Option | Pilot | Growth | Scale | Pros | Cons | Compliance | Ops |
|---|---|---|---|---|---|---|---|
| **ElastiCache Valkey (nodes)** | t4g.micro **$9** | 2× t4g.small **$37** | 2× m7g.large **$185** | Inside your VPC; KMS encryption at rest; TLS; cheapest managed HA. | AWS only. | Excellent | 1.5 |
| ElastiCache Valkey Serverless | about $6 + ECPUs | ~$20–40 | ~$100+ | No sizing decisions. | BullMQ's blocking commands and cluster hash-tags need testing (unverified). | Excellent | 1 |
| Upstash | $10 fixed plan; **$210 with Prod Pack** | ~$220 (unverified) | ~$300 (unverified) | Serverless; REST API. | Per-command billing is bad for BullMQ; compliance costs $200/mo. | Good (only with Prod Pack) | 1 |
| Redis Cloud | ~$5–10 (unverified) | ~$30–60 on Essentials, or $200 on Pro (unverified) | ~$200–400 on Pro (unverified) | Official Redis. | Private networking only on the $200+ Pro plan. | Good | 1 |
| Railway Redis | ~$5 | ~$15 | ~$50 | Cheap. | A container you run; no HA; no guaranteed encryption at rest. | Weak | 2 |
| Memorystore / DigitalOcean / Render | $23 / $15 / $10 | $46 / $60 / $32 | $208 / $120 / $135 | Managed. | Tied to their platform. | Good / Fair / Good | 1 |

**Recommendation: ElastiCache Valkey nodes.** Start with one t4g.micro for the pilot and add a replica from growth.

---

## 4. Object storage alone
Uses the request and egress volumes from the assumptions table.

**Price basis:**
- **S3:** $0.023/GB (first 50 TB); PUT $0.005 per 1k; GET $0.0004 per 1k; Infrequent Access $0.0125/GB; internet egress $0.09/GB after 100 GB free.
- **R2:** $0.015/GB; Class A $4.50 per million; Class B $0.36 per million; **no egress fees**.
- **Backblaze B2:** **$6.95/TB**; free egress up to 3x stored data; transactions free.
- **Tigris:** $0.02/GB; $0.005 per 1k Class A; $0.0005 per 1k Class B; no egress fees.
- **DigitalOcean Spaces:** $5 for 250 GiB + 1 TiB transfer, then $0.02/GiB stored and $0.01/GiB transferred.
- **GCS:** $0.020/GiB and $0.12/GiB egress.

| Option | Pilot | Growth | Scale | Pros | Cons | Compliance | Ops |
|---|---|---|---|---|---|---|---|
| **S3 + CloudFront Pro ($15)** | 1.15 + 5 + 1.2 + 0 = **$7** | 23.55 + 15 + 4 + 15 = **$58** (without CloudFront, egress adds $36 → $79) | 117.8 + 75 + 20 + 15 = **$228** (without CloudFront: $388) | KMS encryption; Object Lock; lifecycle rules for the 30-day PII deletion; free gateway endpoint; access logs. | Egress fees unless you use the CloudFront flat plan. | Excellent | 1 |
| Cloudflare R2 | ~$1 | 15.4 + 9 + 0 = **$24** | 76.8 + 63 + 14.4 = **$154** | No egress fees; S3-compatible API. | Outside your VPC; no customer-managed keys; a separate vendor for PII. | Good (SOC 2) | 1 |
| Backblaze B2 | ~$0.35 | **$7** | **$35** | Cheapest by far. | Weaker performance; no KMS; server-side encryption only. | Fair | 1.5 |
| Tigris | ~$7 | ~$40 | ~$202 | No egress fees; global; native on Fly. | Newer company. | Fair–Good | 1 |
| GCS | ~$13 | ~$100 | ~$433 | Customer-managed keys. | $0.12/GB egress. | Excellent | 1 |
| DigitalOcean Spaces | $5 | $20.5 | $113 | Flat pricing; no request fees. | Basic IAM. | Fair | 1 |
| Hetzner Object Storage | ~$7 | ~$7 | ~$38 (unverified) | Cheap. | EU only. | Fair | 2 |

S3 lifecycle rule to Infrequent Access after 30 days, at scale: 4,096 GB×0.0125 + 1,024 GB×0.023 = **$75** instead of $118.

**Recommendation:**
- **On AWS:** use S3 with KMS encryption behind the CloudFront flat-rate plan. At 2 TB of egress, CloudFront Pro makes R2's zero-egress pricing irrelevant.
- **Keep PII artifacts** (labels, packing slips) in S3 with a 30-day expiry rule.
- **Off AWS:** use R2, or B2 for cold archives.

---

## 5. Infrastructure as code

| Tool | Cost | Pros | Cons | Fit for InvAI |
|---|---|---|---|---|
| **SST v3** | Free, open source; state kept in your own S3 (Console pricing unverified; sst.dev/pricing didn't render) | TypeScript. Ready-made components for `Vpc` (with the `nat:"ec2"` cheap NAT option), `Cluster`/`Service` on Fargate, `Postgres` on RDS, `Redis` on ElastiCache, `Bucket`, `Router`/CloudFront. Built on Pulumi, so any Pulumi provider works. Good local dev loop. | Components are opinionated; sometimes you have to drop down to raw Pulumi. | **Best for a solo TypeScript developer on AWS** |
| Terraform / OpenTofu | Free; HCP Terraform free tier (limits unverified) | Most mature; providers for AWS, Hetzner, DigitalOcean, Fly and Cloudflare. | HCL; more boilerplate; Terraform's BUSL licence. | Good if you might leave AWS |
| Pulumi | Free (Individual tier or your own S3 backend); Essentials $40/mo | TypeScript; multi-cloud; secrets with Pulumi ESC. | Pulumi Cloud charges per resource ($0.18–0.37 each per month). | Good |
| AWS CDK | Free | TypeScript; first-party AWS. | CloudFormation is slow and drift-prone; AWS only. | Acceptable |

**Recommendation: SST v3** with state in your own S3 bucket, which costs about $0.

---

## 6. Recommended phased path

**1. Now → pilot (3 shops): about $230–265/mo**
- AWS us-east-1, set up with SST v3. Graviton Fargate tasks: web+api (2/4) and workers (1/2).
- Imaging runs as Fargate tasks started on demand by the BullMQ worker (ECS RunTask), or as a service that scales from zero, on Spot.
- RDS t4g.medium single-AZ, Valkey t4g.micro, S3 with KMS, and the CloudFront Free or Pro plan (includes WAF).
- One NAT instance (fck-nat) plus an S3 gateway endpoint instead of NAT gateways, to save about $30.
- **Before the first Amazon PII pull**, switch on:
  - CloudTrail and CloudWatch log retention of at least 12 months (export to S3 Glacier)
  - GuardDuty, Security Hub and Inspector (the 30-day scans)
  - KMS keys that are yours (customer-managed), with rotation
  - A 30-day S3 expiry rule and a Postgres job that purges old PII
- Budget a pen test separately (my rough estimate: about $3–10k/year, unverified).

**2. At about 10 shops, or before the SP-API restricted-role review (growth): about $800/mo**
- Move RDS to m7g.large Multi-AZ and add a Valkey replica.
- Use two NAT gateways, or keep the NAT instance with Auto Scaling.
- Add a second web/api task and move to the CloudFront Pro plan.

**3. At about 50+ shops (scale): about $2.1k/mo on demand, about $1.8k/mo with commitments**
- 1-year Compute Savings Plan on Fargate and a reserved RDS instance (r7g.xlarge Multi-AZ).
- S3 lifecycle rules to Infrequent Access.
- Keep imaging on Spot.
- Consider Aurora only if you need read replicas or failover under 30 seconds.

**Alternatives**
- **If you don't want to learn AWS right now:** start on **Render Pro** (about $260 → $785) with R2 for storage and Render Postgres. Use PrivateLink to reach AWS later. Move to the $499 Scale plan when the audit comes, or migrate to AWS at growth. Avoid Fly MPG and Railway for anything holding Amazon PII.
- **Hetzner + Coolify:** only worth it if cost dominates everything else and you're willing to build compliance yourself. After the 2026 price rise, US scale saves about $700/mo against AWS, which is less than one pen-test cycle plus a few days a month of ops time.

---

## Prices I couldn't verify
- **AWS:** the load-balancer hourly rate (the AWS data file labels the $0.0225 row "Network"); discount levels for Savings Plans and reserved instances; the monthly cost of GuardDuty, Config, Security Hub and Inspector (my estimate); the EC2 price for a fck-nat instance; S3's 100 GB free egress (from memory).
- **Cloudflare R2:** free-tier amounts (from memory).
- **GCP:** load balancer and Cloud Armor costs; Cloud KMS key price; GCS Class A/B request prices.
- **Supabase:** XL, 2XL and 4XL prices; PITR at about $100; HA standby being Enterprise-only.
- **Upstash:** fixed-plan prices above 250 MB.
- **Redis Cloud:** Essentials sizes above the entry tier.
- **Railway:** Enterprise pricing and which compliance features it includes.
- **Render:** HA Postgres being priced at 2x.
- **DigitalOcean:** standby node pricing.
- **Hetzner:** object storage, load balancer, volume and backup prices; SOC 2 availability; traffic allowances in US regions.
- **Crunchy Bridge:** status after the Snowflake acquisition.
- **Vercel:** Secure Compute pricing; my Vercel usage estimates.
- **Neon:** the compute-unit-to-RAM ratio.
- **SST:** Console pricing.
- **Pen test:** cost.
- **Utilization assumptions:** Railway figures assume 35% CPU and 75% RAM use. Request volumes and NAT data volumes are my own assumptions.

**Sources:**
- AWS price files for AmazonECS, AmazonRDS, AmazonElastiCache, AmazonS3, awskms, AWSELB, AWSDataTransfer and AmazonCloudWatch (pricing.us-east-1.amazonaws.com/offers/v1.0/aws/…); aws.amazon.com/vpc/pricing; aws.amazon.com/cloudfront/pricing
- cloud.google.com/run/pricing, /sql/pricing, /memorystore/docs/valkey/pricing, /storage/pricing, /vpc/network-pricing
- fly.io/pricing; docs.fly.io/about/pricing; fly.io/docs/mpg
- railway.com/pricing; docs.railway.com/reference/pricing/plans
- render.com/pricing; vercel.com/pricing
- docs.hetzner.com/general/infrastructure-and-availability/price-adjustment; getdeploying.com/hetzner; coolify.io/pricing
- digitalocean.com/pricing/managed-databases, /spaces-object-storage; docs.digitalocean.com/products/app-platform/details/pricing
- neon.com/pricing; supabase.com/pricing and its compute docs; docs.crunchybridge.com/concepts/plans-pricing
- upstash.com/pricing/redis; redis.io/pricing
- developers.cloudflare.com/r2/pricing; backblaze.com/cloud-storage/pricing; tigrisdata.com/pricing
- pulumi.com/pricing
- sellercentral.amazon.com/mws/static/policy?documentType=DPP

WebSearch was unavailable (session limit reached), so everything above comes from direct page fetches or AWS's pricing data. No files were written apart from scratch data under the session scratchpad.
