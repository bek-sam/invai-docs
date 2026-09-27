# Decisions

One file per decision: `NNNN-<slug>.md`, numbered in order. Use the `record-decision` playbook.

- **Format (Nygard):** context, decision, status, consequences.
- **Status:** `proposed`, `accepted`, or `superseded by NNNN`. Never delete a decision; supersede it.
- **Type and owner:**
  - architecture: architect
  - product: product-manager
  - ops: platform-sre
  - security: security-reviewer
  - process: tech-lead
  - owner: decided by the human owner
- Don't reopen an accepted decision without new evidence. Reopening one goes to `owner-inbox.md`.

| # | Decision | Type | Status |
|---|---|---|---|
| [0001](0001-keep-multi-repo.md) | Keep 8 separate repos | architecture | accepted |
| [0002](0002-pack-semantics.md) | QC pass → packed; pack scans don't change state; label → shipped | product | accepted |
| [0003](0003-stock-push-opt-in.md) | Marketplace stock push is opt-in per connection | product | accepted |
| [0004](0004-push-to-main.md) | Work on `main`, push after tests and an independent review | owner | accepted |
| [0005](0005-team-operating-system.md) | 20-role team, playbooks, waves, independent review | process | accepted |
| [0006](0006-v1-cuts.md) | v1 cuts: AI design generation, direct SP-API, SanMar, GPU upscaling… | product | accepted |
| [0007](0007-ai-model-policy.md) | AI model policy: one config, effort per route, evals before cheaper models | architecture | accepted |
| [0008](0008-sign-in-rate-limit.md) | Sign-in rate limit is 20/min per IP (supersedes S-19's 10/min) | security | accepted |
| [0012](0012-floor-contract-compat.md) | Floor contract handshake: CLIENT_TOO_OLD 426, 14-day compat window, stale_version parking | architecture | accepted |
| [0014](0014-market-signals-and-digest-scope.md) | Market signals and weekly digest in scope, with fences (no scraping, no cross-seller data, no auto changes) | owner | accepted |
| [0015](0015-global-market-cache.md) | One global table without `company_id`: `market_series_cache`, taxonomy queries only, public-read RLS, written only by the nightly job | architecture | accepted |
