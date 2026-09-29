# Wave 20 owner report (2026-09-29)

## What works now
- The weekly digest, the assistant's market answers and Today are right on the real calendar date: no "stock before September" advice once the season has passed; a season in progress says "The Halloween season is on now. Make sure your design is listed and in stock." (en and es).
- Margin and on-time changes read as points ("+2.8 pts"); a flat number says "unchanged" / "sin cambio" with no arrow. The Spanish digest heading is fully Spanish, and all Spanish digest numbers use one format.
- The Today "no label yet" alert shows a readable date instead of a computer timestamp.
- Office staff who open a page they can't use see "You don't have access to this page. Ask the owner." instead of a technical message.
- Every money or outside action (label buy, void, tracking push, stock push, listing publish, artwork render, supplier orders) now has a test proving one effect even when it's retried after a crash: 27 new tests, each shown to fail when its safeguard is removed.
- The demo data can be rebuilt while the background worker is running, and a reset clears old queued work, so the demo no longer breaks after a reset.
- Team safety: the tech lead and reviewer agents can no longer edit code by mistake, and the push guard no longer blocks safe pushes while still blocking force-pushes and deletions.

## Evidence
- Integration gate PASS on a fresh seed built with the worker running: API golden path 13/13, floor 3/3, full browser run 35/35 (`reviews/gate.md`, screenshots in `reviews/gate-shots/`).
- Every card has an approving review from each required reviewer (`reviews/`).
- Pushed: contracts `78d2469`, backend `8ffff2b`, web `d092a4b`, docs.

## What went wrong
- Three usage-limit stops, two stalled agents and one full disk (Docker stopped until restarted). Work resumed from disk each time; nothing was lost.
- Three cards needed a second round, mostly because a copy example on a card disagreed with an earlier rule about Spanish number format. Fixed and recorded as a lesson.
- The gate found a deploy blocker that existed before this wave: in production, the browser's security policy would block file uploads to storage (B-190, planned for the deploy-readiness wave).

## What needs you
- OI-20: the Mac's disk is nearly full (about 10 GB free). Default: the team deletes nothing outside InvAI.
- Still open from before: OI-1, OI-2, OI-3, OI-8 to OI-15, OI-17, OI-18, OI-19 (counsel timing for the legal drafts). Nothing in this wave needed an answer to proceed.
