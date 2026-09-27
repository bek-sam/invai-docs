---
name: feedback-dev-csp-needs-build-preview
description: invai-web's plain `pnpm dev` CSP hard-codes the API origin to localhost:3000, so a real browser pass against your own API port needs `vite build` + `vite preview`, not `pnpm dev`
metadata:
  type: feedback
---

`invai-web/vite.config.ts` hard-codes `DEV_API_ORIGIN = "http://localhost:3000"` into the dev server's CSP `connect-src`, regardless of `VITE_API_URL`. Only `build`/`preview` derive `connect-src` from `VITE_API_URL` (`connectSrc(requireApiOrigin(...))`). If you run your own API on a card-specific port (`PORT=31xx`) and start web with plain `pnpm dev --port 5183`, every request to your API is blocked by CSP with a browser console error, and login silently fails (URL never leaves `/login`).

**Why:** `vite.config.ts` is explicitly off-limits ("Things that bite" in the web-engineer role file) — don't try to parameterize the dev CSP to fix this.

**How to apply:** for a real "exercise it in the browser" pass against your own ports, use `VITE_API_URL=http://localhost:31xx pnpm build && VITE_API_URL=http://localhost:31xx node_modules/.bin/vite preview --port 5183 --strictPort` instead of `pnpm dev`. Also set `WEB_ORIGIN=http://localhost:5183` (or whatever port you pick) when starting your API — Hono's `cors()` only allows `env.WEB_ORIGIN`/`env.FLOOR_ORIGIN`, default `5173`/`5174`, so a different web port gets CORS-blocked too. See [[project-t17-4-assistant-starters]].
