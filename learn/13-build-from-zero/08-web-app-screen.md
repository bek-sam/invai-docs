# Lesson 13.8 — The web app: React + TanStack + an oRPC client, one screen

## 1. In one sentence
You'll build a tiny Vite + React app with a typed oRPC client wired into TanStack
Query, and one real screen — a list of widgets with a create form — that calls your
lesson 13.3 backend and gets full autocomplete and compile-time checking on every
field, because the client is generated from the same contract the backend
implements.

## 2. Why it exists
Once backend and contract exist (lessons 13.2–13.3), the frontend's job is just:
call the procedures, show the data, handle loading/error/empty states. The part
worth getting right is *how* it calls them. A typed client built straight from the
contract means your editor autocompletes `orpc.widgets.create.mutationOptions(...)`
and flags it immediately if you pass a field the contract doesn't declare — the same
compile-time safety net from lesson 13.2, now reaching all the way into a React
component.

TanStack Query on top of that client handles the part every data-fetching screen
needs and almost everyone reinvents badly: caching, re-fetching, loading and error
states, and — the part that matters most here — **cache invalidation**, so creating
a widget automatically makes the list screen show it without a manual refresh.

## 3. How it works

### Step 1 — the app
```bash
cd ~/invai-from-zero
pnpm create vite web --template react-ts
cd web
pnpm add @orpc/client @orpc/contract @orpc/tanstack-query @tanstack/react-query @invai/contracts
```

### Step 2 — the typed client
```ts
// src/lib/rpc.ts
import { createORPCClient } from "@orpc/client";
import { RPCLink } from "@orpc/client/fetch";
import { createTanstackQueryUtils } from "@orpc/tanstack-query";
import type { ContractRouterClient } from "@orpc/contract";
import type { Contract } from "@invai/contracts";

const link = new RPCLink({
  url: "http://localhost:3100/rpc",
  fetch: (req, init) => fetch(req, { ...init, credentials: "include" }), // sends the session cookie
});

export const client: ContractRouterClient<Contract> = createORPCClient(link);
export const orpc = createTanstackQueryUtils(client);
```
`orpc` now has one property per contract procedure, each with `.queryOptions(...)`
(for reads) and `.mutationOptions(...)` (for writes) — TanStack Query's own shapes,
just pre-typed from your contract.

### Step 3 — the query client and provider
```tsx
// src/main.tsx
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
const queryClient = new QueryClient();
// ... <QueryClientProvider client={queryClient}><App /></QueryClientProvider>
```

### Step 4 — the screen
```tsx
// src/WidgetsScreen.tsx
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { orpc } from "./lib/rpc";

export function WidgetsScreen() {
  const queryClient = useQueryClient();
  const list = useQuery(orpc.widgets.list.queryOptions({ input: {} }));
  const [name, setName] = useState("");

  const create = useMutation(
    orpc.widgets.create.mutationOptions({
      onSuccess: () => queryClient.invalidateQueries({ queryKey: orpc.widgets.key() }),
    }),
  );

  if (list.isPending) return <p>Loading…</p>;
  if (list.isError) return <p>Couldn't load widgets. Try again.</p>;

  return (
    <div>
      <ul>
        {list.data!.items.map((w) => (
          <li key={w.id}>{w.name} — ${(w.priceCents / 100).toFixed(2)}</li>
        ))}
      </ul>
      <input value={name} onChange={(e) => setName(e.target.value)} />
      <button onClick={() => create.mutate({ name, priceCents: 999 })}>Add</button>
    </div>
  );
}
```
`queryClient.invalidateQueries({ queryKey: orpc.widgets.key() })` is the piece that
makes the list refetch after a successful create — no manual state juggling, no
"push the new item into local state and hope it matches what the server actually
stored."

### Step 5 — look at it, don't just compile it
```bash
pnpm dev     # :5173 by convention
```
Open the browser, create a widget, watch the list update. Open your browser's
network tab and look at the actual request body — confirm it matches exactly what
your contract declared as `widgets.create`'s input.

## 4. In our code
- `invai-web/src/lib/rpc.ts:1-14` — the real client: `createORPCClient(link)`,
  `createTanstackQueryUtils(client)`, an `RPCLink` whose `fetch` sets
  `credentials: "include"` so the session cookie from lesson 13.5's sign-in actually
  reaches the API.
- `invai-web/src/routes/_app/index.tsx:51` — a real read:
  `useQuery(orpc.today.summary.queryOptions({ input: {}, refetchInterval: 60_000 }))`
  — the same `useQuery(orpc.<x>.<y>.queryOptions(...))` shape your Step 4 used, with
  a polling interval added.
- `invai-web/src/routes/_app/index.tsx:595-605` — a real write plus invalidation:
  `useMutation(orpc.alerts.markAllRead.mutationOptions({ onSuccess: () =>
  queryClient.invalidateQueries({ queryKey: orpc.alerts.key() }) }))` — exactly your
  Step 4's `create` mutation, same pattern, different procedure.
- `invai-web/src/routes/__root.tsx` — the real router setup (TanStack Router) this
  lesson's tiny app skipped by keeping everything in one component; a real screen
  would live at its own route.
- Module 03.4 (`03-stack/04-frontend-stack.md`) — why React 19 + TanStack
  Router/Query + Vite over alternatives, in full.

## 5. What it uses
- **Vite** — the dev server and bundler; fast local reloads, no webpack config.
- **TanStack Query** — manages server-state caching, loading/error states, and
  cache invalidation after a mutation; module 03.4 covers why this over manual
  `useEffect` + `fetch` + local state.
- **oRPC's TanStack Query integration (`@orpc/tanstack-query`)** — turns a typed
  oRPC client into typed `queryOptions`/`mutationOptions`, so TanStack Query's own
  hooks get full type safety from the contract with no extra code.

## 6. Try it yourself
1. Break the contract on purpose: in your contract package, rename `priceCents` to
   `price_cents` in the `Widget` schema's output, *without* touching the backend or
   the frontend. Does `pnpm typecheck` in the web app now fail, and at which exact
   line? That's the chain from lesson 13.2 reaching all the way to a React component.
2. Remove the `onSuccess` invalidation from your `create` mutation, create a widget,
   and watch the list *not* update until you manually reload the page. Put it back
   and confirm the behavior changes.
3. Open your browser's network tab while using the real InvAI dev app (if you have
   it running) and find one real `/rpc` request. Compare its JSON body shape to the
   contract procedure it's calling.

## 7. Common mistakes
- Fetching data with plain `fetch()` calls scattered through components instead of
  through the typed client + TanStack Query. It works for a demo, but you lose
  caching, automatic refetch-on-focus, loading/error state management, and —
  critically — the compile-time check that your frontend and backend still agree.
- Forgetting `credentials: "include"` on the fetch call inside `RPCLink`. Without
  it, the session cookie from lesson 13.5 never reaches the API, and every request
  looks unauthenticated even right after a successful sign-in — a confusing bug to
  chase if you don't know to look here first.
- Manually pushing a newly-created item into local component state instead of
  invalidating the query. It looks like it works, until the server's actual stored
  value (say, a generated `id` or a server-side default) differs even slightly from
  what the optimistic local update guessed.

## 8. Check yourself
<details>
<summary>1. What specifically breaks, and when, if you rename a field in the
contract's output schema without touching the frontend?</summary>

`pnpm typecheck` in the web app fails, at the exact line where the component reads
the old field name off the query's data — because the client's types are derived
directly from the contract, the mismatch is caught before the app ever runs, not
discovered as a blank or broken field in the browser.
</details>

<details>
<summary>2. Why does <code>queryClient.invalidateQueries({ queryKey:
orpc.widgets.key() })</code> work, and what would happen if you called it with the
wrong key?</summary>

TanStack Query caches data under a key; invalidating that key tells it "this data
might be stale, refetch it." `orpc.widgets.key()` generates the exact key the
`widgets.list` query is cached under, so invalidating it triggers that query's
refetch. Calling it with the wrong key would invalidate nothing relevant — the UI
would keep showing stale data even though the mutation succeeded.
</details>

<details>
<summary>3. Why does <code>RPCLink</code>'s <code>fetch</code> need
<code>credentials: "include"</code>?</summary>

Browsers don't send cookies on cross-origin (and sometimes even same-site) fetch
requests by default. Better Auth's session lives in a cookie set during sign-in; without
`credentials: "include"`, that cookie never gets attached to the oRPC client's
requests, so every call looks unauthenticated even immediately after signing in.
</details>

## 9. Words to know
- **TanStack Query** — a library managing server-state in React: caching, loading/
  error states, refetching, and invalidation.
- **Query key** — the identifier TanStack Query caches a piece of data under;
  invalidating a key tells it that data may be stale.
- **Mutation** — a TanStack Query hook for a write (create/update/delete), as
  opposed to a query (a read).
- **RPCLink** — oRPC's client-side transport that turns typed procedure calls into
  actual HTTP requests to the `/rpc` endpoint.
