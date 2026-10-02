# Review of T-26-5 (round 2)

- Reviewer: reviewer on Opus 5.5
- Author: web-engineer on Sonnet 5
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `invai-web: pnpm typecheck && pnpm lint && pnpm vitest run --reporter=dot` | exit 0; 163 passed |
| `scan-test-weakening.sh invai-web c471c95~1` | no hits |
| `git show --stat c471c95` | 5 owned files (route, labels.ts, en/es, i18n-es.json); clean tree |
| backend `photos/service.ts:264-317, 846-888`, `lib/s3.ts:103` read | jobId = `randomUUID()` per enqueue; zip reuse by approved-id fingerprint; getSet presign = 3600 s |
| i18n: 4 new `photos.*` keys + `errors.generic` grep | present in en.ts, es.ts and i18n-es.json |
| Screenshots `/tmp/t265r2/02`, `03` | es retry state shown; zip-failed retry button and "Tee · White" translated labels |

## Round-1 findings
| # | Fixed? | Evidence |
|---|---|---|
| 1 poll loop | yes | `:276-294` a new `jobId` while `pending` sets `stalled` and stops the 2 s interval. The jobId is a random UUID, so a re-enqueue is always detected. Retry: `onSuccess` sets `lastJobId` to the new id, clears `stalled` and invalidates, so the next `pending` matches and polling resumes. `key={designId}` resets the state when the design changes |
| 2 zip | yes | Keyed on the sorted approved ids (`:684-695`); while the key differs, Download is hidden (`zipMatchesApproved`). `failed`/`isError` shows a retry button. Remount re-export is a no-op (backend fingerprint reuse) |
| 3 URL storms | yes | `PickDesignCard` uses `useInView` (sticky). `useStableImageUrls` keeps each image URL by id+key for 13 min; signed URLs last 60 min, so a refetch renews them about 47 min before expiry. The hook runs before the early returns |
| 4 raw text / layout | yes | NOT_FOUND and reasonless BAD_REQUEST map to translated text; failed image and failed analysis use fixed keys; `garmentLabel`; one column at base; Attach button wraps |

## Checks
- [x] Only owned paths changed; nothing outside scope
- [x] No tests weakened (no test changes in c471c95)
- [x] en and es complete for new strings; tenancy n/a (web only)

## Optional notes (not blocking)
- `listing-photos.tsx:675-680` wraps every `getSet` error as `PHOTO_SET_ERROR`, so FORBIDDEN loses its title and gains a retry button (B-193 behavior), and NETWORK loses its icon. Only map the message for NOT_FOUND/BAD_REQUEST.
- Shot 02: the compact ErrorState truncates to "Algo salió mal: N…" at 390 px, so the sentence can't be read. Use the full ErrorState there.
- `useStableImageUrls` comment says "~15 minutes"; getSet signs for 60 min (harmless).
- After `exportZip` succeeds, the stale ready zip can show for one refetch round-trip before `queued` arrives.
- Backend re-enqueue-on-failed semantics are still open (author: wave 27); the tech lead should track it.
