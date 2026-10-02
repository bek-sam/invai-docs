---
name: feedback-orpc-queryoptions-always-aborts
description: oRPC's generated .queryOptions() queryFn always consumes context.signal, so TanStack Query aborts the fetch on any unmount while in flight — use .call()/.queryKey() directly when that abort is unwanted.
metadata:
  type: feedback
---

`orpc.<ns>.<proc>.queryOptions()`'s generated `queryFn` always destructures `signal` from the
TanStack Query context and forwards it to the client call (`@orpc/tanstack-query/dist/index.mjs`,
`queryFn: ({ signal }) => client(input, { signal, ... })`). TanStack Query's `Query.removeObserver`
only calls `retryer.cancel()` (actually aborting the underlying fetch, producing a visible
`net::ERR_ABORTED`) when `abortSignalConsumed` is true — which it always is for any oRPC-generated
`queryOptions()`. So any `useQuery(orpc.x.y.queryOptions(...))` call WILL abort its in-flight
request the instant the last component observing it unmounts (any client-side navigation), even if
nothing in the UI depended on the result.

**Why:** found on [[project-t-p2-1-lazy-thumbnails]] — a single `analytics.designLifecycle` call
and per-card `files.downloadUrl` calls were flagged as failed/aborted requests by
`e2e/helpers/ui.ts`'s `watchPage()` purely because the user navigated away before they finished,
not because of any real bug or too many requests.

**How to apply:** when a query's result isn't needed after unmount and a passing E2E check (or just
cleanliness) requires zero aborted requests, replace `useQuery(orpc.x.y.queryOptions({ input }))`
with a manual queryFn that calls the client directly (no signal forwarded):
```ts
useQuery({
  queryKey: orpc.x.y.queryKey({ input }),
  queryFn: () => orpc.x.y.call(input),
  enabled: ...,
})
```
The request completes quietly in the background instead of surfacing as `net::ERR_ABORTED`. Check
first that nothing actually depends on cancellation (e.g. an expensive mutation you want to stop
mid-flight) — for plain reads this is safe and invisible to the user.
