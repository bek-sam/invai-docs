# 0001: Keep 8 separate repos

- Status: accepted (2026-09-23)
- Type: architecture

## Context
The concept planned a monorepo. The repos, CI and deploy keys already existed as separate GitHub repos (`bek-sam/invai-*`).

## Decision
Keep 8 repos side by side: contracts, ui, backend, imaging, web, floor, infra and docs. The shared packages (`@invai/contracts`, `@invai/ui`) are linked with `link:../<repo>`.

## Consequences
- A contract change must be fixed in every consumer on the same day. The order is contracts → backend → web/floor.
- Each repo runs its own checks, so a cross-repo change has to be verified in each repo it touches.
- Revisit this only if cross-repo changes become the main cost of each wave.
