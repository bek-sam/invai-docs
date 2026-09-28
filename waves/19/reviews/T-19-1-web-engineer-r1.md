# Review of T-19-1 (round 1, consumer co-review)

- Reviewer: web-engineer on sonnet
- Author: architect on fable
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `cd invai-web && node_modules/.bin/tsc --noEmit -p tsconfig.json` (against `@invai/contracts` 0.7.0, `e99ac21`+`83eee25`) | 1 error before my first commit (`alertKindLabel` exhaustive switch missing `ai_summary_breaker`, the known grant); clean after |
| Read `invai-contracts/src/contract/digest.ts`, `src/schemas/digest.ts`, `src/contract/tenancy.ts` (`notifications`), `src/schemas/tenancy.ts` (`NOTIFICATION_KINDS`), `src/events.ts`/`src/realtime.ts` (`digest.ready`), README "Public link routes" | full procedure/schema/event surface read |

## Consumer question: can I build every screen without guessing?
| Screen | Verdict |
|---|---|
| Today card, `digest.latest`, `digest.ready` refresh | Yes. `DigestLatest{digest, paused}` and `DigestSummary.net/netChange` are enough. |
| `/digests` list | Yes. `digest.list` paginated `DigestSummary`. |
| `/digests/:weekKey` glance, actions, win, thumbs, market reuse | Mostly yes. `Digest{steady, incompleteOrders, partialChannels, glance, actions≤3, win, marketWatch≤2}` and `DigestAction{kind, params, href}` cover D1–D7 fully (`DIGEST_ACTION_KINDS` and `DigestActionParams` fields map 1:1 onto the spec's Copy-table placeholders). Market items carry the full `MarketRecommendation`, so T-18-5's `RecommendationCard` drops in unchanged. |
| **D8 win card headline** | **Gap, not blocking.** `DigestInsight.templateKey` is a free `z.string()`, and there is no enumerated set of win template keys (best-net-week / on-time-record / units-milestone) and no spec Copy-table row for any of them (the table only has D1–D7 *action* rows). I can't select the win's headline copy from the contract or spec without inventing template-key strings myself and hoping T-19-3 (building in parallel) emits the same ones. I'm building a generic win renderer (fixed "This week's win" headline plus `impactCents`/facts) so the screen degrades gracefully regardless of what `templateKey` T-19-3 sends, and flagging the exact strings in my report for the tech lead to reconcile with T-19-3. Not blocking T-19-1: `templateKey` being a free string is intentionally additive-safe, and the fix (an enum or a documented key list) is a same-day follow-up, not a re-open. |
| `me.notifications.get/set`, first-digest opt-in | Yes. `NOTIFICATION_KINDS = ["digest"]`, `org.read`. |
| Settings → Notifications (day/hour/tz, AI toggle+shadow, recipients, preview) | Yes. `DigestSettings` has every field the screen needs (`aiSummaryMode` for AC33's disabled state, `recipients[].deliverable` for the status badges). `sendPreview`'s `RATE_LIMITED` carries `data.retryAfterSec`; there's no existing shared "try again in N seconds" helper in `src/lib/errors.ts` today (checked) despite the designer's non-blocking note assuming one exists — I'll build the message locally in my own route file, same pattern as `shipping.tsx`'s `voidErrorMessage()`. Not a contract gap. |
| Unsubscribe page | Yes. README "Public link routes" pins the URL, verbs, body shapes and redirect/undo rules precisely enough to build against without T-19-4 landing first. |
| Permissions (office no settings/plan-usage, presser FORBIDDEN, other org NOT_FOUND) | Yes. Permission mapping is on every procedure and matches the spec's AC27 matrix (`digest.test.ts` asserts it). |

## Acceptance criteria (card's own AC1–6)
| # | Met? | Evidence |
|---|---|---|
| 1 additive, web/floor typecheck | Yes, after the granted `ai_summary_breaker` case (my first commit `a800fbe`) | tsc clean above |
| 2 permission matrix | Yes | contract read; matches spec AC27 |
| 3 schemas | Yes | `DigestStatus` client-only `ready\|skipped_quiet`, no narrative text field |
| 4 feedback/recordClick idempotent | Yes | doc comments in `contract/digest.ts` |
| 5 `digest.ready` in realtime map | Yes | `{digestId, weekKey}`, matches wave.md's agreed interface |
| 6 README public-route shape | Yes | precise enough to build the unsubscribe page against |

## Blocking findings
None.

## Checks
- [x] Only owned paths changed by T-19-1 (not re-verified in depth; already approved by reviewer r1 and backend-foundation r1/r2, which I read)
- [x] Nothing outside scope
- [x] Tests exercise the behavior (per `digest.test.ts` described in the T-19-1 report; not re-run by me beyond the web-side typecheck)
- [x] en/es: no strings live in the contract itself; copy stays in web/backend, which is correct
- [x] Decisions recorded where needed (ADR 0016)

## Optional notes (not blocking)
- D8 win `templateKey` catalog: worth a same-day follow-up (contract enum or a doc list) so T-19-3 and T-19-5 render the same win copy without a side-channel agreement. I'll note the exact keys I chose in my T-19-5 report.
- `digest.get`'s `weekKey` as a query param (not a path segment) is a fine, well-documented deviation from the id-in-path convention; the oRPC typed client handles it transparently for the web.
