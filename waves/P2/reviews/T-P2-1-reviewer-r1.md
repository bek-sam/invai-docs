# Review of T-P2-1 (round 1)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Sonnet 5 (commit `invai-web@7c243f9`)
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck && pnpm lint && pnpm test --reporter=dot` (invai-web) | exit 0; 20 files / 133 tests passed; 1 lint warning, already there (`src/content/markdown.test.ts:106`), not in this diff |
| `biome check` on the 3 changed files | clean |
| `VITE_API_URL=http://localhost:3000 pnpm build` | built in 2.22s |
| `scan-test-weakening.sh invai-web 7c243f9~1` | no hits; `git diff --stat 7c243f9~1 7c243f9 -- e2e` is empty |
| Playwright script, 1440×900, owner, dev API :3000 + web :5173 (PIDs 11811/11813, stopped, ports free) | first load: 18 `files/downloadUrl`, 22 static placeholders; after scroll: 34 calls, 34 thumbnails loaded; fresh load then immediate click on a card: `requestfailed` = [] |
| Screenshots before/after scroll (1440) | before: 2 rows of real thumbnails plus a partial row; after: real art down to DB001, no skeleton or spinner |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | `designs.index.tsx:84-98`: `SignedImage` mounts only once `useInView` reports the card on screen; the placeholder is a plain `div.bg-muted.checkerboard` (22 counted), not a skeleton or spinner |
| 2 | Yes | 18 calls on first load (12 visible cards plus the 300px margin row), 34 after scrolling, real thumbnails |
| 3 | Yes (gate re-runs the e2e) | Immediate click produced 0 failed requests; no `e2e/**` or allow-list change. I did not re-run `market`/`screens.smoke` because the gate runs the E2E and the card does not change the golden path |
| 4 | Yes | 7 `SignedImage`/`useSignedUrl` sites (order-detail ×2, pickers, drafts.$draftId, designs.$designId, personalization index and $templateId) read only `data`/`isPending`/`isError`. `queryKey` matches `queryOptions` exactly (`@orpc/tanstack-query/dist/index.mjs:102-129`, no `experimental_defaults` in `src/lib/rpc.ts`), so the cache is shared. `bins.tsx:77` keeps `queryOptions` with an `attachment` key, a separate cache entry |
| 5 | Yes | No contract change, no new dependency |

## Judgement on dropping the abort signal
A real fix, not a mask. Both procedures are cheap, side-effect-free reads with stable keys. Without the signal, a request in flight when the user navigates finishes and fills the cache (14-minute `gcTime`), so going back costs nothing, and nothing is re-requested. There is no stale-response race: each response lands under its own `fileKey` key, and React Query ignores a response for an unmounted observer. The only context lost is oRPC's `OPERATION_CONTEXT_SYMBOL`, which a plain `RPCLink` does not read. The cost: after a click, up to about 12 queued presign calls keep their HTTP/1.1 connections busy for a few milliseconds before the detail page's own calls can use them. That is small, and lazy loading caps it (18, down from about 40). The watcher's real concern was wasted volume, and lazy loading fixes that. Most callers keep cancellation, because only these two queries opted out.

## Blocking findings
None.

## Checks
- [x] Only owned paths changed. `src/hooks/use-in-view.ts` is in `src/hooks/`, not the `src/lib/` or `src/components/` the card names. It still sits inside web-engineer's `invai-web/**` and matches the repo's convention (`use-debounced.ts`), so this is not blocking
- [x] Nothing outside scope (no virtualization library, bulk endpoint or e2e change)
- [x] No tests weakened (scan clean). No unit test covers `useInView`; see note
- [x] Tenancy, idempotency and money: not applicable (UI only). en/es: no new strings
- [x] Decisions: per card, in the report; nothing cross-cutting

## Optional notes (not blocking)
- Add a one-line note to the inline comments that other `useQuery` reads keep auto-abort, so nobody copies this pattern for heavy queries. Also consider a small `useInView` unit test.
- `personalization.index.tsx:221` has the same per-card fetch pattern (author already flagged it as a follow-up).
