// Screenshot web screens at the three audit viewports, signed in as one demo user.
// Run from invai-web (it resolves Playwright from there):
//   cd invai-web && node ../.claude/skills/ux-audit/shoot.mjs <outDir> [email] [lang] [route ...]
// Example:
//   node ../.claude/skills/ux-audit/shoot.mjs ../invai-docs/design/audits/2026-10-01-orders/shots owner@desertbloom.test es /orders "/orders?view=at_risk"
// Env: WEB_URL (default http://localhost:5173), PASSWORD (default demo1234!), THEME=dark for dark mode.
import { mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { join } from "node:path";

const require = createRequire(`${process.cwd()}/`);
const { chromium } = require("@playwright/test");

const [outDir, email = "owner@desertbloom.test", lang = "en", ...routes] = process.argv.slice(2);
if (!outDir) {
  console.error("usage: shoot.mjs <outDir> [email] [lang] [route ...]");
  process.exit(1);
}
const base = process.env.WEB_URL ?? "http://localhost:5173";
const password = process.env.PASSWORD ?? "demo1234!";
const theme = process.env.THEME === "dark" ? "dark" : "light";
const VIEWPORTS = [
  { name: "desktop-1440", width: 1440, height: 900 },
  { name: "tablet-1280x800", width: 1280, height: 800 },
  { name: "phone-390", width: 390, height: 844 },
];
mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch();
for (const vp of VIEWPORTS) {
  const ctx = await browser.newContext({
    viewport: { width: vp.width, height: vp.height },
    colorScheme: theme,
    locale: lang === "es" ? "es-US" : "en-US",
  });
  const page = await ctx.newPage();
  const problems = [];
  page.on("console", (m) => m.type() === "error" && problems.push(`console: ${m.text()}`));
  page.on("response", (r) => r.status() >= 500 && problems.push(`${r.status()} ${r.url()}`));
  await page.goto(`${base}/login`);
  await page.evaluate((l) => localStorage.setItem("invai.lang", l), lang);
  await page.locator('input[type="email"]').fill(email);
  await page.locator('input[type="password"]').fill(password);
  await page.locator('button[type="submit"]').click();
  await page.waitForURL((u) => !u.pathname.startsWith("/login"), { timeout: 30_000 });
  for (const route of routes.length ? routes : ["/"]) {
    await page.goto(`${base}${route}`);
    await page.waitForTimeout(1500); // SSE keeps the network busy; give the first load time
    const slug = route.replace(/[^a-z0-9]+/gi, "_").replace(/^_|_$/g, "") || "today";
    const file = join(outDir, `${slug}.${vp.name}.${lang}.${theme}.png`);
    await page.screenshot({ path: file, fullPage: true });
    console.log(file);
  }
  if (problems.length) console.log(`[${vp.name}] problems:\n  ${problems.join("\n  ")}`);
  await ctx.close();
}
await browser.close();
