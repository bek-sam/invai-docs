# Review of T-27-4 (round 1)

- Reviewer: security-reviewer on opus
- Author: integrations-engineer on opus
- Verdict: changes-required

## Evidence I re-ran
| Command | Result |
|---|---|
| `OPENAI_API_KEY= ANTHROPIC_API_KEY= pnpm vitest run --reporter=dot src/integrations/channels` | 12 files, 81 passed, 1 expected fail (my S-52 proof) |
| S-52 proof with `it.fails` → `it` (temp copy, deleted) | fails: `expected 2 to be 1` (productUpdate sent twice) |
| `scan-test-weakening.sh invai-backend 3f4deae~1` | only hits in src/ai (other card) and my own `it.fails` marker |

## Acceptance criteria
| # | Met? | Evidence |
|---|---|---|
| 1 | Yes | optional `pushProductImages?` in types.ts; Shopify live+mock only; `write_products` in toml and `SHOPIFY_SCOPES` (re-consent = owner step) |
| 2 | Yes | mock store keyed `conn.id:productId:filename`; repeat skipped; short id → product_not_found |
| 3 | Partly | variables-only GraphQL (`$product`, `$media`), userErrors typed, read-back dedupe; but the client's 5xx retry re-sends the mutation without read-back (S-52) |
| 4 | Yes | recorded grant lacking scope → reconnect_needed with no call; 401/403/ACCESS_DENIED → reconnect_needed |
| 5 | Yes | channel suite green; other adapters unchanged |

## Blocking findings
1. `shopify/client.ts:136` (5xx branch) with `shopify/media.ts` `push` → S-52 Medium (integrity). Shopify applies `productUpdate` media, a gateway answers 502/504, `shopifyGraphql` retries the non-idempotent mutation (no `@idempotent`), and the shop's live product shows each photo twice. Fix: a `GraphqlOptions` opt-out of 5xx retry for this mutation so it surfaces as `UPSTREAM_FAILED` and the caller's retry runs the read-back; flip `src/integrations/channels/shopify/security.test.ts` to `it`. Logged in `security/v1-review.md`, due 2026-11-02.

## Checks
- [x] Only owned paths changed (channels/** + shopify.app.toml)
- [x] Nothing outside scope
- [x] Tests stub `fetch`, inspect bodies; no real call; none weakened
- [ ] Idempotency: S-52 above. Tenancy: n/a (token from `conn`, mock keyed by connection)
- [x] Decisions recorded where needed (scope change named in report)

## What leaves InvAI / logs (verified)
- Outbound: https presigned URL (`originalSource`), alt + 8-hex filename marker, `mediaContentType`; token only in `x-shopify-access-token`; `redirect: "error"`, 30 s timeout.
- Logs carry connectionId, idempotencyKey, counts, userError field paths: no URLs, alt, tokens or buyer data.
- Adapter creates no URLs; presigned expiry vs Shopify's async download is T-27-3's call.

## Optional notes (not blocking)
- `rejected` message embeds Shopify userError text, which may echo the presigned URL back to the shop's own caller; fine for the shop, keep it out of logs and analytics in T-27-3.
- T-27-3 must pass only presigned URLs for `isCompanyKey()`-checked keys of the same company.
