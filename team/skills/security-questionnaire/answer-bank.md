# Security answer bank (starting point)

State as researched on 2026-09-24 (research 12 §7, `security/v1-review.md`). Re-verify every line before use; copy to `invai-docs/compliance/questionnaires/answer-bank.md` and keep it current there.

| Domain | Question (typical) | Status | Answer (short) | Evidence |
|---|---|---|---|---|
| Tenancy | How is customer data separated? | Yes | Every customer table carries a company id with Postgres row-level security; the app's database role cannot bypass it; a test fails CI if a table lacks a policy. | `invai-backend/src/db/rls-coverage.test.ts`; v1-review "What was verified" |
| Access control | Role-based access in the app? | Yes | Every API procedure declares a permission; a test calls all of them as each role. Buyer addresses need the orders-manage permission. | `invai-contracts/src/roles.ts`; `src/api/authz.test.ts` |
| Authentication | MFA? | No / Not yet | MFA for owner and admin accounts is planned. | backlog B-09 |
| Authentication | Password policy and lockout? | Partial | Sign-in rate limits per IP; per-account lockout and history planned. | S-19; B-09 |
| Encryption | At rest? | Partial | Buyer name, email, phone and street encrypted with AES-256-GCM at field level; managed-key (KMS) use planned. | `src/lib/crypto.ts`; G11/B-23 |
| Encryption | In transit? | Verify | TLS 1.2+ at the edge. | infra config (B-03 HTTPS listener) |
| Retention | How long is buyer PII kept? | Yes | Deleted 30 days after delivery (or after shipping/cancel when no delivery event), nightly; related files swept after 30 days. | `src/modules/orders/jobs.ts`; `purge.test.ts` |
| Privacy requests | Can you delete one buyer's data? | Partial | Routine purge exists; per-buyer export and deletion tooling planned. | G13/B-23; `privacy-request-handling` |
| AI | Is our data used to train models? | Yes (no training) | No. Marketplace and buyer data are never used for training; buyer PII is removed before AI calls. | `src/ai/pii.ts`; decision 0007; research 10 R15 |
| Logging | Security logs kept 12 months? | No / Not yet | App audit log is append-only; centralized 12-month retention planned. | `src/lib/audit.ts`; G30/B-18 |
| Vulnerability mgmt | Scanning cadence? | No / Not yet | Dependency, secret and container scanning in CI planned (30-day cadence). | G18/B-08 |
| Pen test | Last pen test? | No | None yet; planned before marketplace PII access. | v1-review "Before applying…" |
| Incident response | Written IR plan? Notice time? | No / Not yet | Plan being written; target 24 h notice to customers. | G29/B-10 |
| Vendors | Sub-processors? | Partial | AWS, Anthropic, EasyPost, Stripe (planned), email provider. List and assessments being written. | research 12 §2.4; B-10 |
| Payments | Do you store card data? | Yes (none stored) | No card data touches our systems; billing via Stripe (planned: Checkout redirect, SAQ A). | research 12 §2.5; billing is mocked today |
| Certifications | SOC 2 / ISO 27001? | No | Not audited. Readiness work started. | research 12 §2.6 |
| Supply chain | Dependency pinning? | Partial | Lockfiles committed, frozen installs in CI; action SHA pinning planned. | G15/B-21 |
