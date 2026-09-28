# Reviewer memory

- [Web review env setup](env-web-review.md) — migrate uses MIGRATION_DATABASE_URL, CORS needs WEB_ORIGIN, rebuild dist before vite preview, use @playwright/test for scratch scripts.
- [Backend worktree review setup](env-backend-worktree-review.md) — TEST_DATABASE_URL/REDIS_URL overrides per worktree, evals/run.ts needs manual DB setup, mutation-test validator rules.
- [Contract review checks](contract-review-checks.md) — listProcedures walk via backend tsx, symlinked consumers, ALERT_KINDS exhaustive switch, zsh echo ==== trap.
- [Public route review checks](public-route-review-checks.md) — onError logs path (token leak), mailer logs `to`, XFF-spoofable per-IP buckets, shared worktree/Redis 10 etiquette.
- [Digest module review checks](digest-module-review-checks.md) — pnpm-on-symlink workaround, scratch concurrency tests, patch-the-fixture to prove "red for the right reason", git log truncation trap.
- [QA gate test review](qa-gate-test-review.md) — verify selector fixes against the component tree, check scale-test convention (scratch DB, not afterAll), spot disclosed-vs-silent AC scope gaps.
