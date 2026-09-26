# Review of T-9-4 (round 1)

- Reviewer: architect on Sonnet 5
- Author: imaging-engineer + web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-contracts show ad3d9cc` | contract diff matches wave.md's pre-agreed exact diff (TEMPLATE_FONTS wiring, `kind` enum, new fields, `.refine()`, `PersonalizationTemplateInputShape` split) |
| `git -C invai-backend show f1f1f40 -- src/db/schema/personalization.ts` | `TemplateSlot` type is TS-only (jsonb column); no `drizzle` migration file added or needed |
| `ls invai-backend/drizzle` | last migration `0023_ai_trademark_review.sql` predates this card — confirms no migration was required, consistent with a jsonb column type-only change |
| `invai-backend`: `pnpm typecheck` | clean |
| `grep -n "validateSlots" invai-backend/src/modules/personalization/service.ts` and read it | confirms backend is the real authority for dup-name + geometry, called from both `createTemplate` and `updateTemplate` (merging the partial patch first) — matches the report's claim that the contracts `.refine()` is a fast-fail only |
| `invai-imaging`: `uv run pytest -q` | 71 passed |
| Seed check: `invai-backend/src/db/seed/data.ts` `textSlot()` | new required TS fields (`minFontSizePt`, `maxLines`, `strokeWidthPt`, `strokeColor`, `fit`) added at safe defaults; `fontFamily: "Inter"` is within `TEMPLATE_FONTS` |

## Acceptance criteria (architect angle: contracts, sequencing, dual-authority)
| # | Met? | Evidence |
|---|---|---|
| Contract diff matches the agreed plan | Yes | `fontFamily` wired to `z.enum(TEMPLATE_FONTS)` (was the literal B-81 bug per the card), `kind` widened not narrowed, all new fields carry `.default()`s |
| Existing seeded templates still validate | Yes | Every new `TemplateSlot` field has a default (`minFontSizePt`/`maxLines`/`strokeColor` → `null`, `strokeWidthPt` → `0`, `fit` → `"fit"`); `kind: z.literal("text")` widened to `z.enum(["text","photo"])` so old rows still validate; `fontFamily` narrowed from `z.string()` to an enum, but the only seeded value (`"Inter"`) is a member so nothing breaks |
| Migration additive | Yes | `slots` stays a jsonb column; no SQL migration in this commit, none needed |
| Dual authority (imaging Pydantic + backend `validateSlots` + contracts `.refine()`) is consistent, not just decorative | Yes | All three independently reject duplicate names and out-of-bounds geometry with the same rule (`x+w<=width`, `y+h<=height`, tolerance `1e-6`); imaging is confirmed the actual enforcement point since it also validates `font_family` server-side (backend/contracts don't re-derive the font list, they just carry the enum) |
| `update` route correctness after the `Shape`/refined split | Yes | `PersonalizationTemplateInputShape.partial()` used in `src/contract/personalization.ts`'s `update` (zod v4 forbids `.partial()` on a `.refine()`d schema); backend's `updateTemplate()` still runs `validateSlots()` on the merged result, so a partial PATCH can't bypass the geometry/name check — verified by reading `service.ts:122-160` |
| `invai-backend/src/integrations/imaging/client.ts` zod mirror kept in sync (B-104) | Yes | `git show f1f1f40 -- src/integrations/imaging/client.ts` shows the same field set and the two new flag codes added to the hand-kept duplicate |

## Blocking findings
None.

## Checks
- [x] Only owned/granted paths changed in each repo
- [x] Nothing outside scope
- [x] No weakened tests in this card's own commits (scan-test-weakening hits in imaging/backend belong to concurrent T-9-2/T-9-3 commits sharing the repo, not `a5fd3b5`/`f1f1f40`)
- [x] Additive contract/schema change confirmed (no migration, all new fields defaulted, existing literal enum widened not narrowed)
- [x] Decision on "which shrink floor wins" (larger of the two) is applied identically in imaging and web, per wave.md's testability note

## Optional notes (not blocking)
- Concur with the reviewer's file that buyer-photo upload (an endpoint/UI to produce the storage key) is a separate surface outside this card's owned paths and outside every other wave-9 card too — correctly flagged as a follow-up rather than silently dropped or routed around.
- `PersonalizationTemplateInputShape` vs `PersonalizationTemplateInput` naming is a little easy to mix up at a glance; not blocking, just note it for anyone adding a third refine later.
