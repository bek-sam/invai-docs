# T-8-6: NUL-safe text at the API input boundary (follow-up to T-8-2 r3, OI-5)
Owner: architect (contracts) + backend-foundation. Model: sonnet. Risk flags: security.

## Acceptance criteria
1. **Shared transform:** every string field in oRPC inputs is sanitized. Remove `\u0000` and other characters Postgres text and jsonb reject; leave all other Unicode unchanged. Do it once, through a shared schema helper in contracts, or an input middleware in the backend `orpc.ts`. Pick the smaller change that covers every procedure, and record why.
2. **Other text sources:** webhook and CSV ingestion paths (text that doesn't come through oRPC inputs) use the same helper where they write text.
3. **Tests:** a test sends NUL through a representative procedure (listing draft `brief`), a CSV import row and a webhook payload, and none of them crash.
4. The existing gateway and `ask()` sanitizers stay (defense in depth).
