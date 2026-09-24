# 0007: AI model policy

- Status: accepted (2026-09-23)
- Type: architecture

## Decision
- **Default model:** `claude-opus-5` with adaptive thinking.
- **Effort per route:** `low` for tags, SKU suggestions and personalization checks; `medium` for listing copy; `high` for the assistant.
- **Cheaper models:** Haiku or Sonnet only for bulk routes, and only after an eval shows equal quality (`model-upgrade`).
- **Refusals:** server-side refusal fallback is on, and `stop_reason` is always checked.
- **Config:** model IDs live in one config file.
- **No key:** a deterministic, schema-valid mock provider.
- **PII:** none goes to the AI provider.

## Consequences
The `ai-engineer` owns this policy. Any model or prompt change ships with an eval diff (`ai-feature-with-evals`, `model-upgrade`).
