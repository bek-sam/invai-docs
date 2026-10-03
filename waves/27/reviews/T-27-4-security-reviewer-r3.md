# Review of T-27-4 follow-up 6bf766e (round 3, mock http relaxation)

- Reviewer: security-reviewer on opus
- Author: integrations-engineer
- Verdict: approve

## Evidence I re-ran
| Command | Result |
|---|---|
| `git -C invai-backend show 6bf766e` | 3 files: `shopify/media.ts`, `mock.ts`, `media.test.ts` |
| `grep -rn "validateProductImages\|allowLocalHttp" src` (non-test) | only caller with the option: `mock.ts:235`; live path `media.ts:238` (`pushShopifyProductImages`, used by `live.ts:13`) calls `validateProductImages(input)` with no option |
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/modules/photos src/integrations/channels` | 17 files, 146 passed, exit 0 |

## Security view
| Check | Met? | Evidence |
|---|---|---|
| Relaxation only in the mock adapter | yes | opt-in `opts.allowLocalHttp`, default `{}`; only `shopifyMock` passes it |
| Only localhost / 127.0.0.1 | yes | exact `Set` match on `URL.hostname` + `protocol === "http:"`; `minio.example.com`, ftp:, file:, non-URL rejected (new tests); `localhost.evil.com` would not match |
| Live still https-only | yes | live test (`media.test.ts:470-489`, `shopifyLive`) still rejects `http` with `invalid_input` and no fetch |
| Filename/basename check kept for http | yes | same condition still requires `basename === filename` |

## Blocking findings
none. The mock never fetches the URL, so even the allowed hosts carry no SSRF path.

## Optional notes
- `[::1]` not allowed; fine (narrower than stated).
