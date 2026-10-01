# Wave P7: a repeatable gate pool, one shared confidence badge, tighter guard hooks and a per-round AI spend check

- Status: **planned** (2026-10-01). Planned from the hand-off at the end of `waves/P6/wave.md`.
- Goal (user outcome): the gate's gang-sheet step builds from the same pool every run (no mock order landing mid-run); the market's confidence badge lives once in the design kit, so every screen shows confidence the same way; the team's guard sees scripts it is asked to run, blocks secret and repo-setting changes it missed, and the Stop check notices code edited through the shell; one assistant question can't run past the shop's or the platform's AI spend cap.
- Scope refs: T-P7-1 `always-in-scope: bug` (B-255: flaky gate on the wedge); T-P7-2/T-P7-3 `scope.md#market-signals` (B-134, design-system debt on a shipped screen); T-P7-4 `always-in-scope: security` (B-115 hook gaps, B-189 guard gap); T-P7-5 `always-in-scope: security` (B-115 third gap: LLM10 unbounded consumption, research 12 §1.9).
- Owner's scope for this wave: only agent-doable P1/P2 items. Low (P3) items skipped. If none remain after P7, the tech lead writes `waves/status-2026-10-01.md` instead of a hand-off.
- Fences: no deploys, no AWS, no outbound sends. Track D out. OI-17 and OI-18 are not approved. `invai-infra` is read-only and never pushed (OI-22). Waves 24 and 25 stay paused (decision 0019). No buyer PII. No rate limit or security control weakened. Decision 0020 stands.
- Plan review: product-manager (scope), architect (design: the B-255 mechanism in T-P7-1, the shared component API in T-P7-2, the mid-run stop in T-P7-5). T-P7-4 (hooks, no product design; security-reviewer co-reviews) starts with the plan reviews.

## Cards
| Card | Owner | Model | Reviewer + co-reviewers | Risk flags | Status |
|---|---|---|---|---|---|
| [T-P7-1](T-P7-1-gate-pool-pinned.md) The golden-path suites hold the mock Shopify auto-import while they run (B-255) | qa-engineer | sonnet | reviewer (opus) | golden path | planned |
| [T-P7-2](T-P7-2-ui-confidence-badge.md) Shared `ConfidenceBadge` in `invai-ui` (B-134, kit half) | product-designer | sonnet | reviewer (opus) | ui (shared component) | planned |
| [T-P7-3](T-P7-3-web-confidence-badge.md) Market screens use the kit badge; local copy removed (B-134, web half); assistant spend-cap message in en/es (B-262) | web-engineer | sonnet | reviewer (opus) + product-designer (sonnet) | ui | planned |
| [T-P7-4](T-P7-4-hook-gaps.md) Guard reads scripts it runs, blocks `sst secret` and repo-setting API calls; Stop check counts shell edits (B-115, B-189) | platform-sre | opus | reviewer (sonnet) + security-reviewer (fable) | auth (team controls) | planned |
| [T-P7-5](T-P7-5-assistant-round-spend.md) The assistant re-checks the spend caps before every tool round and records spend per round (B-115) | ai-engineer | opus | reviewer (sonnet) + security-reviewer (fable, same agent as T-P7-4) | payments (AI spend) | planned |

Interfaces: none across repos. T-P7-3 builds on T-P7-2's committed export (`ConfidenceBadge` from `@invai/ui`, props agreed in T-P7-2's card). T-P7-1 uses the existing `channels.update` settings field `autoImport` (`invai-contracts/src/schemas/channels.ts:30`, honored by `pollableConnections`, `invai-backend/src/modules/channels/sync.ts:658`); no contract or backend change.

Order: plan reviews (PM, architect) + T-P7-4 → T-P7-1, T-P7-2, T-P7-5 → T-P7-3 (after T-P7-2's commit). Max 3 agents at once, reviewers included; max 2 heavy test runs.

## Slots and ports
- T-P7-1: scratch DB `invai_p7_gp`, API :3171, worker on the same env, imaging :8071, Valkey DB 12, `SEED_OUTPUT_FILE=/tmp/p7-1-seed-output.json`; API suite only, via `E2E_API_URL=http://localhost:3171`. Browser suite change is proven at the gate. Drop the DB at the end.
- T-P7-2: invai-ui only (vitest + build). No ports.
- T-P7-3: web dev server :5181 against the shared dev API only if :3000 is up; otherwise unit tests + build + Storybook-free screenshots from the gate. Don't use :5173.
- T-P7-4: no ports; works in a temp copy of the hooks first, installs only after the hook test suite passes.
- T-P7-5: vitest on `invai_test` only (Valkey DB 10 for the breaker tests if the card needs a live Redis); API :3175 for a live mock-provider check.
- Gate slot (:3000, :5173, :5174, :8000) stays free.

## Integration gate
- [ ] `caffeinate -i pnpm gate invai-backend invai-web invai-ui`
- [ ] Tech lead looked at: market badge en/es at 1440/390, the gate log's step 5 pool count
- [ ] Pushed (never invai-infra)

## Build log
- 2026-10-01 (P7 tech lead) Pre-wave: disk 8.3 GB free; docker healthy; code repos clean at origin/main (contracts d6d038b, backend a64533e, web 0ad173d, floor 9304da1, ui 2e3519d); infra 5 local commits (OI-22, not pushed); ports 3000-3199, 8000, 5173, 5174 free.
- 2026-10-01 B-134's web swap became its own card (T-P7-3) so each card has one owner; B-115 split into hooks (T-P7-4, with B-189 folded in: same file, same control) and the AI loop (T-P7-5). Grant: T-P7-4 may edit `invai-docs/team/hooks/**` (tech-lead path: the backup copy of the hooks and their tests) as well as `.claude/hooks/**`.
- 2026-10-01 Plan committed (docs fb596c5). Started the PM scope review (sonnet), the architect design review (opus) and T-P7-4 (platform-sre, opus) together.
- 2026-10-01 Architect plan review: approve-with-changes (`reviews/plan-architect.md`, docs 4e8c342). R1: the `autoImport` hold alone can't pin the pool (ticks queue syncs with up to 10 min delay, `syncConnection` doesn't re-check), so API step 5 builds from the preview's `orderItemIds` and asserts `itemCount`; B-261 (Low) for the backend skip. R2: badge in `src/app/`, `ConfidenceBand` from contracts, `confidenceBand.*` locale keys. R3: provider yields an internal `round` event; gateway checks caps/credits between tool rounds, records cumulative-minus-recorded spend. Web ignores `code: spend_cap` → B-262, folded into T-P7-3 (same owner, not started). Rulings applied to the cards before any of them started (docs c698273). Started T-P7-1 (qa-engineer, sonnet).
- 2026-10-01 PM plan review: approve (`reviews/plan-pm.md`). B-262 fold and B-261 as Low accepted. After P7 agent-doable items remain: B-185..B-188 (Amazon DPP hardening, always-in-scope: compliance) → P8 hand-off; B-132 parked (needs an architect decision first). Started T-P7-5 (ai-engineer, opus).
- 2026-10-01 T-P7-4 built: docs 74d0058, 8cd5f18 (report `reports/T-P7-4.md`). Guard reads scripts it runs (incl. nested), denies decode-into-shell, `sst secret set|remove|load`, `gh api` repo-setting writes, gh repo-setting subcommands and ruleset writes; comments stripped before word rules (a `#` used to hide later lines); `track-verify` counts shell edits by command text (own command only) and is wired for `PostToolUseFailure` on Bash (`.claude/settings.json`, within the card's "only if a hook must be wired" clause). 105/105 hook tests (baseline 58 with 1 failure, 2 errors, fixed). Behavior change: running `invai-infra/scripts/dev.sh` directly now asks the owner (it runs `pnpm install`); `pnpm dev:all` unchanged. Backup of `settings.json` to `invai-docs/team/settings.json` is the tech lead's, after review. Started T-P7-2 (product-designer, sonnet); T-P7-4 reviews queue for a slot.
- 2026-10-01 Tech lead finding for the T-P7-4 review: a `python3 - <<'EOF'` heredoc whose Python text quoted the blocked gh subcommands (inside a string literal written to wave.md) was denied as "repo settings are changed by the owner". Today's rule for git verbs in heredocs is the same (lesson 2026-09-26 W16), so maybe by design; the reviewer checks whether non-shell heredoc bodies (python, cat > file) should be read as shell.
- 2026-10-01 T-P7-5 built: backend 33c09fd (report docs 929d635). Per-round `recordSpend`; caps and credits re-checked before each `tool_use`/`pause_turn` round; trip closes the run, charges usage so far (`stop_reason` `spend_cap` / `credits_exhausted`), throws the existing errors; also checks the market-answer regeneration (falls back to the tools' answer). 191/191 in ai, full suite 1484 passed; 4 of 6 new tests red on a64533e (the 2 others guard unchanged behavior). Live :3175 mock answer streamed; presser 403. Accepted risk: parallel questions may each overshoot by one round. Started the security-reviewer (fable) on T-P7-4 + T-P7-5.

## Metrics
- First-pass approval, canary (none: OI-15 open), escaped defects, reopens, cycle time, tokens per card: at the close.

## Retro
- At the close.
