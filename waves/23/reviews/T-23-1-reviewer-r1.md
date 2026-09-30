# Review of T-23-1 (round 1)

- Reviewer: reviewer on Opus 5.5 · Author: web-engineer on Opus 5.5 · Diff: invai-web `54b64d7..353a49d` (8 commits)
- Verdict: **changes-required**

## Evidence I re-ran
| Command | Result |
|---|---|
| `pnpm typecheck` / `pnpm lint` | 0 errors / exit 0, 1 pre-existing warning (`markdown.test.ts`) |
| `pnpm test --reporter=dot` | 19 files, 119 tests passed |
| `VITE_API_URL=http://localhost:3000 pnpm build` | built; largest chunk `vendor-*.js` 394.98 kB, `index-*.js` 305.10 kB, no >500 kB warning |
| `scan-test-weakening.sh invai-web 54b64d7` | no hits (assertions removed 0, added 6) |
| Flattened `en.ts`/`es.ts` at both commits (node strip-types script) | before: 1953 keys, 39 with es==en. After: 1926 keys, **417** with es==en. **374 keys had Spanish at 54b64d7 and show English now**; 91 keys dropped, **85 of them had Spanish** |
| Own API PORT=3139 (PID 76060/76075, stopped; dev DB not reset), packer@ | `maintenance.start`, `me.updateOrg`, `scanForms.create`, `resendEmail` → all 403 with the matching permission. office@ `me.updateOrg` → 403 `org.manage` (UI gates on `org.manage`, matches) |
| `files.presignUpload` kind `photo` as office@ | svg → 415 `UNSUPPORTED_TYPE`; 30 MB → 413 (`maxBytes` 26214400 = UI's "up to 25 MB"); png 1 kB → fileKey |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | yes | SCAN tab gated `shipping.manage` (= backend); `scanForms.list` returns the form; RATE_EXPIRED → `setExpired`+refetch in `shipping.tsx:452` |
| 2 | yes | `company.tsx:57` `editable = can("org.manage")`; refused as office/packer live |
| 3 | yes | `can("production.maintenance")` gates the panel (office+ per contract test); `realtime.ts` case added; packer 403 live |
| 4 | yes | `ResendEmailButton` with `RESEND_TOO_SOON.retryAfterSec` countdown, gated `vendors.manage` |
| 5 | yes | `uploadFile("photo")` presigned flow; preview is SVG `<image href=signedUrl>`, no inline markup; server limits proven above |
| 6 | yes | `localeNumber` es-US, `digestMoneyLang`, `canRetry` excludes FORBIDDEN; 390 px from author screenshots |
| 7 | yes | build output above (vite.config.ts accepted by tech lead) |
| 8 | **no** | Spanish screens now show English for 374+85 strings that were translated (finding 1) |
| 9 | yes (button part only, per ruling) | shows for any emailed sheet: delivery status isn't in the contract |
| 10 | yes | `format.ts` `dateLocale()` from `i18n.language`; unit test in `format.test.ts` |

## Blocking findings
1. `src/i18n/es.ts` (regenerated in 353a49d), e.g. `:1029` `nav.adSpend: "Ad spend"`, `:80` whole `adSpend` block. Before, it was `"Agregar gasto"` and so on. `es.ts` held hand-added Spanish that `scripts/i18n-es.json` never had. `gen-i18n.py` writes `es.get(k, flat[k])`, so regenerating replaced 374 translated values with English: billing 54, digest 78, bins 27, market 23, reprints 19, nav 7, alerts 6, and more. Scenario: a Spanish-app owner opens Facturación or the weekly digest and gets English labels that were Spanish yesterday. That also breaks AC8 ("no English fallbacks"). Also, 91 dynamic-lookup keys were dropped from en/es because they're missing from `i18n-extra-en.json` (`creditKind.*` in `billing.tsx:476`, `digest.costLine.*` in `digest-copy.ts:165`, `assistant.tool.*`, `billingStatus.*`, `alerts.kind.*`). 85 of them had Spanish, so they now fall back to the English code default. Fix: copy every Spanish value from `54b64d7:src/i18n/es.ts` into `scripts/i18n-es.json`, add the dynamic keys to `i18n-extra-en.json`, then re-run `pnpm i18n`. Proof: es==en count ≤ 39 plus the new intentionally identical keys, and 0 keys that had Spanish at 54b64d7 lost it.

## Checks
- [x] Only owned paths (`src/**`, plus `vite.config.ts`/`scripts/i18n-*.json` accepted by the tech lead)
- [x] Nothing outside scope (AC9 alert text moved to 23b)
- [x] No weakened tests (scan clean)
- [ ] en/es text: **fails**, finding 1. Tenancy/idempotency: backend guards match UI gates; no money math added
- [x] Decisions: none needed

## Optional notes (not blocking)
- `sheets.$sheetId.tsx` resend button: the contract's `VendorConnection.delivery` (`portal`/`email`) could hide it for portal vendors instead of relying on the 409 toast.
- `main.tsx` adds `RATE_EXPIRED` to the global silence list. Only `shipping.buy` handles it, and that call is already `silent`, so the entry is redundant and would hide a batch-buy expiry.
