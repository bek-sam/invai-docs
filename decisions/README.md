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
| [0016](0016-signed-link-routes-and-notification-preferences.md) | Email links are signed `/l/:token` HTTP routes outside oRPC (POST mutates, GET never); per-person email preferences keyed by kind, opt-in only; one send guard in `sendUserEmail` | architecture | accepted |
| [0017](0017-listing-attributes-shape.md) | Listing attributes are one `Record<string, string>` at the API and in `listing_drafts.content`; the model's `{ key, value }[]` is AI transport only, folded once in `toContent` (first key wins) | architecture | accepted |
| [0018](0018-token-budget.md) | Token budget: trimmed output, layered tests, cheapest capable model per card, ≤3 agents, fresh tech lead per wave; writing/UI roles default to sonnet | process | accepted |
| [0019](0019-lighter-review.md) | Co-reviewers only for real risk; reviewers run affected tests, full suites and E2E once per wave at the gate; waves 24–25 wait for AWS, analytics first | process | accepted |
| [0020](0020-is-reprint-means-re-pressed.md) | `isReprint` means "re-pressed at least once" (informational); a re-pressed, non-cancelled item is still a sale unit; no reader filters on it to count units, revenue or re-import matches | architecture | accepted |
| [0021](0021-openai-provider.md) | AI provider order: Anthropic key → Anthropic, else OpenAI key → OpenAI (`gpt-6.1-sol`, `gpt-6-luna` for the niche route), else the mock; same gateway controls; OpenAI quality unproven until `pnpm evals` runs in openai mode | architecture | proposed |
