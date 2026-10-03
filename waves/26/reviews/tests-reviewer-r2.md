# Review: invai-web 50955a3, e2e/listing-photos.spec.ts (round 2, gate-time test fix)

Reviewer: reviewer on Opus 5.5. Verdict: approve.

Evidence: `git -C invai-web show 50955a3 -- e2e/listing-photos.spec.ts` (read-only; no server run, per instructions, gate in progress).

Findings: the old assertion (`getByRole("button",{name:/^Approve$/}).first()).toBeHidden()`) depended on DOM order — it only ever passed if the first-rendered image happened to be one that passed every check, and failed whenever a legitimately-kept Approve button (failed/warned image, e.g. Amazon main or hoodie per AC6) sat first. That's not a fair test of AC6, which explicitly keeps Approve/Reject on non-passing images. The new assertion (count Approve buttons before click, assert an "Approved" badge appears, assert the count strictly drops after "Approve all passing") still fails if the feature does nothing (count unchanged, no Approved text) or if the button errors out, so it is not a no-op/weakened check.

Gap (non-blocking): "count strictly drops" doesn't prove *all* passing images got approved, only at least one — a bug that approves just one of several passing images would slip through. A stronger version would snapshot the pre-click count of `Pass` badges and assert the post-click Approve-button count equals `approveCountBefore - passBadgeCount`. Worth a follow-up QA ticket, not a block on this gate fix.

Scope/ownership: single file, matches qa-engineer's owned `invai-web/e2e/**`; no production code touched.
