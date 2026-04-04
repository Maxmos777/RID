#!/usr/bin/env node
/**
 * Post-build script:
 * copies Vite dist output into Django's staticfiles.
 *
 * Source:      dist/
 * Destination:
 *   assets → /home/RID/backend/static/apps/rockitdown/assets/
 *   (index.html is served by Django template, NOT as a static file)
 */
import { cpSync, mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const distDir = resolve(__dirname, "../dist");
const backendStatic = resolve(
  __dirname,
  "../../../../backend/static/apps/rockitdown"
);

if (!existsSync(distDir)) {
  console.error("dist/ not found — run vite build first");
  process.exit(1);
}

mkdirSync(backendStatic, { recursive: true });

// Copy the assets folder (JS, CSS, images) into Django staticfiles
cpSync(resolve(distDir, "assets"), resolve(backendStatic, "assets"), {
  recursive: true
});

console.log(`Copied assets → ${backendStatic}/assets`);

