# Review of T-27-5 (round 1)

- Reviewer: reviewer on opus · Author: web-engineer on sonnet · Commit: invai-web 0495189
- Verdict: approve. No browser and no screenshots were used (decision 0024); I checked the code, the tests and the build.

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm vitest run --reporter=dot` (invai-web) | exit 0, all green |
| `VITE_API_URL="" pnpm build` | exit 0, built in 1.63s (with the var unset the build stops on the existing CSP guard, which is not this card) |
| `scan-test-weakening.sh invai-web 0495189~1` | no hits; the card changes no tests |
| i18n key diff: en.ts / es.ts / i18n-es.json | the same 36 `photos.*` keys in all 3 files; `es: Messages` is typed; no `i18n-es-missing.json`; no added es value equals its en value; a grep for mock/job/provider/queue in the copy finds nothing |
| contract read: `contract/photos.ts`, `schemas/photos.ts`, backend `photos/push.ts`, `scenes.ts` | the UI uses only fields and procedures that exist (pushTargets, pushToShopify, PushTarget, pushes, hasAiImages, designLockScore, the lock codes) |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | listing-photos.tsx:639-705: count 0-6 is clamped; scene checkboxes come from `analysis.sceneSuggestions`. The extra credits are the full estimate minus the estimate without `lifestyle` (:519-529), so the screen never copies a price. The sample note is at :649 |
| 2 | yes | labels.ts:203-228: IMAGE_DAILY_CAP_REACHED (already there), CREDITS_EXHAUSTED, AI_SPEND_CAP_REACHED and CONFLICT each get a plain en/es message |
| 3 | yes | ImageCard: ai_scene, AI person and drawn badges, plus the design-match %. `driftFailed` reads the `design_drift`/`region_changed` codes; scenes.ts `toOutcome` stores those checks on a failed image. The message includes "No credits charged" |
| 4 | yes | AttachButton shows the Etsy line when `hasAiImages` is true and the Amazon AI-person line when `hasSyntheticPerson` is true |
| 5 | yes | Picking a target sets both `connectionId` and `productRef.listingId`. One idempotency key per dialog open, unchanged across clicks. Results come from the latest push (`pushed` and `skipped`, which includes `already_pushed`, push.ts:404). The polling continues while a push runs. The button only shows with a Shopify connection, and `channels.list` is only called when the role has `channels.read`, so a designer gets no 403 |
| 6 | yes (code) | es is complete; the grid is `grid-cols-1` at small widths (:207, :921); the target list uses `button role=option`, so it is keyboard reachable. Light/dark was not checked in a browser (decision 0024) |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed: 5 files, all in invai-web src/ and scripts/i18n-es.json
- [x] Nothing outside scope. Wave 26 round 2 behaviour is kept: the poll stops when jobId changes (:301-312), the zip is keyed on `approvedKey`, URLs stay stable (the 5 deleted lines are only the replaced spec, poll and badge lines)
- [x] No weakened tests. The sample note waits for count > 0 so the QA-owned e2e passes without being edited
- [x] Tenancy and idempotency rest on the backend (key + requestHash conflict). Money is shown as credits only. en/es complete
- [x] No decision needed

## Optional notes (not blocking)
- :1236: the key stays the same after a failed push. If the shop then picks a different product in the same dialog, the server returns CONFLICT ("try again") until the dialog is reopened. Consider a new key in `onError` or when the target changes.
- :649: the "sample scenes" signal comes from the analysis source, not the image provider. The report flags this; a contract field would fix it (architect).
- A role with `photos.manage` but no `channels.read` never sees the push button. That is safe, but check it is the intended product rule.
