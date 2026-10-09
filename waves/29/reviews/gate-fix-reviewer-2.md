# Gate-fix review 2: invai-backend 32113d7 (security-reviewer, T-29-1 co-review test)
Reviewer: reviewer (Opus 5.5). Read-only pass; gate is running, so no vitest/typecheck/DB run (by instruction).
Verdict: **approve**

- Scope: `git show --stat` lists one file, `src/modules/privacy/security.test.ts`, 92 insertions, 0 deletions. No existing assertion removed or loosened; no `.skip`/`.only`.
- Control test: seeds company B objects (art, preview, photo), points A's order_items and item_artwork keys and photo slot at them, ages A's order, runs `purgeBuyerPii`, then asserts all three B objects still exist (`exists`, a real head-object check) and A's unit is `purged` with artworkKey null. It asserts the property, not just "no error". Matches `own()` / `isCompanyKey` in `privacy/service.ts` (~:270).
- `it.fails` test: setup is sound (helpers `seedItemArt`, `exists`, `readBack` exist and return `photoKey`; the live item is `ready`, so it is not purged). Both units share the photo key. Service code (~:277) adds the photo key with no shared check, so the delete runs and the final `exists(...)` assertion is what fails, not setup. The earlier values.photo assertion still holds, so no earlier failure masks it.
- Traceability: the comment names S-59 and says to remove `.fails` when fixed; S-59 row in v1-review.md names this test title and the fix. Owner can flip it.
- Not run: tests (gate in progress); the S-56 row reports the control going red when the `isCompanyKey` check is removed.
- Optional non-blocking: `seedB` helper sits at file bottom; fine (hoisted).
