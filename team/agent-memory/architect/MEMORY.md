# architect memory

Seeded 2026-09-26 from `team/lessons.md` (T-16-3); every line below is a row there. Add your own entries under "Learned on cards": date, card, what you learned. No PII or secrets.

## Lessons that apply to you
- 2026-09-26 W8: Never `git stash`, `reset` or `checkout --` in a shared tree; compare in your own worktree at the base commit.
- 2026-09-26 W8: Don't push. Only the tech lead pushes, after the gate (a builder once pushed 44 ungated commits).
- 2026-09-25 W3: Shared files: stage only your hunks (`git add -p` / `git apply --cached`), check `git diff --cached`, then commit.
- 2026-09-24 W2: Kill only PIDs you started (`lsof -ti :<your port>`); never `pkill`/`killall`.
- 2026-09-25 W6/7: Never run `pnpm` inside a worktree; call `node_modules/.bin/*` directly. Never re-link shared `node_modules`.
- 2026-09-25 W3: Poll long jobs inside your turn with short sleeps; don't end your turn to wait.
- 2026-09-24 v1: Check the installed library API in `node_modules` before writing code (oRPC 1.15, drizzle 0.45, Zod 4, TS 7, Better Auth 1.7 are newer than training data).
- 2026-09-26 W7: A `db/schema` change ships with its generated migration in the same commit, and you run the backend tests, not only typecheck (68 tests broke once).

## Learned on cards
- [T-13-2 tooling not built](project_t13_2_not_built.md) — the version-check script/CI gate cards reference doesn't exist; verify before relying on it.
- [Contract version bump convention](feedback_contract_version_bump_convention.md) — bump minor (never patch) on 0.x, breaking or additive alike; only touch FLOOR_COMPAT_BASELINE for floor-facing shape changes.
- [Sample workspace and global tables](project_sample_workspace_and_global_tables.md) — `companies.demo` is not the sample test; global tables write via withSystem; `.list` must paginate (wave 18 plan review)
- 2026-09-27 W18 plan review: the assistant `tool_result` yield lives in `modules/ai/service.ts`; any new event field needs that file in the ai-engineer's card, or a grant is certain.
- 2026-09-27 T-18-1: `contract.test.ts` rejects GET paths with a param other than `{id|orderItemId|blankVariantId|userId|code|purchaseOrderId|shipmentId|orderId|jobId}`; a GET keyed by `designId` goes as a query param (`GET /niches/design?designId`), not `/{designId}`.
- 2026-09-27 T-18-1: a new contract namespace always breaks `invai-backend/src/api/router.ts` typecheck (`os.router` requires every key) until the implementer's one-line registration lands; report it as the expected break, don't wait on it. Web and floor stay green for additive changes.
- 2026-09-27 T-18-1: `invai-contracts/README.md` (namespace table, permission list) is not in the card's owned paths even though the role owns it; ask the tech lead for the line in the card up front.
- [Market module boundaries](project_market_module_boundaries.md) — T-18-3's `deps.ts` funnel pattern and the asOf normalize-on-write/serialize-on-read seam; a good template for future cross-module reviews.
- [Contract permission and consumer gotchas](project_contract_permission_and_consumer_gotchas.md) — `org.read` = any member; OWNER_ONLY perms; web `keysForEvent` needs a case per new event; a stub per touched namespace (wave 19 plan review)
- 2026-09-27 W19 plan review: when two cards each add a table, fix the migration order in wave.md (day-1 card first) instead of "later regenerates"; and name where email idempotency lives (a durable `email_sends` key in the sender, plus the caller's per-recipient outcome row).
