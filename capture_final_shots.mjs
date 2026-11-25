/**
 * Captura 3 screenshots finais em WebGPU de http://localhost:4173/:
 * 1) Desktop 1280x720 (Sanctuary Hero com logo Vercel vgpu + controles liquid glass)
 * 2) Mobile 390x844 (apenas ▲ vgpu no topo + pills compactas + botao 3 pontos)
 * 3) Mobile 390x844 com menu de 3 pontos aberto (Exterior Sun, Andon Glow, Retro Daylight)
 */
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { chromium } = require(
  "C:/Users/Administrador/.gemini/config/plugins/arquiteto/skills/arquiteto/node_modules/playwright",
);

const OUT_DIR = "C:/Users/Administrador/.gemini/antigravity/scratch/sala-japonesa-blueprint/renders";
fs.mkdirSync(OUT_DIR, { recursive: true });
const URL = "http://localhost:4173/";

async function capture(page, cdp, filename) {
  await page.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  await new Promise((r) => setTimeout(r, 450));
  const { data } = await cdp.send("Page.captureScreenshot", { format: "png" });
  const out = path.join(OUT_DIR, filename);
  fs.writeFileSync(out, Buffer.from(data, "base64"));
  console.log(`[Shot OK] ${out}`);
}

async function main() {
  const browser = await chromium.launch({
    headless: false,
    channel: "chrome",
    args: [
      "--enable-unsafe-webgpu",
      "--enable-features=Vulkan,WebGPU",
      "--ignore-gpu-blocklist",
      "--window-position=-2000,0",
    ],
  });

  // 1. Desktop 1280x720
  const ctxDesk = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const pDesk = await ctxDesk.newPage();
  const cdpDesk = await ctxDesk.newCDPSession(pDesk);
  await pDesk.goto(URL, { waitUntil: "domcontentloaded" });
  await pDesk.waitForFunction(() => document.getElementById("status")?.classList.contains("hidden"), { timeout: 45000 });
  await new Promise((r) => setTimeout(r, 700));
  await capture(pDesk, cdpDesk, "webgpu_desktop_hero.png");
  await ctxDesk.close();

  // 2 & 3. Mobile 390x844 (fechado e com menu 3 pontos aberto)
  const ctxMob = await browser.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2 });
  const pMob = await ctxMob.newPage();
  const cdpMob = await ctxMob.newCDPSession(pMob);
  await pMob.goto(URL, { waitUntil: "domcontentloaded" });
  await pMob.waitForFunction(() => document.getElementById("status")?.classList.contains("hidden"), { timeout: 45000 });
  await new Promise((r) => setTimeout(r, 700));
  await capture(pMob, cdpMob, "webgpu_mobile_clean.png");

  await pMob.click("#more-menu-btn");
  await new Promise((r) => setTimeout(r, 500));
  await capture(pMob, cdpMob, "webgpu_mobile_menu.png");

  await ctxMob.close();
  await browser.close();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
