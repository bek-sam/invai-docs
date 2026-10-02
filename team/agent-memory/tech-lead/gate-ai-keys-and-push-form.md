---
name: gate-ai-keys-and-push-form
description: P8 (2026-10-02) - blank real AI keys for gates; the only allowed push forms after T-23-6
metadata:
  type: project
---

Since 2026-10-02 the owner keeps a real `OPENAI_API_KEY` in `invai-backend/.env`. Run gates as `OPENAI_API_KEY= ANTHROPIC_API_KEY= caffeinate -i pnpm gate <repos>`.
**Why:** the gate and E2E would call a paid live model. Node's `loadEnvFile` keeps an already-set empty var, and `env.ts` treats blank as unset.
**How to apply:** use this for every gate. Push only with the bare `git -C /Users/bekbolsun/invai/<repo> push origin main|<sha>:main`; docs use the same form, without a stamp. Each security-reviewer agent picks the next free S-id: two reviews both used S-49 in P8 (B-271).
