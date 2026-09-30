# Wave 25: operable without an AWS account (roadmap wave 11, agent part)

- Dates: planned; after wave 24
- Goal (user outcome): once the owner deploys, CI proves every change (lint, typecheck, unit, E2E, contract consumers, dependency/secret/container scans) and alarms tell the owner when shops are affected; traces follow an order from the API through the queue to imaging.
- **Hard fence:** no deploys, no `gh workflow run`, no secrets, no accounts. Workflows are written and linted (`actionlint`), not triggered against AWS. A workflow that needs a secret reads it from the GitHub environment and is documented in the owner checklist.
- Sources (backlog): B-08, B-18, B-21 (actions pinned by SHA, `permissions:`, deploy gated on tests), B-22 (E2E in CI), B-75, B-76 (deploy pipeline with pinned sibling SHAs, staging → production promotion, smoke, rollback), B-83 (contract CI triggers consumer typechecks), B-37 (SSE fan-out, autoscaling config).
- Plan reviewed by: product-manager (2026-09-28, approve), architect (2026-09-28, approve with change A1: imaging grant).

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| T-25-1 CI hardening in all 8 repos: SHA-pinned actions, least `permissions:`, dependency review, secret scan, container scan (Trivy or Grype), Dependabot/Renovate, SBOM (B-08, B-21) | platform-sre | opus | reviewer (sonnet) + security-reviewer | security | planned |
| T-25-2 E2E in CI and contract consumer CI: services (Postgres, Valkey, MinIO, imaging) in GitHub Actions, golden path + floor + role/Spanish suites, contracts CI typechecks backend/web/floor (B-22, B-83) | qa-engineer | sonnet | reviewer (opus) + platform-sre | — | planned |
| T-25-3 Deploy pipeline (not run): pinned sibling SHAs gated on green CI, migrate task, staging → production promotion with environment protection, smoke test, rollback (B-76) | platform-sre | opus | reviewer (sonnet) + security-reviewer; tech lead (release-affecting) | security | planned |
| T-25-4 Observability code (imaging spans by grant: `invai-imaging/app/main.py` middleware only, imaging-engineer co-reviews; architect A1): OTel traces API → queue → imaging, logs with `company_id`, `request_id`, `trace_id`, redaction tests, SSE fan-out through Valkey (B-18, B-37) | backend-foundation | opus | reviewer (opus) + security-reviewer (redaction) | pii | planned |
| T-25-5 Alarms and error tracking as code: CloudWatch alarms, SNS, budget alarm, 12-month log retention, error tracking provider behind a key (mock when absent), SLOs (B-75) | platform-sre | sonnet | reviewer (opus) + security-reviewer | security | planned |

## Integration gate
- [ ] All workflows pass `actionlint`; the ones that can run without secrets pass on a push of this wave (CI runs on GitHub by the push; report links)
- [ ] Fresh reset, migrate, seed; `run-golden-path`; traces visible locally (OTel exporter to console or a local collector)
- [ ] Owner checklist updated; roadmap criterion 3 and 5 status written honestly
- [ ] Pushed to `main`
- 2026-09-29 Paused by the owner until the AWS setup starts (decision 0019); analytics A1 and A2 go first. T-25-2 AC1 and AC3 (E2E in CI, pinned and linted workflows) were pulled forward to wave 23 as T-23-7; AC2 (contracts consumer CI) stays here.
