# Review of T-13-5 (round 1)

- Reviewer: reviewer on Sonnet 5
- Author: (backend agent) — model not stated in report
- Verdict: approve

Scope note: per the tech lead's request this review covers **backend commit `c7fcb25` only**
(the FFD gang-sheet packer + `locale: es` seed change). The imaging-`/nest` follow-up visible as
uncommitted work in the shared `invai-backend` tree is explicitly out of scope. Per instruction,
did not run the full suite and did not seed the shared dev DB.

## Evidence I re-ran

| Command | Result |
|---|---|
| `git -C invai-backend diff --stat c7fcb25^ c7fcb25` | Only `src/db/seed/builder.ts` (+56/-18 net incl. comments) and `src/db/seed/index.ts` touched. No `data.ts`, no production/nesting modules. |
| `git worktree add --detach /tmp/review-t135-wt c7fcb25` + `tsc --noEmit -p tsconfig.json` | Clean, 0 errors, at the exact commit (no unrelated stray error — that error in the author's report comes from a later, unrelated in-flight commit sharing the tree). |
| `node_modules/.bin/biome check src/db/seed/builder.ts src/db/seed/index.ts` (in the isolated worktree) | `Checked 2 files. No fixes applied.` |
| `node_modules/.bin/biome check .` (whole repo, in the isolated worktree) | `Checked 277 files. No fixes applied.` |
| `.claude/skills/independent-review/scan-test-weakening.sh /tmp/review-t135-wt c7fcb25~1` | `Result: no hits` (exit 0) — no test files touched by this commit at all. |
| Standalone re-implementation of the exact packing loop from `builder.ts` (`/tmp/review-t135-wt/pack-check.mjs`), run 3x each against: a 24-item realistic size mix, ten equal-12in-wide items (the pairing-collision case the author's report calls out), an empty chunk, a single item, and 24 random-sized items (fixed seed) | All layouts: zero pairwise rectangle overlaps, every item's right edge ≤ `filmIn - marginIn`, byte-identical layout JSON across all 3 runs (deterministic). Only failure was a deliberately pathological case (a single item wider than the whole 22in film) — a pre-existing shelf-pack limitation, not a regression, and not reachable by real DTF print widths (max ~12in per the wave root-cause doc). |
| `grep` for who imports `db/seed/builder.ts` / calls `buildShopData` | Only `src/db/seed/index.ts` (offline seed script) and `src/modules/tenancy/demo.ts` (the live "sample workspace" API feature, pre-existing dependency from T-5-3, unchanged by this commit). Demo calls with `pins: []`, so the new `locale` branch never fires there — confirmed in `demo.ts:104`. |
| `grep -n locale src/db/schema/tenancy.ts` | `users.locale: text().notNull().default("en")` — plain text column, no enum constraint to violate; `src/db/seed/index.ts:48` shows the seed already updates `users` directly elsewhere (`emailVerified`), so this isn't a new pattern. |

Cleaned up: worktree removed (`git worktree remove /tmp/review-t135-wt --force`), scratch script deleted with it. No DB touched, no processes left running.

## Acceptance criteria

| # | Met? | Evidence |
|---|---|---|
| 1. Film efficiency 85–92% | **Not met, but out of this review's scope by the tech lead's framing** | Author's own numbers: 69.58%→79.46% avg (min 72/max 85%), below the 85–92% band. Root cause (wide "back" prints can't pair under 22in film) is real and already flagged by the author for an architect/PM call; a separate follow-up (imaging `/nest` integration, visible as WIP in the shared tree) is already underway to address it. Packing *algorithm* itself is verified correct (see evidence above) — the shortfall is a data/overhead-constants ceiling, not an algorithm bug. |
| 2. Locale: `es` for floor staff | Met | `src/db/seed/index.ts` diff: `luis@desertbloom.test` now carries `locale: "es"`; threaded through `pins[].locale` into `builder.ts`'s new `if (p.locale) await tx.update(users)...` line. Column exists, type-checks, no RLS concern (`users` is explicitly a non-tenant table per `schema/tenancy.ts` comment, and seed code already writes it directly elsewhere). |
| 3. Demo workspace gets same mix | Met | `demo.ts` and `index.ts` both call the one shared `buildShopData`; no demo-specific code needed changing, confirmed by grep — this is the correct, minimal way to satisfy the AC. |
| 4. Seed unchanged elsewhere / under 60s | Not independently re-run (would require seeding a DB, out of this review's remit) | Author reports 18–22s. No `data.ts` diff, no change to volumes/counts, so nothing here would plausibly regress seed time. Taken as reported. |

## Blocking findings

None.

## Checks

- [x] Only owned paths changed (`git diff --stat`): `builder.ts` (owned exclusively), `data.ts` untouched, `index.ts` touched but uncontested/unowned by any other wave-13 card (verified via `grep` across `wave.md` and `T-13-*.md`) and justified (AC2 can only land where `SHOP_USERS` lives).
- [x] Nothing outside scope: no changes to `modules/production/*`, imaging, or any real-order nesting path. `demo.ts` (a genuine production API route for the "sample workspace" feature) does call the modified `buildShopData`, but that dependency pre-dates this commit (T-5-3) and is the intended mechanism for AC3 — not new scope creep. Worth flagging for visibility, not blocking.
- [x] Tests exercise the behavior, none weakened: scan script found zero hits (this commit touches no test files at all — there's no unit test of the packer itself, only the author's manual efficiency measurement; see optional note).
- [x] Tenancy / idempotency / money / en-es: N/A for tenancy/idempotency (seed-only, `users` is a non-tenant table); no money touched; no new UI copy (a data field, not a string) so the en/es rule doesn't apply here.
- [x] Decisions recorded where needed: root cause and the FFD fix are documented inline in `builder.ts` and in the wave/report docs; the AC1 shortfall is explicitly flagged for a PM/architect decision rather than silently swept under the rug.

## Optional notes (not blocking)

- No unit test covers the packer directly (no-overlap / width-bound / determinism) — the only evidence is the author's manual efficiency run and my own out-of-repo re-implementation. A small `builder.test.ts` asserting no-overlap/width-bound over a synthetic chunk would make this regression-proof; consider for a follow-up.
- `demo.ts` importing `buildShopData` means every future seed-builder change silently reaches the live sample-workspace feature too. Not a problem here (it's literally AC3), but worth a comment or test tying the two together so it stays intentional.
