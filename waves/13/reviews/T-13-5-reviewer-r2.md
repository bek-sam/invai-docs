# Review of T-13-5 (round 2)

- Reviewer: reviewer on Sonnet 5
- Author: (backend agent) — model not stated in report
- Verdict: approve

Scope note: per the tech lead's request this round covers **backend commit `3bc8f53` only** — the
imaging `/nest` integration (gang sheets now built through the real nesting service, FFD kept only
as a fallback). Round 1 (`T-13-5-reviewer-r1.md`) already approved the prior commit `c7fcb25` (the
FFD-only packer + `locale: es` change); that ground isn't re-litigated here except where `3bc8f53`
changes it. Fast-track: no full suite, no seeding the shared dev DB. Checked only the four items the
tech lead named: production `nestRequest` shape, fallback warning, seed determinism, tsc/biome.

## Evidence I re-ran

| Command | Result |
|---|---|
| `git diff --stat 3bc8f53^ 3bc8f53` (invai-backend) | Only `src/db/seed/builder.ts` touched (+240/-165). No `data.ts`, no other files — matches the card's exclusive ownership; `index.ts` (touched in `c7fcb25` for AC2) is untouched by this commit. |
| `git diff 3bc8f53^ 3bc8f53 -- src/db/seed/builder.ts` (full read) | New `ffdPack()` helper (mechanical extraction of the round-1-verified FFD loop, same logic, now generic over `NestItemLike`/`SheetSpec`); the per-chunk loop now calls `imaging.nest(...)` in a try/catch, builds one `gangSheets` row per returned sheet (`plans.length`, was hardcoded `1`), falls back to `ffdPack(chunk, DEFAULT_SHEET_SPEC)` on any thrown error or empty/no-placement result. |
| Compared the seed's inline `imaging.nest({...})` call (builder.ts, the try block) field-by-field against `nestRequest()` (`src/modules/production/sheets.ts:267-278`) and the identical inline call in the real send-to-vendor path (`sheets.ts:840-853`) | Same 8 fields, same names, same values: `items:[{id,width_in,height_in}]`, `sheet_width_in`/`spacing_in`/`margin_in`/`max_length_in` from `DEFAULT_SHEET_SPEC`, `allow_rotation: true`, `label_height_in`/`header_height_in` from the shared constants. Only difference is the item source type (`chunk` seed rows vs. `Candidate`), which is expected — field shape and semantics match production exactly. |
| `grep -n "imagingUp" src/db/seed/builder.ts` and read lines 1060/1104-1150 | The `imaging.nest()` call in the sheet loop is **not** gated by the `imagingUp` precheck (that flag only guards sample-art/compose rendering elsewhere) — it always attempts the real call and relies on its own try/catch, so an imaging-down seed run still falls back correctly and isn't silently skipped. |
| Read the fallback's `catch` block and the post-loop summary | Two `log.warn` calls: per-chunk `"seed: imaging /nest unreachable, falling back to FFD shelf pack"` (with `day` + error message) inside the `catch`, and a run-level `"seed: sheets built with the FFD fallback", { chunks: fellBackTo }` after the loop when `fellBackTo > 0`. A third `log.warn("seed: /nest left items unplaced", ...)` covers the (unreachable with real print widths ≤12in vs. 22in film) partial-placement case. |
| `.claude/skills/independent-review/scan-test-weakening.sh invai-backend 3bc8f53^` | `Result: no hits` — this commit touches no test files at all. |
| Forked sub-check of `invai-imaging/app/nesting.py` (the real `/nest` handler) for determinism | Deterministic: no `random`, no wall-clock or threading dependence; enumerates a fixed, literal-order set of 3 sort orders × 3 rotation modes × 3 heuristics and keeps the best via a numeric score compared with strict `<`, so ties always resolve to the same first-seen candidate. Same inputs → same placements every run. |
| `git worktree add --detach /tmp/review-t135-r2-wt 3bc8f53` (isolated, symlinked `node_modules`) then `tsc --noEmit -p tsconfig.json` | Clean, 0 errors (worktree removed after). |
| `biome check src/db/seed/builder.ts` (same worktree) | "Checked 1 file. No fixes applied." |
| `biome check .` (whole repo, same worktree) | "Checked 289 files. No fixes applied." |

Cleaned up: worktree removed, no DB touched, no processes left running.

## Acceptance criteria (round-2 scope only — the 4 items the tech lead named)

| # | Met? | Evidence |
|---|---|---|
| Uses the production `nestRequest` shape | Met | Field-for-field match against `nestRequest()` and the send-to-vendor inline call in `sheets.ts`, confirmed above. |
| Fallback logs a warning | Met | Per-chunk warning with error detail, plus a run-level summary warning; also a warning for partial placement. |
| Seed stays deterministic enough for the golden path | Met | `/nest` itself is a deterministic function of its inputs (confirmed by reading the algorithm); its inputs (`chunk` order, widths/heights, spec) are already deterministic given the seed's own RNG seed, unchanged by this commit. The FFD fallback (used whenever imaging is down) is unchanged, already-verified-deterministic logic, just extracted into a function. Golden-path E2E (`api-golden-path.spec.ts` test 5, `golden-path.spec.ts` test 5) build their own sheets live via `production.batches.build` / the UI, not from the seed's pre-built sheets, so this commit's seed-time layout doesn't feed those `utilization >= 80%` assertions either way. |
| `tsc` and `biome` pass | Met | Both clean at `3bc8f53`, in an isolated worktree (not the shared tree). |

Wider ACs (film efficiency 85–92%, seed <60s) are unchanged from round 1's framing — already flagged by the author for a PM/architect call and explicitly out of this round's checklist per the tech lead.

## Blocking findings

None.

## Checks

- [x] Only owned paths changed (`git diff --stat 3bc8f53^ 3bc8f53`): `src/db/seed/builder.ts` only, exclusively owned by this card.
- [x] Nothing outside scope: no changes to `modules/production/*`, imaging itself, or any real-order nesting path — the seed now *calls* the same imaging endpoint production uses, it doesn't change production code.
- [x] Tests exercise the behavior, none weakened: scan script found zero hits (no test files touched); same caveat as round 1 — no unit test asserts no-overlap/determinism directly against the new `imaging.nest` path (mocking a real HTTP call isn't in this commit's scope), evidence here is static (shape comparison, algorithm read) rather than a run against a live imaging instance, per the fast-track/no-DB-seeding instruction.
- [x] Tenancy / idempotency / money / en-es: N/A — seed-only code, no tenant table or money touched, no new UI copy.
- [x] Decisions recorded where needed: the commit's own comments explain why `/nest` is now used and why FFD is kept as a fallback; the report documents the efficiency numbers and flags the AC1 shortfall for a PM/architect decision.

## Optional notes (not blocking)

- The entire per-chunk loop, including the sequential `imaging.nest()` HTTP round-trips for every chunk (~15–25 per full seed), runs inside one DB transaction (`run(async (tx) => ...)` → `withSystem`). This is a real increase in transaction hold time versus the pure-CPU `c7fcb25` version, and lines up with the author's own observed 211s run (partly attributed to host/Docker contention, but the added network I/O inside the transaction is also a contributing factor worth having on record). Not blocking here — the tech lead directed this change, imaging is already a required seed dependency, and the seed doesn't run concurrently with other DB traffic in normal use — but worth a follow-up if seed time regresses in CI.
- No new unit test asserts "same shape as `nestRequest()`" mechanically (e.g. a shared builder function both call), so a future edit to `nestRequest()`'s field set could silently drift from the seed's inline copy without a test catching it. Same class of gap already noted in round 1 for the packer itself.
