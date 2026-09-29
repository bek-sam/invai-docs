# Access-control policy

Written policy for B-10, closing research gap G29
(`invai-docs/research/12-security-quality-playbook.md` §7). This states who can touch what — AWS,
GitHub, the database, the app, and secrets — and the review and offboarding cadence. It is evidence
for the Amazon DPP evidence pack (`.claude/skills/amazon-dpp-evidence-pack/SKILL.md`) and the
Shopify App Store security questionnaire.

Every "not yet" below is a real gap, the same rule the vendor inventory uses
(`invai-docs/compliance/vendor-inventory.md`): **MUST NOT** answer "yes" on a questionnaire for
anything marked `[[OWNER]]` or "not yet" here without new evidence.

## 1. AWS

No AWS account is deployed to yet (`CLAUDE.md`: "MUST NOT run `sst deploy`... without the owner's
explicit go-ahead"; `invai-infra/sst.config.ts` header: "this environment does not have [AWS
credentials]"). Everything in this section is the policy to apply from the first deploy onward,
not a description of a live account.

| Control | Policy | Status |
|---|---|---|
| Root user | Never used for day-to-day work; root credentials are stored offline, root MFA is on, and no access key exists for the root user | `[[OWNER]]` — account not created |
| Human access | AWS SSO (IAM Identity Center), not IAM users with long-lived access keys | `[[OWNER]]` — no account yet |
| MFA | Phishing-resistant MFA on every human account that can reach the AWS console (research 12 §1.5, CISA supply-chain guidance) | `[[OWNER]]` |
| CI/CD access | OIDC role assumption, no long-lived AWS keys in any repo. Already wired in `invai-infra/.github/workflows/deploy.yml` (`permissions: id-token: write`, `aws-actions/configure-aws-credentials@v4` with `role-to-assume`) | **Partly done, code side.** The role ARN in `deploy.yml` is a placeholder (`arn:aws:iam::123456789012:role/invai-deploy`, comment: "replace with the real deploy role before this workflow can run") — creating the real IAM role, its trust policy (audience `sts.amazonaws.com`, subject restricted to this repo and ref) and least-privilege permissions is `[[OWNER]]` |
| Least privilege | Each service (api, worker, imaging) gets its own task role scoped to only the resources SST links it to (`sst.aws.Service({ link: [...] })` in `invai-infra/sst.config.ts` — api/worker link `db, redis, files, ...secrets`; imaging links only `files, redis`); SST generates these roles from `link:` automatically, so keeping `link:` minimal per service **is** the least-privilege control here | Enforced in `invai-infra/sst.config.ts`; verify the generated IAM policy after the first deploy `[[OWNER]]` |
| Data at rest | RDS Postgres storage-encrypted by default (`sst.aws.Postgres` component default, noted in `sst.config.ts` comment), private subnets only (no `public` prop set), field-level encryption for buyer PII on top (`FIELD_ENCRYPTION_KEY`, see §4) | Set in code; unverified against a real deploy |
| Data in transit | ElastiCache/Valkey requires TLS + AUTH by default for this component (`sst.config.ts` comment: "ElastiCache Redis/Valkey clusters from this component require TLS + AUTH"); RDS connections use the standard TLS-capable Postgres driver | Set in code |
| Deletion protection / backup retention | `removal: "retain"` and `protect: true` only when `stage === "production"` (`sst.config.ts` `app()`); **RDS backup retention is not explicitly set**, so it uses the component default — verify it meets the P0 rule (retention ≥ 14 days, 35 in production; `.claude/agents/platform-sre.md` "P0 before any AWS use") before any real deploy | **Gap: retention not explicitly configured. File a card before first deploy.** |
| Access review | Quarterly review of who can reach the AWS console and what they can do (Amazon key-controls guidance, research 12 §1.3) | `[[OWNER]]` — no account, so no review has run; first review is due within 90 days of first deploy (§6) |

## 2. GitHub

8 repos: `invai-contracts`, `invai-ui`, `invai-backend`, `invai-imaging`, `invai-web`,
`invai-floor`, `invai-infra`, `invai-docs`.

| Control | Policy | Status |
|---|---|---|
| Branch protection on `main` | Required status checks (the repo's `ci.yml`), no force-push, no direct deletion. `CLAUDE.md` already treats `main` as protected by convention ("Never force-push, never rewrite pushed history") and `.claude/hooks/guard-bash.py` blocks a local `git push --force` (the `PUSH_RULE` pattern), but branch-protection *rules* are a GitHub repo setting | `[[OWNER]]` — set in each repo's Settings by the owner. **The literal command `gh repo edit <repo>` is on the hook's deny list (`guard-bash.py` line ~71: "repo settings are changed by the owner"), but the actual way branch protection is normally set — `gh api -X PUT repos/<org>/<repo>/branches/main/protection ...` — is not caught by any of the hook's rules today.** Probed directly (T-21-2 review round 1): that exact command returns `rc=0`, i.e. not blocked. This is a real gap, not a documentation error — tracked as `invai-docs/waves/backlog.md` **B-189** ("guard gap: `sst secret set` and branch-protection API calls aren't blocked"), owned by platform-sre + security-reviewer. Until B-189 lands, the only thing stopping an agent from calling that API is this written policy, not a technical control — treat it as owner-only by policy, not by enforcement |
| Who pushes | Per `CLAUDE.md` ("Repos, branches, ownership") and decision `0004`: push straight to `main`, but only after tests pass and an independent review approves; the tech lead pushes after the wave's integration gate, or a solo agent pushes its own reviewed work. No agent pushes ungated work (`invai-docs/team/lessons.md`, 2026-09-26 W8: "a builder once pushed 44 ungated commits") | Enforced by process + `.claude/hooks/guard-bash.py`; **not yet enforced by GitHub branch protection** (same gap as above) |
| Deploy keys | Read-only, one per repo, used only by `invai-infra/.github/workflows/deploy.yml` to check out the sibling repos it builds from (`BACKEND_DEPLOY_KEY`, `IMAGING_DEPLOY_KEY`, `WEB_DEPLOY_KEY`, `FLOOR_DEPLOY_KEY`, `CONTRACTS_DEPLOY_KEY`, `UI_DEPLOY_KEY`) | Referenced in `deploy.yml`; the actual keys and their scoping are `[[OWNER]]` (GitHub secrets, not visible to agents) |
| Environment protection | `deploy.yml` already scopes the job to a GitHub Environment (`environment: ${{ github.event_name == 'push' && 'production' || inputs.stage }}`), which is where required-reviewer and wait-timer rules would attach | The Environments themselves (`staging`, `production`) and any required-reviewer rule on them are `[[OWNER]]` to create in repo Settings |
| Actions pinned by SHA, least `permissions:` | `deploy.yml` sets a top-level `permissions: id-token: write, contents: read` (least privilege) but pins actions by tag (`actions/checkout@v4`), not SHA; the 6 app `ci.yml` files have **no** `permissions:` block at all and also pin by tag | **Open gap**, tracked as research gap G15 (`dependency-and-container-audit` playbook owns closing it) — platform-sre fixes CI/Dockerfiles, this document just states the policy: every `uses:` should be `@<40-char sha> # vX.Y.Z`, every workflow should set `permissions: contents: read` at the top and widen per job only where needed |
| Secret scanning / push protection | GitHub secret scanning and push protection on, on all 8 repos | `[[OWNER]]` — a repo setting; `gh repo edit` is blocked for agents by `.claude/hooks/guard-bash.py` |
| MFA on GitHub | Phishing-resistant MFA for every human account with write access (CISA supply-chain guidance, research 12 §1.5) | `[[OWNER]]` |

## 3. Database roles

Local and CI mirror this exactly (`invai-infra/local/init.sql`, each repo's `ci.yml`); production uses the same
model once the bootstrap step below runs.

| Role | Privilege | Where defined | Used by |
|---|---|---|---|
| `invai` | Table owner. Creates and alters tables (migrations), no RLS applied to it | `invai-infra/local/init.sql` (`POSTGRES_USER=invai`); `MIGRATION_DATABASE_URL` in `invai-backend/src/env.ts` | Migrations, seed, the outbox relay, and cross-tenant jobs — only through `withSystem()`, which every reviewer greps for a justifying comment (research 12 §1.1) |
| `invai_app` | `LOGIN` only, **no `BYPASSRLS`**, owns no tables, granted `SELECT/INSERT/UPDATE/DELETE` on tables and `USAGE/SELECT` on sequences via `ALTER DEFAULT PRIVILEGES` (`local/init.sql`) — so RLS applies to every request it makes | `invai-infra/local/init.sql`; `DATABASE_URL` in `invai-backend/src/env.ts` | The API and worker, for all tenant-owned request paths, through `withTenant(companyId, fn)` |
| **Production gap** | `sst.aws.Postgres` in `invai-infra/sst.config.ts` "only provisions the master (owner) user"; the comment in that file states plainly that nothing there yet creates `invai_app` in RDS the way `local/init.sql` does locally, so today `DATABASE_URL` in the SST config points the app at the **owner** user | **P0 before any AWS use** (`.claude/agents/platform-sre.md`): a bootstrap step — a one-time SQL script run against the instance, from a deploy job or an SST dynamic provider — must create `invai_app` with the same no-`BYPASSRLS` grant before the API is pointed at a real database. `[[OWNER]]` to approve the bootstrap mechanism; platform-sre builds it as a card, not as part of this doc. |

## 4. App roles and permissions

Source of truth: `invai-contracts/src/roles.ts` (`ROLES`, `PERMISSIONS`, `ROLE_PERMISSIONS`).
Reviewers re-check this table against that file, since it is generated by hand, not derived.

- **Shop roles** (`SHOP_ROLES`): `owner`, `admin`, `office`, `designer`, `presser`, `packer`,
  `receiver`.
- **Vendor organizations** have exactly one role: `vendor` (`ROLES` includes it; a vendor org's
  members are always `vendor`, per the file's top comment).
- **Floor roles** (`FLOOR_ROLES`, PIN + station login, not a web session): `presser`, `packer`,
  `receiver`.
- **Owner-only permissions** (`OWNER_ONLY` in `roles.ts`): `billing.manage`, `org.export`,
  `org.delete` — `admin` gets every other shop permission (`SHOP_ALL.filter(p =>
  !OWNER_ONLY.includes(p))`) but never these three.
- **Least privilege by role** (from `ROLE_PERMISSIONS` in `roles.ts`):
  - `office`: broad operational access (orders, channels, production build/QC/receive, vendors,
    inventory read, shipping, finance read, AI listings) but not `billing.manage`, `org.export`,
    `org.delete`, or `inventory.adjust`/`purchasing.receive`/`production.override`.
  - `designer`: catalog and personalization management, AI listings, no shipping, finance or
    inventory access at all.
  - `presser`/`packer`/`receiver`: narrow, floor-scoped permission sets, all three sharing
    `production.scan` (`invai-contracts/src/roles.ts` `PRESSER`/`PACKER`/`RECEIVER` arrays,
    lines 175-209). Only `presser` and `packer` also have `production.qc` — `receiver` does not;
    it gets `production.receive` instead. `packer` adds `shipping.read`/`shipping.buy`; `receiver`
    adds `inventory.read`/`inventory.adjust`/`inventory.count` and
    `purchasing.read`/`purchasing.receive`.
  - `vendor`: `vendor_portal.read`/`update`, `team.read`/`manage` (its own org's team only, scoped
    by tenant), `files.read`, `alerts.read` — no access to any shop-side permission.
- **Enforcement**: every oRPC procedure declares a `permission` in its contract `.meta`; the backend
  checks `hasPermission(role, permission)` (`invai-contracts/src/roles.ts`) via the permission
  guard. `invai-backend/src/api/authz.test.ts` (owned by `backend-foundation`) walks every procedure as anonymous,
  no-permission, floor, station-only and vendor sessions — this is the automated check that keeps
  this section true; a new procedure with `permission: "none"` outside `me.*`/`floor.*` fails CI
  (research 12 §1.3).
- **Field-level PII**: `shipTo`, buyer email and phone are returned only under `orders.manage`
  (research 12 §1.3); this is enforced in backend service code, not visible in `roles.ts` alone.
- **Owner-only actions get an audit trail**: role/permission changes and owner transfers write an
  `audit_log` row with `from`/`to` values (`invai-backend/src/db/schema/tenancy.ts` `auditLog`
  table, append-only by migration-level grant, research 12 §1.10).

## 5. Secret storage

| Where | What lives there | Notes |
|---|---|---|
| SST Secrets (`invai-infra/sst.config.ts`) | `BetterAuthSecret`, `FieldEncryptionKey` (both required in SST — "deploy fails loudly if unset"), `AnthropicApiKey`, `EasyPostApiKey`, `ShopifyApiKey`, `ShopifyApiSecret` (optional *in SST*, empty string default) | `sst secret set <Name> <value> --stage <stage>`, run by `[[OWNER]]` (blocked for agents by `.claude/hooks/guard-bash.py`'s `sst deploy/remove` rule, but see the gap noted below — `sst secret set` itself is not on the hook's deny list) |
| **"Optional in SST" is not the same as "safe to leave unset in production."** `ANTHROPIC_API_KEY`, `EASYPOST_API_KEY`, `SHOPIFY_API_KEY`, `SHOPIFY_API_SECRET` (plus `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `SMTP_URL`, `MAIL_FROM`, `IMAGING_SHARED_SECRET`) are all in `PRODUCTION_KEYS` (`invai-backend/src/env.ts:174-183`); production **refuses to start** if any is missing, unless `ALLOW_MOCKS=true` is explicitly set for a demo/staging stage only (`env.ts:193-199`) — there is no silent "falls back to a safe mock" behavior in production. | — |
| **Not yet SST-managed** | `EASYPOST_WEBHOOK_SECRET`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `INTERNAL_ADMIN_TOKEN`, **and three more that this table previously missed: `IMAGING_SHARED_SECRET` (`env.ts:54,182`, a `PRODUCTION_KEYS` entry — used to authenticate backend→imaging calls), `FLOOR_TOKEN_SECRET` (`env.ts:61`, signs every floor PIN hash and station session — see §6.1 step 3 of `incident-response.md`), and `SMTP_URL`/`MAIL_FROM` (`env.ts:112-113`, `SMTP_URL` carries mail-relay credentials)** — all read from plain env vars in `invai-backend/src/env.ts` with no corresponding `sst.Secret` in `sst.config.ts` | **Gap**, matches `invai-docs/compliance/vendor-inventory.md`'s EasyPost and Stripe rows ("not yet an SST-managed secret") — file a card to add all seven before they carry real credentials. `incident-response.md` §6.1 steps 3a and 6 now cover containment for a leaked `FLOOR_TOKEN_SECRET` or `IMAGING_SHARED_SECRET`, but both still describe rotating a secret that has no `sst.Secret` yet — the card to add them is a real prerequisite, not just documentation |
| Local dev | `.env` files, never committed (`CLAUDE.md`: "No real API keys exist... Never remove a mock"; `git ls-files \| grep '\.env$'` is checked in `dependency-and-container-audit`) | Fine for local dev only |
| CI | GitHub Actions secrets (deploy keys, and the OIDC role in `deploy.yml`) | Never printed to logs; `deploy.yml` uses OIDC instead of a stored AWS key |
| Rotation cadence | **No rotation cadence is written down for any secret** (`invai-docs/compliance/vendor-inventory.md` flags every rotation-rule cell `[[OWNER]]`) except `FIELD_ENCRYPTION_KEY`, whose *mechanism* exists (prepend a new key, old data still decrypts — `invai-docs/build/runbook.md` §2) even though no *cadence* is set | `[[OWNER]]` to set a cadence (research 12 §1.4 suggests at least yearly, and immediately after any suspected leak or staff departure) — recommend: yearly for provider keys, immediately on any incident per `incident-response.md` §6.1 |
| Credentials never reach the client | Channel OAuth tokens and supplier keys stay write-only (`hasApiKey` flags) and masked in `audit_log`; they never go to the frontend, the AI provider, or logs (research 12 §1.4) | Enforced in backend code; re-verified by `security-reviewer` |

## 6. Access review and offboarding

| Control | Policy | Status |
|---|---|---|
| Access review cadence | Every 90 days: export the app's role matrix (`invai-contracts/src/roles.ts` against the live member list per tenant, via `team.read`) plus our own staff's AWS and GitHub access | **Not yet run — no production account and no staff GitHub roster tracked in this doc.** First review is due within 90 days of the first production deploy; `[[OWNER]]` to schedule and platform-sre to run the query side |
| Offboarding | Revoke a departing staff member's access within **24 hours** (Amazon key-controls guidance, research 12 §1.3): AWS SSO removal `[[OWNER]]`, GitHub org removal `[[OWNER]]`, and in-app `team.deactivate` (`team.manage`, `invai-contracts/src/contract/tenancy.ts:119`) — the in-app step ends that member's active sessions immediately, already true for floor sessions per research 12 §1.2 ("Deactivating a member ends their sessions at once... already true for floor sessions (S-07), so verify it for web sessions too" — **verify web-session revocation on deactivate before relying on this for offboarding**, a card for `backend-foundation`) |
| Station token offboarding (floor-specific, not a person) | `stations.revokeToken` (`stations.manage`, `invai-contracts/src/contract/tenancy.ts:177`) revokes the station's current token immediately (`invai-backend/src/modules/tenancy/service.ts:813-816`, returns `{ok: true}`) — used when a tablet is lost/stolen or a station's access must be cut. To bring the station back online, a separate call issues a fresh token: `stations.issueToken` (`stations.manage`, `tenancy.ts:173`, `service.ts:798-810`). Both are separate from a staff member's own account | Reachable today, no AWS needed |
| Owner-level actions | `org.export` (whole-company data export) and `org.delete` (whole-company deletion request and cancel) are owner-only (§4) and write an audit row; used for a tenant's own offboarding from InvAI, not staff offboarding | `invai-contracts/src/roles.ts` |

## 7. What this document does not yet cover

- MFA and email-verification enforcement in the app itself (research 12 §1.2, gap G1) — that is an
  application change, owned by `backend-foundation`, not an ops-doc gap; tracked in
  `invai-docs/security/v1-review.md` (T-21-3).
- A written Record of Processing Activities (RoPA) — part of the same G29 gap this document closes;
  the compliance-officer's legal drafts (`invai-docs/legal/**`, T-21-1) are the adjacent piece.
- Centralized 12-month security-log retention (research 12 §1.10, gap G30) — see
  `invai-docs/ops/incident-response.md` §3.

## References

- `invai-docs/research/12-security-quality-playbook.md` §1.2–1.4 (auth, authz, secrets), §7 (gap
  G29)
- `invai-contracts/src/roles.ts`, `invai-contracts/src/contract/tenancy.ts`,
  `invai-contracts/src/contract/channels.ts`
- `invai-infra/sst.config.ts`, `invai-infra/local/init.sql`,
  `invai-infra/.github/workflows/deploy.yml`
- `invai-backend/src/env.ts`, `invai-backend/src/db/schema/tenancy.ts`
- `invai-docs/build/runbook.md` §2 (key rotation)
- `invai-docs/compliance/vendor-inventory.md` (same `[[OWNER]]` convention, same vendor set)
- `CLAUDE.md` ("The owner's rules", "Repos, branches, ownership"), `.claude/hooks/guard-bash.py`
