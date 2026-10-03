# Review of T-27-3 (round 1)

- Reviewer: compliance-officer on Sonnet 5
- Author: backend-engineer (photos) on Opus 5.5
- Verdict: approve

Scope of this review: marketplace-policy risk flag only — disclosures and image rules end to end
(XMP synthetic-performer, Etsy image disclosure, drawn-template exemption, Amazon main-image slot,
zip README wording). Code correctness, tenancy, files/credits and the S-55 fix are the reviewer's
and security-reviewer's territory.

## Evidence I re-ran / read
| Source | What I checked |
|---|---|
| `src/modules/photos/scenes.ts` (`compositeAll`, `ensureScene`, `toOutcome`) | XMP `xmp_subjects` set from `c.containsPerson`, which is decided once at `createSet` from the scene kind/analysis (`sceneContainsPerson`), not from the provider's output; `result.containsPerson` from both `mock.ts` and `openai.ts` is a passthrough of the requested prompt's flag, not pixel inspection — matches ADR 0023 §3 |
| `src/modules/photos/service.ts` (`createSet` image ordering, `attachToDraft`) | Templates always precede scenes within a channel (`ordered.length` then `sceneComps`); `attachToDraft`/`attachPhotosToDraft` only sets disclosures from `ok` (approved, channel-matched) images, OR'd monotonically onto `before` so a later template-only attach never clears a disclosure |
| `src/modules/photos/service.ts` `plan()` | `planned.length === 0` throws `view_not_available` before any scene is planned — a set can never be scene-only, so slot 0 (`presetFor(channel,0)`) is always a template |
| `invai-contracts/src/schemas/photos.ts:54-56` | `presetFor("amazon", 0) === "amazon_main"`, confirming lifestyle images (slot ≥ `ordered.length`) can never land on `amazon_main` |
| `src/db/schema/photos.ts:185-187` | `aiGenerated`/`containsSyntheticPerson` default `false`, `drawnTemplate` default `true` — a drawn template never carries a disclosure unless explicitly set, and nothing sets it for templates |
| `src/modules/photos/zip-readme.ts` (`readmeText`, `readmeEntries`) and `service.ts:1130-1136` (`runZip`) | README built per channel folder from each image row's own `aiGenerated`/`containsSyntheticPerson`, only from approved images; en+es text |
| `src/ai/validators/listing.ts:111-114` (`IMAGE_AI_DISCLOSURE`) and `src/modules/ai/service.ts:865-889,1049` | Sentence wording, and that `exportCsv` only adds it to Etsy's description when `imageAiGenerated` (wired from `draft.imageDisclosures.aiGenerated`) is true |
| `src/modules/photos/lifestyle.test.ts` | "base -> provider -> composite" test: `compositeCalls.every(c => c.xmp_subjects.includes("contains-synthetic-performer"))` for a person scene kind (`street`); "attach sends aiGenerated + syntheticPerformer"; "the zip gets a README per channel naming the AI and synthetic-person files (en + es)" |
| Dev run in the T-27-3 report | Street scene (person) got the XMP subject in the JPEG and `containsSyntheticPerson`; `flat_lay` (no person) got neither; zip README listed 2 AI files / 1 person file in en+es; another design's draft attach returned 409 CONFLICT |

## Acceptance criteria (my scope: parts of AC2, AC3)
| # | Met? | Evidence |
|---|---|---|
| AC2 — XMP whenever a person is present | Yes | `compositeAll` applies `p.c.containsPerson` to every channel derivative of a scene; test above; dev run (street JPEG carries the subject, flat_lay doesn't) |
| AC3 — Etsy disclosure on any approved AI image attach; README per channel, en+es | Yes | `attachToDraft`/`attachPhotosToDraft` OR logic; `exportCsv` sentence gated on `imageAiGenerated`; `readmeEntries`/`readmeText` built and tested |
| Drawn templates carry no disclosure | Yes | schema defaults + `createSet` only sets `aiGenerated:true`/`drawnTemplate:false` inside the scene-render branch (`r.scene`), never for template renders |
| Lifestyle images never used as Amazon main | Yes | structurally guaranteed: `plan()` refuses an empty template list, so slot 0 is always a template; `presetFor` maps slot 0 to `amazon_main` only |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed (photos module, imaging client grant, zip-readme) — no edits outside the card's scope, read-only review
- [x] Nothing outside scope
- [x] Tests exercise the behavior (XMP on person scenes, disclosure OR-merge, README content), none weakened
- [x] Disclosure wording reviewed for accuracy (en+es); not misleading
- [x] Decisions recorded where needed (0022, 0023 already cover disclosure-follows-source and design-lock; this card implements them faithfully)

## Optional notes (not blocking)
1. `zip-readme.ts` `readmeText()` builds the same generic text for every channel folder, including an Etsy-specific action line ("When you list on Etsy, mark the listing as made with AI") inside the Amazon/TikTok/Walmart READMEs too. It isn't false — the sentence is still conditionally true wherever it appears — but it gives an Amazon/TikTok/Walmart shop an irrelevant instruction instead of telling them their own channels' requirement is already satisfied automatically (the embedded XMP tag). Not blocking: the per-file AI/person lists are still correct and complete for every channel. A future card could make the action line conditional on the channel folder.
2. Carried forward from `waves/26/reviews/T-26-2-compliance-officer-r1.md`: Amazon's apparel on-model main-image requirement still has no check in `invai-imaging` (T-27-2's territory, not this backend card). Phase B now produces real/AI-rendered non-illustration images, so a flat lifestyle photo wrongly placed as `amazon_main` would no longer be blocked by `illustration_not_photo` — though this card's own slot ordering keeps lifestyle images off slot 0 entirely, so the gap doesn't bite through this card's flow. Still worth closing in imaging before a real shop uses `amazon_main` with a non-template image.
