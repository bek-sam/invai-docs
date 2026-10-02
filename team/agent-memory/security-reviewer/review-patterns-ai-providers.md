---
name: review-patterns-ai-providers
description: Defect patterns and proof techniques for reviewing AI provider code (SDK env-var key fallback, body-level PII assertions, guard-bash limits)
metadata:
  type: project
---

- 2026-10-01 T-P8-ai-openai: Both the `openai` and `@anthropic-ai/sdk` clients fall back to `process.env.<PROVIDER>_API_KEY` when `apiKey` is `undefined`, and `env.ts` loads `.env` into `process.env` for every non-production run. "Keys ignored under test" in `env.ts` therefore protects only the gateway path; a provider called directly under `NODE_ENV=test` still gets the real key. Filed as S-49 (Low, ai-engineer). Proof that needs no network: run `tsx -e` with `NODE_ENV=test`, a fake key and `OPENAI_BASE_URL=http://127.0.0.1:9/v1`; `APIConnectionError` means a key was found, `Missing credentials` means it was not.
- 2026-10-01: For AI cards, the strongest PII evidence is a test that stubs `fetch` on the real SDK client and asserts on the serialized HTTP body (no email/phone/street, injection string inside the `<data>` block, `store:false`). Accept `vi.spyOn(provider, ...)` only when it swaps the singleton's HTTP client, not the logic.
- 2026-10-01: `.claude/hooks/guard-bash.py` blocks long compound commands ("runs too many scripts") and `node -p "require(...)"`; split review commands into short separate Bash calls and read package metadata with grep on `package.json`. zsh also chokes on bare `====` echo separators: quote them.

**Why:** these three cost the most time in the P8 security co-review and will recur on every AI or dependency card.
**How to apply:** on any card touching `src/ai/providers/**` or adding an SDK, run the key-fallback proof and read the body assertions before anything else.
