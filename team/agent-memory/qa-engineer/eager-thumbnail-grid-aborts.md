---
name: eager-thumbnail-grid-aborts
description: A list page that renders one SignedImage per card with no lazy-loading will abort many files/downloadUrl requests on navigation once previewKey stops being null; settled()'s swallowed timeout hides it
metadata:
  type: project
---

2026-10-01 wave P1 gate: `invai-web/src/routes/_app/catalog/designs.index.tsx` renders one
`<SignedImage>` per card for up to 60 designs. Before T-P1-4 gave designs real `previewKey`s, every
card's `fileKey` was null so `useSignedUrl`'s `enabled: !!fileKey` never fired a request — the whole
code path was dead. Once previewKey went live, ~40 concurrent `files/downloadUrl` POSTs fire on
every list load; Chrome's 6-per-origin cap queues most, and `e2e/helpers/ui.ts`'s `settled()`
silently swallows its own 10s timeout (`.catch(() => {})`), so a test can click a link and navigate
away while a chunk are still in flight — `watchPage()` then correctly reports a pile of
`net::ERR_ABORTED`. Lesson: any time a "previously always-null fileKey" field goes live, re-check
every list/grid screen that renders a `SignedImage` per row for this exact failure mode before
blaming the backend. See [[gate-contention-transaction-held-during-http-call]].

Also: `catalog.renderDesignPreviewsJob` (T-P1-4) calls `imaging.preview()` **inside** an open
`withTenant` transaction (`src/modules/catalog/service.ts:341-359`), queue `render` concurrency 2,
`lockDuration 120_000` (`src/lib/queues.ts`). Flagged by its own reviewer as a backlog risk. Worth
checking first whenever a floor/API request times out shortly after a batch of design
attach/update activity in the same gate run.
