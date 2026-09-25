# Review of T-4-1 (round 2): architect co-review (contract comments fix)

- Reviewer: architect co-review, run by the reviewer agent on Claude Opus 5.5 (a different model from the fix's author)
- Author: architect on Claude Sonnet 5 (contracts `6718f56`)
- Verdict: **approve**

## Evidence I re-ran
| Command | Result |
|---|---|
| `git show 6718f56`; `git diff c181abf 6718f56 --stat` | 4 files: `contract/production.ts`, `roles.ts`, `schemas/orders.ts`, `schemas/production.ts`; 18 lines added, 11 removed |
| `git diff -U0` filtered to changed lines that aren't `/** … */`, `*` or `//` comment text | none. **Comments only**: no schema, enum, route, permission or error change. |
| contracts `vitest run` | 4 files, 31 tests passed |
| contracts `tsc --noEmit` / `biome check .` | exit 0 / 46 files clean |
| decision 0010 in invai-docs | committed (`c842d36`) |

## Round-1 finding 1: resolved
Each comment now matches decision 0010 and the replay behavior I saw live in round 1 (`T-4-1-reviewer-r1.md`):

| Location | Now says | Matches |
|---|---|---|
| `schemas/production.ts` `PackOrderInput.idempotencyKey` | only calls that changed something are stored; a refusal (`PACK_INCOMPLETE`, `FORBIDDEN`, `CONFLICT`) has no effect, and a retry re-evaluates | `floor.ts` stores only after the effects; live: a refused key later packed with the same key (`pack.test.ts:139`) |
| `schemas/production.ts` `override` | the "hand to lead" path (0010) | 0010 |
| `schemas/production.ts` `PackOrderResult.missing` | non-empty when `packed` is false, empty when it's true | backend: `packed = missing.length === 0` |
| `schemas/production.ts` `PackOrderResult.override` | non-null when this call, or the stored call under this key, handed the order to a lead; `packed` is then false | replay is keyed by key (not by order); live hand-off returned `packed:false` + `override` |
| `schemas/orders.ts` `Order.packOverride` | handed to a lead (0010); cleared once every non-cancelled unit is really packed | `orderStatusWithOverride` `clearOverride`; seen live |
| `roles.ts:66` | "hand a short order to a lead" | 0010 |
| `contract/production.ts` `packOrder` doc | stored vs refused calls; the hand-off records the reason and missing units, releases the tote, returns `packed:false` and never changes the status; the order ships only once fully packed | 0010; live: `in_production` kept, tote released, not in the ship queue |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`invai-contracts/src/**`, architect).
- [x] Nothing outside scope (comments only).
- [x] Tests: none changed; 31 pass.
- [x] Contract stays additive: no shape change in this commit.
- [x] Decision 0010 is committed and referenced from the comments.

## Optional notes (not blocking)
1. An override sent when nothing is missing is ignored: `packed:true`, `override:null` (`pack.test.ts:244`). The comments don't say so, but they don't contradict it.
2. The round-1 optional note about `roles.test.ts` coverage for `production.override` and `production.receive` still stands.
