# 0003: Marketplace stock push is opt-in per connection

- Status: accepted (2026-09-24)
- Type: product

## Context
Availability sync can overwrite a shop's live marketplace quantities.

## Decision
Availability sync pushes only to connections where the shop turned on `pushAvailability`. Onboarding prompts the shop to turn it on.

## Consequences
A missed update is less harmful than silently overwriting live listings on day one. Onboarding (`onboard-shop`) must include the prompt.
