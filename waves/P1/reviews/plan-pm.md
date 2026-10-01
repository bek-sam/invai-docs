# PM review: wave P1 plan

**Verdict: approve**

## Checked
- Scope refs valid: T-P1-1/4/5 cite `always-in-scope: bug` (reliability/bug classes, scope.md "Always in scope"); T-P1-2 cites `#mvp-in` items 4 (Gang Sheet Builder), 12 (personalization), plus `always-in-scope: bug` for the B-209 preview-endpoint half; T-P1-3 cites items 13 (assistant) and 16 (market signals, `#market-signals`). All five anchors exist in `scope.md`. Nothing in the five cards' ACs touches the market/digest fences (no scraping, no cross-seller data, no auto price/listing changes) or any MVP-out item.
- 5-card cap holds, matching the wave 24 hand-off's own suggested set (B-228+B-229 split, T-23-3, T-23-4, B-209, B-222 as floor slot) exactly.
- Backlog rows B-41, B-103, B-114, B-131, B-132, B-135, B-165, B-192, B-209, B-215, B-222, B-228, B-229 all map 1:1 to a card. B-215 correctly absorbed into T-P1-1 AC5. B-227 (Low, no recurrence in A2) correctly deferred to backlog, not forced into a 6th card — sound, matches hand-off's own recommendation.
- Follow-on wave P2 deferrals (B-230, B-223/224, Today actions jobId re-queue, D2 unmapped label, D13 fixture, invai-ui follow-ups) are all genuinely separate from this wave's bug fixes — none is a prerequisite for T-P1-1..5. Sound cut.
- B-131: confirmed `specs/market-signals.md` is `Status: ready` (line 7) and Step 3a (detrending fix, with worked example and AC34) was added 2026-09-29 by product-manager per the Review log — the spec prerequisite T-P1-3 needs is in place.
- ACs are observable: each card's criteria name a concrete check (file/commit existence, response shape, DB name pattern, test pass count, wording in en/es, screenshot). T-P1-1 AC8 and T-P1-2 AC3's "note it" lines are hand-off instructions rather than testable behavior, which is fine — they're explicitly reporting obligations, not disguised scope creep.
- Dependency order (T-P1-4 waits on T-P1-1 committed + T-P1-2's `/preview` commit) is stated consistently in both `wave.md` and the T-P1-4 card.
- `files` risk flag on T-P1-2/T-P1-4 skips security co-review under decision 0019's lighter-review rule, with a named fallback (new/non-company-prefixed key pattern re-triggers security-reviewer) — acceptable, not a PM concern.

## Minor note (not blocking)
- T-P1-2's header scope-ref line names B-209 for the preview endpoint, while `wave.md`'s summary table only lists items 4/12 for T-P1-2 — harmless (the card is the source of truth and the B-209 split with T-P1-4 is well-documented), but the tech lead could align the summary line for clarity next time.
