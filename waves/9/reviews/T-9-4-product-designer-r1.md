# Review of T-9-4 (round 1)

- Reviewer: product-designer on Sonnet 5
- Author: imaging-engineer + web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-web show 80fc945 -- src/routes/_app/catalog/personalization.\$templateId.tsx` | read the full editor diff |
| `git -C invai-web show 80fc945 -- src/i18n/en.ts src/i18n/es.ts` | diffed both locale files side by side |
| `grep -n '"pers\.' src/i18n/en.ts` vs `es.ts` (new keys only) | every new key added in `en.ts` (`fillOption`, `fit`, `fitOption`, `kind`, `kindPhoto`, `kindText`, `maxLines`, `maxLinesPh`, `minSize`, `minSizePh`, `strokeColor`, `strokeWidth`) has a matching key in `es.ts`, same alphabetical position |
| `invai-web`: `pnpm typecheck && pnpm lint` | clean — `es.ts` still satisfies the `Messages` type derived from `en.ts`, so no key can be silently missing |
| `invai-web`: `pnpm vitest run src/features/personalization/fit.test.ts` | 6 passed, including the new wrap/max-lines/min-size cases |
| Read `LivePreview`'s slot-rendering branch (`s.kind === "photo"` placeholder box; text branch's `<text>` per `fit.lines` with `stroke`/`paintOrder`) | placeholder box + label is a reasonable stand-in given no upload flow exists yet; text wrap/outline preview matches imaging's actual render rule (confirmed against `render.py` side by side) |

## Acceptance criteria (design angle: editor UX, en/es, preview fidelity)
| # | Met? | Evidence |
|---|---|---|
| Slot Type select (Text/Photo) | Yes | new `pers.kind` field; switching to Photo collapses font/color/align/stroke/sample-text fields out of the form (conditional render on `s.kind === "photo"`), avoids showing controls that don't apply |
| Photo slot fields | Yes | Fit/Fill select only (`pers.fit`, `pers.fitOption`, `pers.fillOption`), matches the card's scope (geometry + fit/fill, no upload widget) |
| Text slot new fields: Min size, Max lines, Outline width, Outline color | Yes | all four present with placeholders (`pers.minSizePh` "60% default", `pers.maxLinesPh` "Unlimited") that communicate the default behavior instead of leaving the field looking broken when empty |
| Outline color field disabled when width is 0 | Yes | `disabled={!s.strokeWidthPt}` — good micro-detail, avoids a confusing enabled-but-inert color picker |
| Live preview reflects wrap/shrink/outline/photo placeholder | Yes | multi-line `<text>` per `fit.lines`, SVG stroke/paintOrder for outline, dashed placeholder box + label for photo slots |
| en/es coverage | Yes | full parity, checked key-by-key above; strings read naturally in both locales (e.g. "Ajustar (se ve toda la foto)" / "Rellenar (recorta para cubrir)" are clear, idiomatic translations of fit/fill, not machine-literal) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (`invai-web` template editor + i18n, per the card's grant)
- [x] Nothing outside scope
- [x] Tests exercise the behavior; the two "removed" assertions in `fit.test.ts` are a rename (`.text` → `.lines.join(" ")`) plus a split into a more specific overflow-vs-wrap pair, not a loosening — confirmed by reading the diff, not just the scan output
- [x] All new UI strings added by hand to both `en.ts` and `es.ts` (not run through `pnpm i18n`, per the agent-brief rule); no key present in one locale and missing from the other
- [x] Conditional field visibility matches the two slot kinds' actual affordances — no dead/inapplicable controls left visible

## Optional notes (not blocking)
- The photo-slot placeholder box has no visual distinction between "no key configured yet" and "a key is configured but this is just a preview" — since there's no upload flow in this pass, a shop admin configuring a photo slot has no way to see what it'll actually look like until an order comes in. That's an acceptable, clearly-flagged gap for this card (see the reviewer/architect notes on the missing upload surface), but worth carrying into whichever card adds buyer-photo upload: the editor's preview should probably let staff attach a sample photo at that point, not just render.
- Consider a short helper caption under Max lines/Min size explaining the "larger floor wins" rule for a shop admin setting both — right now that logic is invisible in the UI and only discoverable by trial (typing a long name and watching what happens). Not blocking; a copy nit for a follow-up pass.
