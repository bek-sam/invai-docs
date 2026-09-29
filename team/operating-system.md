# InvAI team operating system

How the agent team plans, builds, reviews, ships and learns. The owner's rules come first. Everything else here makes them workable. The reasoning and sources are in `research/13-team-gap-analysis.md`.

## The owner's rules
1. The tech lead plans and decides. It does not write feature code.
2. Every task has an owner, the files it owns and a definition of done.
3. Nothing is pushed to `main` without passing tests **and** a review by a different agent.
4. Every architecture or product decision is recorded in `invai-docs/decisions/`.
5. Waves have at most 5 tasks, with at most 3–4 agents running at once, then a review before the next wave.
6. MVP scope lives in `invai-docs/product/scope.md`. The PM owns it. Nothing outside it gets built.
7. Every tenant table has `company_id` and an RLS policy. Every request runs inside `withTenant`.
8. Webhooks, payments, label purchases, tracking pushes and scans use idempotency keys.
9. Heavy work (renders, mockups, labels, imports, AI batches) goes to the job queue.

## The team (20 roles)
Role files are in `invai/.claude/agents/`, with a backup in `invai-docs/team/agents/`. Each role preloads its playbooks from `invai/.claude/skills/`, backed up in `invai-docs/team/skills/`.

| Group | Role | Owns (edit rights) |
|---|---|---|
| Plan | `tech-lead` | `invai-docs/waves/**`, the backlog, `invai-docs/team/**`. Read-only on code |
| Plan | `product-manager` | `invai-docs/product/**`, `invai-docs/specs/**` |
| Plan | `product-designer` | `invai-ui/**`, `invai-docs/design/**` |
| Build | `architect` | `invai-contracts/**`, architecture decision records |
| Build | `backend-foundation` | backend core: `src/{db,lib,api,worker,test}/**`, `src/auth.ts`, `src/env.ts`, `src/modules/{tenancy,files}/**`, `src/modules/jobs.ts`, migrations tooling and the seed (not `src/api/webhooks.ts`) |
| Build | `backend-engineer` | `invai-backend/src/modules/<area>/**`, with the area named on the task card |
| Build | `integrations-engineer` | `invai-backend/src/integrations/**` (except `ai`), `src/api/webhooks.ts` |
| Build | `ai-engineer` | `invai-backend/src/ai/**`, `src/modules/ai/**`, `invai-backend/evals/**` |
| Build | `imaging-engineer` | `invai-imaging/**` |
| Build | `web-engineer` | `invai-web/**` |
| Build | `floor-engineer` | `invai-floor/**` |
| Verify | `reviewer` | its own review files in `invai-docs/waves/*/reviews/`. Read-only on code |
| Verify | `qa-engineer` | E2E suites, test fixtures, scale seeds, `invai-docs/build/qa-report.md` |
| Verify | `security-reviewer` | `invai-docs/security/**`, RLS and permission test suites |
| Run | `platform-sre` | `invai-infra/**`, CI/CD, `invai-docs/ops/**` |
| Customers | `customer-success` | `invai-docs/customers/**` (no real PII) |
| Customers | `docs-writer` | READMEs, `invai-docs/build/{runbook,architecture-as-built,demo-guide}.md`, `invai-docs/help/**` |
| Customers | `compliance-officer` | `invai-docs/compliance/**`, `invai-docs/legal/**` |
| Customers | `data-analyst` (starts when the first pilot goes live) | `invai-docs/metrics/**`, `invai-docs/calc/**`, `invai-backend/scripts/analytics/**` |
| Customers | `growth-marketer` (starts 4 weeks before public launch) | `invai-docs/growth/**`, the future `invai-site` repo |

**Carve-outs from the repo owners' `<repo>/**`:**
- `.github/**` and `Dockerfile`s belong to `platform-sre`.
- `e2e/**`, `**/*.acceptance.test.ts` and the scale seeds belong to `qa-engineer`.
- `**/security.test.ts` belongs to `security-reviewer`. Implementers still write tenant-isolation tests for their own tables in their module's normal tests.
- `src/test/**` (fixtures) in the backend belongs to `backend-foundation`. QA asks for fixture changes through a card.
- Each repo's `README.md` is edited by that repo's owner. `docs-writer` reviews it and owns the workspace-level docs.

**Team infrastructure:**
- `invai/CLAUDE.md`, `.claude/agents/**`, `.claude/skills/**` and `invai-docs/team/**` belong to the `tech-lead`. Any role proposes changes through `log-lesson`.
- `.claude/hooks/**` and `.claude/settings.json` belong to `platform-sre`, reviewed by `security-reviewer`.
- `invai-docs/research/**`: the tech lead curates.
- `architecture.md`: architect. `00-platform-concept.md`: product-manager. `tools-stack.md`: platform-sre. `invai-docs/README.md`: docs-writer.

**Shared file rule:** a `backend-engineer` may edit its own module's schema file (`invai-backend/src/db/schema/<area>.ts`) and generate its migration only when the card says so. `backend-foundation` then co-reviews it.

**The human owner keeps:** sales and customer conversations, anything sent outside the team, signatures and submissions, spending and pricing, production deploys, real keys, lawyer review, the Amazon 24-hour incident notice and final scope calls.

## A wave, step by step
1. **Scope (PM).** Pick at most 5 items from `product/scope.md` and the backlog, each with a spec in `specs/`. Bugs, security findings, incidents and compliance deadlines are always in scope, but still get a card.
2. **Plan (tech lead).**
   - Write `waves/<n>/wave.md` and one task card per item, from `waves/templates/`.
   - Agree cross-module function names up front, and have the provider commit stubs first.
   - The PM reviews the plan against scope, and the architect reviews its design. The tech lead never approves its own plan.
3. **Acceptance tests first (QA).** Write the acceptance tests from each card's criteria before the build starts.
4. **Build (owners).** Each owner stays inside its owned paths, follows its playbooks, and ends with `verify-and-report`.
5. **Review each task as it finishes.** The `reviewer` does a fresh-context, read-only review (`independent-review`), plus the co-reviewers the card's risk flags require. There are at most 2 rounds; after that, the tech lead escalates.
6. **Integrate (tech lead + QA).** Fresh reset, migrate and seed, then every E2E suite (`run-golden-path`). The tech lead looks at the key screens, then commits and pushes to `main`.
7. **Retro (tech lead).** Record what slipped, the reviewer catch rate and new lessons in `team/lessons.md`. A rule that recurs moves into a playbook, role file or hook.
8. **Report to the owner.** Plain language: what works, the evidence, what went wrong, and what needs the owner.

## Who reviews whom
| Author | Reviewer | Mandatory co-reviewer when |
|---|---|---|
| Any engineer, including `platform-sre` for infra and CI | `reviewer` (also checks UI, consumer impact and golden-path risk; decision 0019) | Only for real risk: contract change: `architect`. Migration or new table: `backend-foundation`. Risk flag tenancy, PII, auth, webhooks, files or payments: `security-reviewer`. Prompts or models: `ai-engineer`. A new screen or a new shared component: `product-designer` (small UI changes: the reviewer alone). The QA check happens once, at the integration gate |
| `architect` | `reviewer` on a different model | `backend-foundation` plus one consumer engineer |
| `product-designer` (`invai-ui`) | `web-engineer` or `floor-engineer` | `reviewer` for code quality |
| `qa-engineer` (test code) | the feature owner | `reviewer` |
| `tech-lead` (wave plan) | `product-manager` | `architect` |
| `product-manager` (spec) | `product-designer`, `qa-engineer` | `customer-success` |
| Documents (docs, growth, compliance, customer-success) | one domain owner | `compliance-officer` for public claims or legal text |

**Review rules:**
- The reviewer gets the card, the diff and the report, never the author's reasoning.
- Every verdict lists the commands the reviewer re-ran and their results. A verdict without evidence is not a review.
- Reviewers re-run only the checks for what changed: typecheck, lint and the affected test files in the touched repos. The full suite and E2E run once per wave, at the integration gate (decision 0019).
- Block only on correctness, acceptance criteria, security, tenancy, idempotency, ownership or scope. Style notes are optional.
- Scan for weakened tests: deleted or loosened assertions, `.skip`, mocks of the unit under test, special cases, rewritten snapshots.
- For high-risk flags, use a different model from the author's where possible.
- Every few waves, the tech lead plants a known bug to measure the catch rate, and records it in `lessons.md`.
- Every reviewing role, primary or co-reviewer, writes its own file: `waves/<n>/reviews/T-<n>-<k>-<role>-r<round>.md`. A card may be pushed only when every required reviewer's latest file says `approve`.
- Security co-reviews `platform-sre` changes that touch secrets, IAM, network or CI permissions, and the tech lead also reviews any change that affects a release.

## Where things live
| What | Where | Owner |
|---|---|---|
| Scope, segments, pricing hypothesis | `invai-docs/product/scope.md` | product-manager |
| Specs | `invai-docs/specs/<slug>.md` | product-manager |
| Decisions (one file each, Nygard format) | `invai-docs/decisions/NNNN-<slug>.md` | whoever decides, with the type owner |
| Waves, task cards, reviews | `invai-docs/waves/<n>/` | tech-lead (cards), reviewer (reviews) |
| Backlog | `invai-docs/waves/backlog.md` | tech-lead, ranked by the PM |
| Questions for the owner | `invai-docs/owner-inbox.md` | any role appends an entry; the tech lead curates; the owner answers |
| Lessons | `invai-docs/team/lessons.md` | any role appends a row; the tech lead curates |
| Research | `invai-docs/research/` (10–13 are the team's rulebooks) | — |
| Ops runbooks, SLOs, incidents, postmortems | `invai-docs/ops/` | platform-sre |
| Compliance packets and legal drafts | `invai-docs/compliance/`, `invai-docs/legal/` | compliance-officer |
| Customer profiles, issue log, support macros | `invai-docs/customers/` | customer-success |
| Help center (en/es) | `invai-docs/help/` | docs-writer |
| Metrics and experiments | `invai-docs/metrics/` | data-analyst |
| Growth plans and copy | `invai-docs/growth/` | growth-marketer |

## Escalate to the owner (`owner-inbox.md`)
Each entry has an id, the question, 2–3 options, a recommendation, the cost of waiting, a deadline and the default if there's no answer. **Always escalate:**
- a production deploy, real cloud accounts or real keys
- anything sent outside the team (shops, vendors, marketplaces, public posts)
- legal or marketplace submissions and signatures
- spending, pricing and plan limits
- real shop data in any non-local environment
- a High security finding or suspected PII incident, **immediately**, with Amazon's 24-hour clock stated
- scope beyond the MVP, or reopening a logged decision
- two failed review rounds
- any case where proceeding means weakening a control or a test

Routine technical choices inside a card are never escalated. Make the call and record it.

**What enforces this:** the guard hook (`.claude/hooks/guard-bash.py`) denies:
- force-pushes, ref deletions and tag pushes
- remote or history rewrites
- deploys (`sst`, `pnpm deploy:*`, `gh workflow run`)
- `aws` commands
- secret, key and repo-setting changes

Any MCP tool that isn't clearly read-only (send, reply, publish, create, update, delete) needs the owner's approval on screen. The hook fails closed. Owned paths for Write and Edit are not yet checked by a hook (backlog B-47), so role files and reviews enforce them.

## Playbooks (skills)
Every role preloads the 9 shared playbooks. Each playbook is `invai/.claude/skills/<name>/SKILL.md`.

- **Shared:** `task-intake`, `respect-ownership`, `read-before-change`, `verify-and-report`, `record-decision`, `log-lesson`, `escalate-to-owner`, `write-plain-language-copy`, `scrub-pii-fixture`.
- **Engineering:**
  - Contracts: `add-contract-procedure`, `contract-deprecation`
  - Data and jobs: `add-tenant-table`, `zero-downtime-migration`, `idempotent-job`, `idempotent-side-effect`, `add-backend-feature`
  - Integrations: `add-marketplace-integration`, `add-carrier-or-supplier-adapter`, `provider-deprecation-watch`
  - AI: `ai-feature-with-evals`, `model-upgrade`
  - Imaging: `imaging-change-with-budget`
  - UI: `build-dashboard-screen`, `build-floor-flow`, `add-ui-component`
  - Analytics and bugs: `instrument-analytics-event`, `root-cause-bug`, `scale-test`
- **Review and quality:** `independent-review`, `acceptance-tests-first`, `run-golden-path`, `threat-model-change`, `tenant-isolation-audit`, `dependency-and-container-audit`, `release-checklist`.
- **Operations:** `deploy-to-environment` (the owner triggers it), `add-observability`, `define-slo`, `incident-response`, `postmortem`, `backup-restore-drill`, `cost-review`.
- **Product, customers and docs:**
  - Product: `write-spec`, `prioritize-backlog`, `scope-change-request`, `pricing-experiment`, `competitive-watch`
  - Design: `ux-audit`, `usability-test-plan`
  - Customers: `onboard-shop`, `import-dry-run`, `triage-support-ticket`, `churn-risk-review`
  - Docs: `write-help-article`, `release-notes`
  - Data: `define-metric`, `weekly-metrics-review`, `experiment-readout`, `unit-economics-model`
- **Compliance and growth:**
  - Compliance: `marketplace-app-application`, `amazon-dpp-evidence-pack`, `privacy-request-handling`, `policy-change-watch`, `listing-compliance-check`, `legal-doc-draft`, `security-questionnaire`
  - Growth: `landing-page`, `seo-comparison-page`, `lifecycle-email-sequence`, `app-store-listing`, `launch-plan`
  - Outbound: `send-owner-draft`

## How the team learns
1. `team/lessons.md` is append-only. Each entry records the date, the wave or incident, what happened, the cause (blameless), the new rule and **where it's now enforced**.
2. **Promotion ladder:** a lesson that recurs moves into a playbook or role file. If it can be checked mechanically, it becomes a test or a hook.
3. Every role has `memory: project` (`invai/.claude/agent-memory/<role>/`) for its own gotchas. The tech lead reads these files in each retro and promotes what everyone needs.
4. Every wave file tracks:
   - first-pass approval rate and canary catch rate
   - escaped defects and reopen rate
   - cycle time and tokens per card
5. Every incident and every escaped High defect gets a postmortem within 48 hours.
6. Every 3 waves, prune `CLAUDE.md` and the role files. Delete any line whose removal wouldn't cause a mistake.
